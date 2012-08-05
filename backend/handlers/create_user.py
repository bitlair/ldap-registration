import ldap
import ldap.modlist as modlist
from Crypto.Hash import SHA, MD4
import os
import re
from config import Config
import smtplib
from email.mime.text import MIMEText
from ldap.dn import escape_dn_chars as escape_dn

def create_ssha_password(password):
    salt = os.urandom(4)
    h = SHA.new(password)
    h.update(salt)
    return (h.digest() + salt).encode('base64').strip()

def create_nt_password(password):
    h = MD4.new(password.encode('utf-16-le'))
    return h.hexdigest().upper()

# Function to assign a user ID for a user to add to the target database
def assign_uid(conn):
    try:
        res = conn.search_s('cn=NextFreeUnixId,%s' % Config.ldap_base_dn, ldap.SCOPE_BASE, '(objectclass=sambaUnixIdPool)', [ 'uidNumber' ])
        uidNumber = 1000
        for dn,attr in res:
            uidNumber = attr['uidNumber'][0]

        res = conn.modify_s('cn=NextFreeUnixId,%s' % Config.ldap_base_dn, [ (ldap.MOD_REPLACE, 'uidNumber', str(int(uidNumber) + 1) ) ])
        return uidNumber

    except ldap.LDAPError, e:
        print "LDAP Error in assign_uid(): " + repr(e.message['desc'])
        raise

# Function to assign a user ID for a user to add to the target database
def assign_sambasid(conn):
    try:
        res = conn.search_s('sambaDomainName=%s,%s' % (Config.samba_domain, Config.ldap_base_dn), ldap.SCOPE_BASE, '(objectclass=sambaDomain)', [ 'sambaSID', 'SambaNextRid' ])
        rid = 1000
        sambaSID = ""
        for dn,attr in res:
            sambaSID = attr['sambaSID'][0]
            rid = attr['sambaNextRid'][0]

        res = conn.modify_s('sambaDomainName=%s,%s' % (Config.samba_domain, Config.ldap_base_dn), [ (ldap.MOD_REPLACE, 'sambaNextRid', str(int(rid) + 1) ) ])
        return "%s-%s" % (sambaSID, rid)

    except ldap.LDAPError, e:
        print "LDAP Error in assign_uid(): " + repr(e.message['desc'])
        raise



def create_user(request):
    # Connect to LDAP
    try:
        conn = ldap.initialize(Config.ldap_uri)
        conn.bind_s(Config.ldap_bind_dn, Config.ldap_bind_password)
    except Exception as e:
        return request.response_json({'success': False, 
                                      'msg': "Can't bind to LDAP: %s" % e.message['desc']})


    # Validate inputs
    try:
        errors = []
        if request.post['answer'][0] != '42':
            errors.append( {'id': 'answer', 'msg': 'Sorry, wrong answer' } )
        if not re.match(r'^[a-z0-9\-\{\}\.]+$', request.post['username'][0]):
            errors.append( {'id': 'username', 'msg': 'Username should match r\'^a-z0-9\-\{\}\.]+$\'' } )
        if not re.match(r'^[a-z0-9\-\_\.]+\@[a-z0-9\-]+\.[a-z]{2,30}$', request.post['email'][0]):
            errors.append( {'id': 'email', 'msg': 'E-mail address incorrect.' } )
        if request.post['first'][0] == "":
            errors.append( {'id': 'first', 'msg': 'First name cannot be empty' } )
        if request.post['last'][0] == "":
            errors.append( {'id': 'last', 'msg': 'Last name cannot be empty' } )
        if len(request.post['password'][0]) < 5:
            errors.append( {'id': 'password', 'msg': 'Password too short' } )

        if len(errors) > 0:
            return request.response_json({'success': False, 'errors': errors })
    except:
            return request.response_json({'success': False, 'msg': 'Missing POST variables or internal server error'}, status="500 Internal Server Error")

    attrs = {
        'objectClass': [ 'top', 'person', 'organizationalPerson', 'inetOrgPerson', 'posixAccount', 'sambaSamAccount', 'qmailUser' ],
        'cn': "%s %s" % (request.post['first'][0], request.post['last'][0]),
        'displayName': "%s %s" % (request.post['first'][0], request.post['last'][0]),
        'description': "%s %s" % (request.post['first'][0], request.post['last'][0]),
        'gecos': "%s %s,,," % (request.post['first'][0], request.post['last'][0]),
        'givenName': request.post['first'][0],
        'sn': request.post['last'][0],
        'accountStatus': '1', # Unverified account
        'mail': request.post['email'][0],
        'uid': request.post['username'][0].lower(),
        'userPassword': "{SSHA}%s" % create_ssha_password(request.post['password'][0]),
        'sambaNTPassword': create_nt_password(request.post['password'][0]),
        'uidNumber': str(assign_uid(conn)),
        'gidNumber': '1000',
        'sambaSID': assign_sambasid(conn),
        'homeDirectory': "/home/%s" % request.post['username'][0].lower(),
        'loginShell': '/bin/bash',
        'sambaAcctFlags': '[U          ]',
    }

    #
    # Add the object to the directory
    #
    # FIXME: ou should be configurable
    ldif = modlist.addModlist(attrs)
    try:
        conn.add_s("uid=%s,ou=accounts,%s" % (escape_dn(request.post['username'][0].lower()), Config.ldap_base_dn), ldif)
    except Exception as e:
        return request.response_json({'success': False,
                                      'errors': [{'id': 'username', 'msg': e.message['desc'] }]})

    #
    # Grab the entryUUID for the newly created object, this is the unique identifier for account email verification
    #
    res = conn.search_s("uid=%s,ou=accounts,%s" % (escape_dn(request.post['username'][0].lower()), Config.ldap_base_dn), ldap.SCOPE_BASE, attrlist=[ 'entryUUID' ])

    if len(res) != 1:
        return request.response_json({'success': False, 
                                  'msg': 'Could not find newly created user in the directory' })

    attrs['entryUUID'] = res[0][1]['entryUUID'][0]


    # FIXME Text should be configurable
    msg = MIMEText("Hello %(givenName)s,\n\nYou've created an account for %(site_name)s, but you still need to activate it. You can activate it by going to http://services.ifcat.org/registration/verify.html?uuid=%(entryUUID)s&username=%(uid)s\n\nOr enter the form fields manually:\nUUID: %(entryUUID)s\nUsername: %(uid)s\n\nRegards,\n\nThe %(site_name)s team" % dict(attrs.items() + {'site_name': Config.site_name }.items()))
    msg['Subject'] = 'Activate your account'
    msg['From'] = "\"%(site_name)s\" <%(site_mail)s>" % dict(attrs.items() + {'site_name': Config.site_name, 'site_mail': Config.site_mail }.items())
    msg['To'] = attrs['mail']

    s = smtplib.SMTP('localhost')
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()

    return request.response_json({'success': True, 
                                  'msg': 'A verification email has been sent to you' })
