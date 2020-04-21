import os
from typing import NewType, Type

## SMTP server
#app.config['MAIL_SERVER'] : default ‘localhost’
#app.config['MAIL_PORT'] : default 25
#app.config['MAIL_USE_TLS'] : default False
#app.config['MAIL_USE_SSL'] : default False
#app.config['MAIL_DEBUG'] : default app.debug
#app.config['MAIL_USERNAME'] : default None
#app.config['MAIL_PASSWORD'] : default None
#app.config['MAIL_DEFAULT_SENDER'] : "test@api.statec.lu"
#app.config['MAIL_MAX_EMAILS'] : default None
#app.config['MAIL_SUPPRESS_SEND'] : default app.testing
#app.config['MAIL_ASCII_ATTACHMENTS'] : default False


pwd = os.path.dirname(__file__)
class ConfigDefault:
    TEMPLATE_DIR = os.path.join(pwd, 'templates/')
    TMP_DIR = os.path.join(pwd, 'temps/')
    LOG_DIR = os.path.join(pwd, 'logs/')
    LOG_MODE = "w" # https://docs.python.org/3/library/functions.html#filemodes
    LOG_FILE = "default.log"
    LANG_ALLOWED = "fr;de;lu;en;pt"
    RQ_IS_ASYNC = True

class Prod(ConfigDefault):
    LOG_MODE = "a"
    LOG_FILE = "prod.log"
    pass

class Test(ConfigDefault):
    LOG_MODE = "w"
    LOG_FILE = "test.log"
    pass

class Dev(ConfigDefault):
    LOG_MODE = "w"
    LOG_FILE = "dev.log"
    pass

class UnitTest(ConfigDefault):
    LOG_MODE = "w"
    LOG_FILE = "unittest.log"
    TESTING = True
    RQ_IS_ASYNC = False
    pass


NewType('T', ConfigDefault)
def get_config(key_env:str) -> Type[ConfigDefault] :
    conf = {
    'production':Prod,
    'testing':Test,
    'development':Dev
    }
    return conf.get(key_env.casefold(), Dev)