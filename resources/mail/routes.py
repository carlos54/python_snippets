from flask import Blueprint, Response, render_template, make_response, abort, request, json, url_for
from jinja2 import TemplateNotFound 
import os
import secrets
import logging
import shutil
import subprocess
from jsonschema import validate, ValidationError
from typing import Dict, List
##########################
from mailing.resources.utils import merge_pdf, format_genre, format_date, insert_barcode_in_pdf



bp = Blueprint('resource_mail', __name__)
pwd = os.path.dirname(__file__)
@bp.record
def copy_appconfig(setup_state):
    bp.config = dict([(key,value) for key,value in setup_state.app.config.items()])
    #load validator SCHEMA of the resource (to only load schema once)
    with open(os.path.join(pwd, "validator.schema"))as f:
        bp.config['SCHEMA'] = json.loads(f.read())



@bp.route("/mail/<print_id>", methods=["GET"])
def info_print(print_id):
    """ return print log """
    pass


@bp.route("/mail", methods=["POST"])
def new_print():
    """ merge template and the respondents file
    needed parameter :
    - "template_id"
    - "respondents" json data (schema mail_validator.schema)
    => return "application/pdf" as Content-Disposition = attachment
    response.headers['mail-id'] as 
    """
   
    job_id = secrets.token_hex(8)
    logging.info("******** /mail  - id : %s", job_id)
   
    ##### check post data param to process
    template_id = request.form.get('template_id') 
    if not template_id :
        logging.error(f"({job_id}) ABORT - Missing data payload - template_id : str")
        abort(403, "Missing data payload - template_id : str")

    json_bytes = request.files.get("respondents")
    if not json_bytes :
        logging.error(f"({job_id}) ABORT - Missing data payload - respondents : application/json file")
        abort(403, """Missing data payload 
              - respondents : application/json file""")
          
    # check if is a valide file and valide schema
    try:
        respondents = json.loads(json_bytes.read())
        validate(instance=respondents, schema=bp.config['SCHEMA'])
    except ValidationError:
        logging.error(f"({job_id}) ABORT -respondents json application/json not valide")
        abort(403, "respondents json application/json not valide") 
    except:
        logging.error(f"({job_id}) ABORT - respondents json application/json file corrupt")
        abort(403, "respondents json application/json file corrupt") 

    # check if all lang have it's template available
    langs = []
    _ = [langs.extend(r.get('apply_lang')) for r in respondents]
    for lang in set(langs):
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
    job_work_dir = os.path.join(bp.config.get('TMP_DIR'), job_id)
    if not os.path.exists(job_work_dir):
        os.makedirs(job_work_dir)

    if not os.path.exists(job_work_dir):
        logging.error(f"({job_id}) ABORT - permission mkdir job_work_dir failed")
        abort(500, "OSError, permission mkdir job_work_dir failed") 
    # save json data file received and validaded    
    data_file = os.path.join(job_work_dir,"data.json")    
    json_bytes.save(os.path.join(job_work_dir,data_file))  
    
       
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
            if var.get('lang_sensitive', False) == True:
                if (var.get('format_function', None) == "genre()") :
                    apply_fn[key+"_format_genre"] = True
                elif (var.get('format_function', None) == "date()") :
                     apply_fn[key+"_format_date"] = True
                     
        ### process doc 
        for lang in resp_data.get('apply_lang'):
            #reprocess data if the variable is lang_sensitive
            for key in doc_data:
                if apply_fn.get(key+"_format_genre", False):
                    doc_data[key] = format_genre(lang, str(doc_data[key]))
                elif apply_fn.get(key+"_format_date", False):
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
        return resp_all_langs_mail_pdf
    #####
    
    ##### process merging
    # init log.json of the job
    log_job = {'id':job_id, 'success':False, 'file': None, 'respondents' : []} 
    merge_filename = ".".join([job_id,"pdf"]) 
    try :
        for r in respondents:
           log = {'id':r.get('id'),'success':False, 'file': None}
           log['file'] = process_respondent(r)
           if log['file']:
               log['success'] = True
           log_job['respondents'].append(log)
        
        merge_file = merge_pdf(dir_path=job_work_dir, file_name=merge_filename)
    except BaseException as e:
        log_job['success'] = False
        log_job['error'] = f"ABORT - process_respondent error {r} - {e}"
    else :
        log_job['success'] = True
        log_job['file'] = merge_filename
    finally:
        with open(os.path.join(job_work_dir,"log.json"), "w", encoding="utf-8") as f :
            json.dump(log_job, f, indent=4)
        
        if not log_job['success'] :
            logging.error(f"({job_id}) {log_job['error']}")
            abort(500, log_job['error'])
        
   
    
    ##### return pdf
    with open(merge_file, 'rb') as f:
        binary_pdf = f.read()
        response = make_response(binary_pdf)
        response.headers['id'] = str(job_id)
        response.headers['log'] = json.dumps(log_job)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={merge_filename}'
        
    logging.info(f"({job_id}) - success : {log_job['success']}")
    return response