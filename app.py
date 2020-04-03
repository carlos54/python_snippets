from flask import Flask
from flask_wkhtmltopdf import Wkhtmltopdf
import os

app = Flask(__name__)
app.config['WKHTMLTOPDF_BIN_PATH'] = r'/usr/bin/wkhtmltopdf'
app.config['PDF_DIR_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'pdf')


wkhtmltopdf = Wkhtmltopdf(app)

@app.route("/")
@app.route("/home")
def home():
    return "<h1>Home Page</h1>"


@app.route("/dopdf")
def dopdf():
    #regarde celery.task() decorateur  WKHTMLTOPDF_USE_CELERY
    return wkhtmltopdf.render_template_to_pdf(template_name_or_list='test.html', download=False, save=False, wkhtmltopdf_args=None, param1='hello')


if __name__ == '__main__':
    app.run(debug=True)
