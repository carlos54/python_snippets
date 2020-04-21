from flask import Flask
import logging
import os
from redis import Redis
from rq import Queue


def create_app(ConfigCls):
   
    app = Flask(__name__)
    app.config.from_object(ConfigCls)
     
    rq = Queue("mail", is_async=app.config.get('RQ_IS_ASYNC'),
               connection=Redis.from_url('redis://'), 
               default_timeout=60*10)#10 mins
    app.config.update({'mail_rq': rq})
    rq = Queue("email", is_async=app.config.get('RQ_IS_ASYNC'),
               connection=Redis.from_url('redis://'), 
               default_timeout=60*10)#10 mins
    app.config.update({'email_rq': rq})
   
    
    ### log init
    logfile_path = os.path.join(app.config['LOG_DIR'], app.config['LOG_FILE'])
    logging.basicConfig(filename=logfile_path,
                    format='%(asctime)s %(message)s',
                    level=logging.INFO, filemode=app.config['LOG_MODE'])


    # api v1 
    from mailing.resources.mail.routes import bp as resource_mail
    from mailing.resources.email.routes import bp as resource_email
    from mailing.resources.template.routes import bp as resource_template
    app.register_blueprint(resource_mail, url_prefix='/v1')
    app.register_blueprint(resource_email, url_prefix='/v1')
    app.register_blueprint(resource_template, url_prefix='/v1')

    return app


