from flask import Flask, render_template, make_response, abort, request, json
from flask_mail import Message
import tempfile
import os
import secrets
import logging
import shutil
import subprocess

from typing import Dict, List
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
    return "<h1>Help doc</h1>", 200


@app.route("/template/<template_id>/<lang>", methods=["GET"])
def show_template(template_id, lang):
    """ return base template  """
    return render_template(f'{template_id}_{lang}.html')



@app.route("/template/<template_id>/<lang>", methods=["POST"])
def transfer_template(template_id, lang):
    """ transfer the new template to make it avalaible"""
    pass


@app.route("/template/<template_id>/<lang>", methods=["DELETE"])
def delete_template(template_id, lang):
    """ delete exiting template """
    pass


@app.route("/template/<template_id>/<lang>", methods=["PUT"])
def replace_template(template_id, lang):
    """ replace exiting template """
    pass

# "print" is this api is consider as ressource
@app.route("/print/<print_id>", methods=["GET"])
def info_print(print_id):
    """ return print log """
    pass


@app.route("/print", methods=["POST"])
def new_print():
    """ merge template and the respondents file 
    => return pdf file content type
    """
    
    job_id = secrets.token_hex(8)
    logging.info("******** /print  - id : %s", job_id)
        
    ## check posted data to process
    template_id = request.form.get('template_id') 
    if not template_id :
            abort(403, "Missing data payload - template_id : str")
    logging.info(f"({job_id}) - template:{template_id}")
   
    json_file = request.files.get("respondents")
    if not json_file :
          abort(403, """Missing data payload 
              - respondents : application/json file""")
    try:
        respondents = json.loads(json_file.read())
    except:
        abort(403, "respondents json application/json file corrupt") 
    logging.info(f"({job_id}) - respondents file :{type(json_file)} / {len(respondents)}")

    
 
    ## create working job directory
    job_work_dir = os.path.join(app.config.get('TEMP_DIR_PATH'), job_id)
    if not os.path.exists(job_work_dir):
        os.makedirs(job_work_dir)

    if not os.path.exists(job_work_dir):
        abort(500, "OSError, permission mkdir job_work_dir failed")
    
    
    ## save json data file received

    for respondent in respondents:
        print(respondent.get("id"))

                 
    data_file = os.path.join(job_work_dir,"data.json")
    json_file.save(os.path.join(job_work_dir,data_file))  
       
    
 
 

 

   

    

    
  #  respondent_data = {'param1': "11:11"}
   # process_respondent(respondent_data)
 #   respondent_data = {'param1': "12:12"}
 #   process_respondent(respondent_data)

 #   merge_file = merge_pdf(job_work_dir)
  #  logging.info(
  #      f"({job_id}) - merging file ready to print : {merge_file}")

    return make_response(job_id)

    """

    # inner function
    def process_respondent(data: Dict[str, object]):
        logging.debug("(%s) - vars current instance : %s", job_id,
                        json.dumps(data))
        doc_instance_html = render_template(f'{template_id}.html',
                                            **data).encode('utf-8')

        file_path = os.path.join(job_work_dir, secrets.token_hex(8))
        logging.info(f"({job_id}) - current instance files {file_path}")
        with open(file_path + ".html", "wb") as fp:
            fp.write(doc_instance_html)

        # https://wkhtmltopdf.org/usage/wkhtmltopdf.txt,
        p_res = subprocess.run(args=["wkhtmltopdf",
                                        "--dpi", "72",
                                        "--margin-top", "0",
                                        "--margin-left", "0",
                                        "--margin-right", "0",
                                        "--margin-bottom", "0",
                                        f"{file_path}.html",
                                        f"{file_path}.pdf"], capture_output=True, text=True)
        logging.debug(f"({job_id}) - stdout wkhtmltopdf {p_res}")

        insert_barcode_in_pdf(pdf_file_path=f"{file_path}.pdf",
                                tmp_dir=job_work_dir)
    ######
    
    
    """

if __name__ == '__main__':
    app.run(debug=True, port=8001)
