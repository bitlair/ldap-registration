import ldap
from Crypto.Hash import SHA, MD4
import os
import re
from config import Config
import smtplib
from ldap.dn import escape_dn_chars as escape_dn
from ldap.filter import escape_filter_chars as escape_filter


def verify(request):
    # Connect to LDAP
    try:
        conn = ldap.initialize(Config.ldap_uri)
        conn.bind_s(Config.ldap_bind_dn, Config.ldap_bind_password)
    except Exception as e:
        return request.response_json({'success': False, 
                                      'msg': "Can't bind to LDAP: %s" % e.message['desc']})


    #
    # Grab the entryUUID for the newly created object, this is the unique identifier for account email verification
    #
    res = conn.search_s(Config.ldap_base_dn, ldap.SCOPE_SUBTREE, 
            '(&(entryUUID=%s)(uid=%s))' % (escape_filter(request.post['entryUUID'][0]), escape_filter(request.post['username'][0])))

    if len(res) != 1:
        return request.response_json({'success': False, 
                                      'errors': { 'entryUUID': 'Cannot find this UUID with this username'}})

    dn = res[0][0]

    ldif = [( ldap.MOD_REPLACE, 'accountStatus',  '2' )]
    try:
        conn.modify_s(dn, ldif)
    except Exception as e:
        return request.response_json({'success': False, 
                                      'msg': "Can't modify account: %s" % e.message['desc']})

    return request.response_json({'success': True, 
                                  'msg': 'Your account is activated' })
