from handlers.create_user import create_user
#from handlers.users import users
from handlers.verify import verify

urls = {
    'create-user': create_user,
#    'users': users,
    'verify': verify,
}
