from flask import Flask, make_response
from flask_wkhtmltopdf import Wkhtmltopdf #https://github.com/chris-griffin/flask-wkhtmltopdf, https://wkhtmltopdf.org/usage/wkhtmltopdf.txt, 
import os
import secrets
import logging
import json
import shutil
from typing import Dict
from api.barcode import insert_barcode_in_pdf

app = Flask(__name__)

PWD = os.path.dirname(__file__)
TMP_DIR = os.path.join(PWD, 'temps/')
LOG_DIR = os.path.join(PWD, 'logs/')

app.config['WKHTMLTOPDF_BIN_PATH'] = r'/usr/bin/wkhtmltopdf'
app.config['PDF_DIR_PATH'] = TMP_DIR
app.config['TEMP_DIR_PATH'] = TMP_DIR

wkhtmltopdf = Wkhtmltopdf(app)

logfile_path = ''.join([LOG_DIR, "main.log"])
logging.basicConfig(filename=logfile_path,
                    format='%(asctime)s %(message)s', level=logging.DEBUG, filemode='w')
logging.info('start up')


@app.route("/")
@app.route("/home")
def home():
    return "<h1>Home Page</h1>", 200

# no route decorators => private flask methode, no acces trought URL route


def generate_doc(template_name: str, **kwargs) -> str:
    """
    private function, generate the pdf doc for one instance and return its path
    """
    wkhtmltopdf_opt = ["--orientation Landscape", "--page-size A5"]

 
    r = wkhtmltopdf.render_template_to_pdf(
        template_name_or_list=template_name,
        download=True,
        save=True,
        wkhtmltopdf_args=wkhtmltopdf_opt,
        **kwargs)
    assert r.status_code == 200, "problem generating render pdf doc "  # AssertionError

    if not 'Content-Disposition' in r.headers:
        raise ValueError("http header empty")

    header_file_info = r.headers['Content-Disposition']

    _, file_full_name = os.path.split(header_file_info)
    # remove "double extension, issue
    # https://github.com/chris-griffin/flask-wkhtmltopdf/issues/10
    file_name = file_full_name.replace(".pdf", "")
    file_path = os.path.join(app.config['PDF_DIR_PATH'], file_name + ".pdf")

    return file_path


@app.route("/apply_pdf_template")
def apply_pdf_template():

    ###### inner function
    def process_respondent(data: Dict[str, object]):
        logging.debug("(%s) - data current instance : %s", job_id,
                      json.dumps(data))

        temp_file_path = generate_doc(template_name='test.html',
                                      **data)
        if not os.path.isfile(temp_file_path):
            raise BaseException("error during respondent pdf generation")

        insert_barcode_in_pdf(pdf_file_path=temp_file_path,
                              tmp_dir=job_work_dir)
        
        shutil.move(temp_file_path, job_work_dir)
         
        logging.info("(%s) - generate doc ok : %s",
                     job_id, os.path.basename(temp_file_path))

        
    ######

    job_id = secrets.token_hex(8)
    job_work_dir = os.path.join(app.config.get('TEMP_DIR_PATH'), job_id)
    if not os.path.exists(job_work_dir):
        os.makedirs(job_work_dir)

    if not os.path.exists(job_work_dir):
        abort(500, "OSError, permission mkdir job_work_dir failed")

    logging.info("new process %s : %s", job_id, job_work_dir)
    respondent_data = {'param1': "11:11"}

    process_respondent(respondent_data)

    return make_response()

    # regarde celery.task() decorateur  WKHTMLTOPDF_USE_CELERY


if __name__ == '__main__':
    app.run(debug=True, port=8001)
