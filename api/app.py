from flask import Flask, render_template, make_response, abort, request, json, url_for
from jinja2 import TemplateNotFound 
import tempfile
import os
import secrets
import logging
import shutil
import subprocess
from textwrap import wrap
from jsonschema import validate, ValidationError
import numpy

from typing import Dict, List
##########################
from api.barcode import insert_barcode_in_pdf
from api.utils import merge_pdf, format_genre, format_date


app = Flask(__name__)

PWD = os.path.dirname(__file__)
TMP_DIR = os.path.join(PWD, 'temps/')
LOG_DIR = os.path.join(PWD, 'logs/')
STC_DIR = os.path.join(PWD, 'static/')

app.config['TEMP_DIR_PATH'] = TMP_DIR

# Log config
logfile_path = ''.join([LOG_DIR, "main.log"])
logging.basicConfig(filename=logfile_path,
                    format='%(asctime)s %(message)s',
                    level=logging.INFO, filemode='w')


#load validator (to only load schema one time)
MAIL_SCHEMA = None # cannot use falsk url_for at this time
with open(''.join([STC_DIR, "mail_validator.schema"]))as f:
    MAIL_SCHEMA = json.loads(f.read())
    
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


@app.route("/mail/<print_id>", methods=["GET"])
def info_print(print_id):
    """ return print log """
    pass


@app.route("/mail", methods=["POST"])
def new_print():
    """ merge template and the respondents file 
    => return "application/pdf" as Content-Disposition = attachment
    """
   
    job_id = secrets.token_hex(8)
    logging.info("******** /mail  - id : %s", job_id)
        
    ##### check post data param to process
    template_id = request.form.get('template_id') 
    if not template_id :
        logging.error(f"({job_id}) ABORT - Missing data payload - template_id : str")
        abort(403, "Missing data payload - template_id : str")

    json_file = request.files.get("respondents")
    if not json_file :
        logging.error(f"({job_id}) ABORT - Missing data payload - respondents : application/json file")
        abort(403, """Missing data payload 
              - respondents : application/json file""")
          
    # check if is a valide file and valide schema
    try:
        respondents = json.loads(json_file.read())
        validate(instance=respondents, schema=MAIL_SCHEMA)
    except ValidationError:
        logging.error(f"({job_id}) ABORT -respondents json application/json not valide")
        abort(403, "respondents json application/json not valide") 
    except:
        logging.error(f"({job_id}) ABORT - respondents json application/json file corrupt")
        abort(403, "respondents json application/json file corrupt") 

    # check if all lang have it's template available
    langs = []
    _ = [langs.extend(r.get('apply_lang')) for r in respondents]
    for lang in langs:
        try:
            render_template(f'{template_id}_{lang}.html')
        except TemplateNotFound:
            logging.error(f"({job_id}) ABORT - missing template {template_id}_{lang}.html")
            abort(404, f"missing template {template_id}_{lang}.html")
    
    # check if "id" is unique
    ids = [r.get('id') for r in respondents]
    if len(ids) != len(set(ids)):
        logging.error(f"({job_id}) ABORT - data issue : field *id* is not unique")
        abort(403, "data issue : field *id* is not unique")
    
    logging.info(f"({job_id}) - data valided : {template_id} / respondents : {len(respondents)}")
    #####

    ##### create working job directory
    job_work_dir = os.path.join(app.config.get('TEMP_DIR_PATH'), job_id)
    if not os.path.exists(job_work_dir):
        os.makedirs(job_work_dir)

    if not os.path.exists(job_work_dir):
        logging.error(f"({job_id}) ABORT - permission mkdir job_work_dir failed")
        abort(500, "OSError, permission mkdir job_work_dir failed") 
    # save json data file received and validaded    
    data_file = os.path.join(job_work_dir,"data.json")    
    json_file.save(os.path.join(job_work_dir,data_file))  
       
    ##### inner function to process one mail 
    def process_respondent(resp_data: Dict[str, object]):
        logging.debug(f"({job_id}) - vars current instance : {json.dumps(resp_data)}")
        work_dir_resp = os.path.join(job_work_dir, str(resp_data.get('id')))
        os.makedirs(work_dir_resp)
        ### create the dict of apply_vars
        doc_data = {}
        for var in resp_data.get('apply_vars'):
            doc_data[var.get('name', 'none')] = var.get('value', 'none')
        
        ### flag the variable who are lang_sensitive and need format reprocessing 
        apply_fn = {}
        for var in resp_data.get('apply_vars'):
            key = var.get('name', 'none')
            apply_fn[key+"_format_genre"] = (var.get('lang_sensitive', False) == True and var.get('format_process', None) == "genre()")
            apply_fn[key+"_format_date"] = (var.get('lang_sensitive', False) == True and var.get('format_process', None) == "date()")
           
        ### process doc 
        for lang in resp_data.get('apply_lang'):
            #reprocess data if the variable is lang_sensitive
            for key in doc_data:
                if apply_fn.get(key+"_format_genre"):
                    doc_data[key] = format_genre(lang, str(doc_data[key]))
                elif apply_fn.get(key+"_format_date"):
                    doc_data[key] = format_date(lang, str(doc_data[key]))
            
            doc_data['apply_lang'] = lang #apply_lang is avalaible for the template 
            html = render_template(f'{template_id}_{lang}.html',
                                    **doc_data).encode('utf-8')
            file_path = os.path.join(work_dir_resp, secrets.token_hex(8))
            
            with open(file_path + ".html", "wb") as fp:
                fp.write(html)
            
            #convert html to pdf (https://wkhtmltopdf.org)
            p_res = subprocess.run(args=["wkhtmltopdf",
                                            "--dpi", "72",
                                            "--margin-top", "0",
                                            "--margin-left", "0",
                                            "--margin-right", "0",
                                            "--margin-bottom", "0",
                                            f"{file_path}.html",
                                            f"{file_path}.pdf"],
                                            capture_output=True, text=True)
            logging.debug(f"({job_id}) - stdout wkhtmltopdf {p_res}")

            # note : mettre les barcode en static si c'est toujours les même...
            insert_barcode_in_pdf(pdf_file_path=f"{file_path}.pdf",
                                tmp_dir=work_dir_resp)
            
        resp_all_langs_mail_pdf = merge_pdf(dir_path=work_dir_resp)
        shutil.move(resp_all_langs_mail_pdf, job_work_dir)
        logging.info(f"""({job_id}) - respondent : {resp_data.get('id')} - {resp_all_langs_mail_pdf}""")
    #####
    
    ##### process merging
    try :
        for r in respondents:
            process_respondent(r)
        merge_file = merge_pdf(dir_path=job_work_dir, file_name=".".join([job_id,"pdf"]))
    except BaseException as e:
        logging.error(f"({job_id}) ABORT - process_respondent error {r} - {e}")
        abort(500, e) 
        
    logging.info(f"({job_id}) - final mail : {merge_file}")
    
    ##### return pdf
    with open(merge_file, 'rb') as f:
        binary_pdf = f.read()
        response = make_response(binary_pdf)
        response.headers['job-id'] = str(job_id)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={job_id}.pdf'
            
    
    return response




if __name__ == '__main__':
    app.run(debug=True, port=8001)
    logging.info('READY TO WORK')
