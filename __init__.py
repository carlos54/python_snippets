from flask import Flask
import logging
import os


def create_app(ConfigCls):
    
    app = Flask(__name__)
    app.config.from_object(ConfigCls)
    
    ### log init
    logfile_path = os.path.join(app.config['LOG_DIR'], app.config['LOG_FILE'])
    logging.basicConfig(filename=logfile_path,
                    format='%(asctime)s %(message)s',
                    level=logging.INFO, filemode=app.config['LOG_MODE'])


    #v1 resources
    from mailing.resources.mail.routes import bp as resource_mail
    from mailing.resources.email.routes import bp as resource_email
    from mailing.resources.template.routes import bp as resource_template
    app.register_blueprint(resource_mail, url_prefix='/v1')
    app.register_blueprint(resource_email, url_prefix='/v1')
    app.register_blueprint(resource_template, url_prefix='/v1')

    return app


