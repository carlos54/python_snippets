from mailing import create_app
from mailing.config import Prod, Test, Dev


app = create_app(Prod)

if __name__ == '__main__':
    #https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.run
    #run(host=None, port=None, debug=None, load_dotenv=True, **options)
    app.run(debug=True)
    
# run the api : python -m mailing.run (pwd from outsite package)