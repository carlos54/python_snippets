from mailing import create_app
from mailing.config import get_config
import os

os_conf = os.getenv('FLASK_ENV', "production")
print(f"***** FLASK_ENV :{os_conf}")
ENV = get_config(os_conf)
app = create_app(ENV)

if __name__ == '__main__':
    #https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.run
    #run(host=None, port=None, debug=None, load_dotenv=True, **options)
    app.run(host='0.0.0.0', debug=True)
   
# run the api : python -m mailing.run (pwd from outsite package)