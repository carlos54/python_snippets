from flask import Blueprint, Response, render_template, make_response, abort, request, json, url_for, jsonify
from jinja2 import TemplateNotFound 
import os
import secrets
import logging
import shutil
import subprocess
from jsonschema import validate, ValidationError  # type: ignore
from typing import Dict, List
##########################
from mailing.resources.utils import merge_pdf, format_genre, format_date, insert_barcode_in_pdf

import time

bp = Blueprint('resource_mail', __name__)
pwd = os.path.dirname(__file__)

@bp.record
def copy_appconfig(setup_state):
    bp.config = dict([(key,value) for key,value in setup_state.app.config.items()])
    #load validator SCHEMA of the resource (to only load schema once)
    with open(os.path.join(pwd, "validator.schema"))as f:
        bp.config['SCHEMA'] = json.loads(f.read())



@bp.route("/mail/<mail_id>", methods=["GET"])
def get_mail(mail_id):
    """ return mail pdf file (Content-Type "application/pdf") 
    if process statuts is "finished"and the job is success.
    Other wise return process the status json format
    status : queued, started, deferred, finished, and failed
    """
    log_id = secrets.token_hex(8)
    logging.info("******** GET /mail - log id : %s", log_id)
      
    q = bp.config['mail_rq'] 
    job = q.fetch_job(mail_id)
    if not job:
        logging.error(f"({log_id}) ABORT - mail don't exist : {mail_id}")
        abort(404, f"ABORT - mail don't exist : {mail_id}")
    
    res = {'id':job.get_id(), 
            'statuts': job.get_status()}
    
    #add return object from the mail process to response
    if job.result:
        res.update(job.result)

    response = jsonify(res)
    if job.get_status() == "finished" and res.get('success', False) == True:
        with open(res.get('file', None), 'rb') as f:
            binary_pdf = f.read()
            response = make_response(binary_pdf)
            response.headers['response-json'] =  json.dumps(res) 
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f"attachment; filename={res.get('filename', None)}"
   
    logging.info(f"({log_id}) - response : {res}")
    return response


@bp.route("/mail", methods=["POST"])
def create_mail():
    """ merge template and the respondents file
    needed parameter :
    - "template_id"
    - "respondents" json data (schema mail_validator.schema)
    => json with mail id and status
    """
   
    log_id = secrets.token_hex(8)
    logging.info("******** POST /mail - log id : %s", log_id)
   
    ##### check post data param to process
    template_id = request.form.get('template_id') 
    if not template_id :
        logging.error(f"({log_id}) ABORT - Missing data payload - template_id : str")
        abort(403, "Missing data payload - template_id : str")

    json_bytes = request.files.get("respondents")
    if not json_bytes :
        logging.error(f"({log_id}) ABORT - Missing data payload - respondents : application/json file")
        abort(403, """Missing data payload 
              - respondents : application/json file""")
          
    # check if is a valide file and valide schema
    try:
        respondents = json.loads(json_bytes.read())
        validate(instance=respondents, schema=bp.config['SCHEMA'])
    except ValidationError:
        logging.error(f"({log_id}) ABORT -respondents json application/json not valide")
        abort(403, "respondents json application/json not valide") 
    except:
        logging.error(f"({log_id}) ABORT - respondents json application/json file corrupt")
        abort(403, "respondents json application/json file corrupt") 

    # check if all lang have it's template available
    langs = []
    _ = [langs.extend(r.get('apply_lang')) for r in respondents]
    for lang in set(langs):
        try:
            render_template(f'{template_id}_{lang}.html')
        except TemplateNotFound:
            logging.error(f"({log_id}) ABORT - missing template {template_id}_{lang}.html")
            abort(404, f"missing template {template_id}_{lang}.html")
    
    # check if "id" is unique
    ids = [r.get('id') for r in respondents]
    if len(ids) != len(set(ids)):
        logging.error(f"({log_id}) ABORT - data issue : field *id* is not unique")
        abort(403, "data issue : field *id* is not unique")
    
    logging.info(f"({log_id}) - data valided : {template_id} / respondents : {len(respondents)}")
    #####

    ##### create working job directory
    job_work_dir = os.path.join(bp.config.get('TMP_DIR'), log_id)
    if not os.path.exists(job_work_dir):
        os.makedirs(job_work_dir)

    if not os.path.exists(job_work_dir):
        logging.error(f"({log_id}) ABORT - permission mkdir job_work_dir failed")
        abort(500, "OSError, permission mkdir job_work_dir failed") 
        
    # save json data file received and validaded    
    with open(os.path.join(job_work_dir,"data.json"), "x") as f:
        json.dump(respondents, f, indent=4) 

    ### add job to the api queue for asynchrone execution
    q = bp.config['mail_rq']
    params = {
            'log_id':log_id,
            'respondents':respondents,
            'job_work_dir': job_work_dir,
            'template_id':template_id
            }
    job = q.enqueue(process_mail,
                    result_ttl=60*60*24*360,
                    description = f"log_id : {log_id}",
                     **params)

   
    res = {'id':job.get_id(), 
            'statuts': job.get_status(),
            'template_id': template_id}


    logging.info(f"({log_id}) - process_mail() add to queue : {res}")
    return jsonify(res)


#RUN in queue asynchron process
def process_mail(log_id:str, respondents:List,
                template_id:str, job_work_dir:str) -> Dict[str, object]:
    
    
    ##### inner function to process one mail 
    def process_respondent(resp_data):
        logging.debug(f"({log_id}) - vars current instance : {json.dumps(resp_data)}")
        work_dir_resp = os.path.join(job_work_dir, str(resp_data.get('id')))
        os.makedirs(work_dir_resp)
       
        ### create the dict of apply_vars
        doc_data = {}
        apply_vars : List[dict] = resp_data.get('apply_vars')
        for var in apply_vars:
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
            logging.debug(f"({log_id}) - stdout wkhtmltopdf {p_res}")

            # note : mettre les barcode en static si c'est toujours les même...
            insert_barcode_in_pdf(pdf_file_path=f"{file_path}.pdf",
                                tmp_dir=work_dir_resp)
            
        #merge all lang of respondent 
        # and move file to root work_dir for the futur total merge
        resp_all_langs_mail_pdf = merge_pdf(dir_path=work_dir_resp)
        shutil.move(resp_all_langs_mail_pdf, job_work_dir)
        logging.info(f"""({log_id}) - respondent : {resp_data.get('id')} - {resp_all_langs_mail_pdf}""")
        return resp_all_langs_mail_pdf
    #####
    
    
    ##### process merging
    merge_filename = "root_merge_file.pdf"
    job_res : Dict = { 'log_id' : log_id, 
               'filename': None, 
               'file': None,
               'respondents' : [],
                'template_id': template_id}  
    try :
        for r in respondents:
           log = {'id':r.get('id'),'success':False, 'file': None}
           log['file'] = process_respondent(r)
           if log['file']:
               log['success'] = True
           job_res['respondents'].append(log)
        
        merge_file = merge_pdf(dir_path=job_work_dir, file_name=merge_filename)
    except BaseException as e:
        job_res['success'] = False
        job_res['error'] = f"ABORT - process_respondent error {r} - {e}"
        
    else :
        job_res['success'] = True
        job_res['file'] = merge_file 
        job_res['filename'] =  merge_filename
       
    finally:
        with open(os.path.join(job_work_dir,"log.json"), "w", encoding="utf-8") as f :
            json.dump(job_res, f, indent=4)
           
    logging.info(f"({log_id}) - process_mail() asynchrone exec finished :  {job_res}")   
    return job_res
