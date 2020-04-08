from flask import Flask, render_template, make_response
from flask_mail import Message
import tempfile
import os
import secrets
import logging
import json
import shutil
import subprocess
from typing import Dict
##########################
from api.barcode import insert_barcode_in_pdf
from api.utils import merge_pdf




app = Flask(__name__)

PWD = os.path.dirname(__file__)
TMP_DIR = os.path.join(PWD, 'temps/')
LOG_DIR = os.path.join(PWD, 'logs/')

app.config['PDF_DIR_PATH'] = TMP_DIR
app.config['TEMP_DIR_PATH'] = TMP_DIR



logfile_path = ''.join([LOG_DIR, "main.log"])
logging.basicConfig(filename=logfile_path,
                    format='%(asctime)s %(message)s', level=logging.DEBUG, filemode='w')
logging.info('start up')


@app.route("/")
@app.route("/home")
def home():
    return "<h1>Home Page</h1>", 200


@app.route("/apply_pdf_template")
def apply_pdf_template():

    ###### inner function
    def process_respondent(data: Dict[str, object]):
        logging.debug("(%s) - data current instance : %s", job_id,
                      json.dumps(data))
        doc_instance_html = render_template('test.html',  **data).encode('utf-8')
        
        file_path = os.path.join(job_work_dir, secrets.token_hex(8))
        logging.info(f"({job_id}) - current instance files {file_path}")
        with open(file_path+".html","wb") as fp:
           fp.write(doc_instance_html)

        #https://wkhtmltopdf.org/usage/wkhtmltopdf.txt, 
        p_res  = subprocess.run(args=["wkhtmltopdf",
              "--dpi", "72",
              "--margin-top", "0",
              "--margin-left", "0",
              "--margin-right", "0",
              "--margin-bottom", "0",
              f"{file_path}.html",
              f"{file_path}.pdf"], capture_output= True, text=True)
        logging.debug(f"({job_id}) - stdout wkhtmltopdf {p_res}")
        
        insert_barcode_in_pdf(pdf_file_path=f"{file_path}.pdf",
                              tmp_dir=job_work_dir)

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
    respondent_data = {'param1': "12:12"}
    process_respondent(respondent_data)

    merge_file = merge_pdf(job_work_dir)
    logging.info(f"({job_id}) - merging file ready to print : {merge_file}")
        
    return make_response()

    # regarde celery.task() decorateur  WKHTMLTOPDF_USE_CELERY


if __name__ == '__main__':
    app.run(debug=True, port=8001)
