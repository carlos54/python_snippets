from flask import Flask, Response, render_template, make_response, abort, request, json, url_for
from flask_mail import Mail, Message
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
from bs4 import BeautifulSoup
from typing import Dict, List
##########################
from api.barcode import insert_barcode_in_pdf
from api.utils import merge_pdf, format_genre, format_date



app = Flask(__name__)

PWD = os.path.dirname(__file__)
TMP_DIR = os.path.join(PWD, 'temps/')
LOG_DIR = os.path.join(PWD, 'logs/')
STC_DIR = os.path.join(PWD, 'static/')
TEMPLATE_DIR = os.path.join(PWD, 'templates/')

app.config['TEMP_DIR_PATH'] = TMP_DIR

## email config falsk 
#app.config['MAIL_SERVER'] : default ‘localhost’
#app.config['MAIL_PORT'] : default 25
#app.config['MAIL_USE_TLS'] : default False
#app.config['MAIL_USE_SSL'] : default False
#app.config['MAIL_DEBUG'] : default app.debug
#app.config['MAIL_USERNAME'] : default None
#app.config['MAIL_PASSWORD'] : default None
app.config['MAIL_DEFAULT_SENDER'] = "test@api.statec.lu"
#app.config['MAIL_MAX_EMAILS'] : default None
#app.config['MAIL_SUPPRESS_SEND'] : default app.testing
#app.config['MAIL_ASCII_ATTACHMENTS'] : default False
mail = Mail(app)


# Log config
logfile_path = ''.join([LOG_DIR, "main.log"])
logging.basicConfig(filename=logfile_path,
                    format='%(asctime)s %(message)s',
                    level=logging.INFO, filemode='w')


#load validator (to only load schema one time)
MAIL_SCHEMA = None # cannot use falsk url_for at this time
with open(''.join([STC_DIR, "mail_validator.schema"]))as f:
    MAIL_SCHEMA = json.loads(f.read())

EMAIL_SCHEMA = None # cannot use falsk url_for at this time
with open(''.join([STC_DIR, "email_validator.schema"]))as f:
    EMAIL_SCHEMA = json.loads(f.read())
       
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
    job_work_dir = os.path.join(app.config.get('TEMP_DIR_PATH'), job_id)
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


@app.route("/email", methods=["POST"])
def new_email():
    """ send email to respondents
    needed parameter :
    - "template_id" : str
    - "respondents" : json data (schema email_validator.schema)
    - ("test_recipients") : str (split ";") =>  "mail1@statec.lu;mail2@statec.lu"
    => return "application/json" log
    """
   
    job_id = secrets.token_hex(8)
    logging.info("******** /email  - id : %s", job_id)
    
  

    ##### check post data param to process4
    test_recipients = [] # optional
    test_recipients_str = request.form.get('test_recipients', None)
    if test_recipients_str:
        try:
            test_recipients = list(str(test_recipients_str).split(";"))
        except:
            logging.error(f"({job_id}) ABORT - test_recipients  str (sep ;) not valide")
            abort(403, "ABORT - test_recipients  str (sep ;) not valid")  
    
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
        validate(instance=respondents, schema=EMAIL_SCHEMA)
    except ValidationError:
        logging.error(f"({job_id}) ABORT -respondents json application/json not valide")
        abort(403, "respondents json application/json not valide") 
    except:
        logging.error(f"({job_id}) ABORT - respondents json application/json file corrupt")
        abort(403, "respondents json application/json file corrupt") 

    # check if all block lang are in the template
    langs = []
    _ = [langs.extend(r.get('apply_lang')) for r in respondents]
    template_path = os.path.join(TEMPLATE_DIR, f"{template_id}.html")
    template_content = None
    with open(template_path,  "r") as f:
        template_content = f.read()

    for lang in set(langs):
        lang = lang.lower()
        if not f'apply_lang_{lang}' in template_content:
            logging.error(f"({job_id}) ABORT - template **{template_id}** missing block lang : {lang}")
            abort(404, f"ABORT - template **{template_id}** missing block lang : {lang}")

    # check if template as title (use as subject of email)
    email_subject = BeautifulSoup(template_content, features="html.parser").title.string
    if not email_subject:
        logging.error(f"({job_id}) ABORT - the template has no title, title use as email subject")
        abort(500, "ABORT - the template has no title, title use as email subject") 
        
    # check if 1"id" is unique
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
    json_bytes.save(os.path.join(job_work_dir,data_file))  
    
       
    ##### inner function to process one mail 
    def process_respondent(resp_data: Dict[str, object], testing:bool):
        logging.debug(f"({job_id}) - vars current instance : {json.dumps(resp_data)}")
       
        ### process apply_vars in all apply_lang required
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
            lang = lang.lower()
            doc_data['apply_lang_'+lang] = True
            #reprocess data if the variable is lang_sensitive and it to doc_data as varname_lang
            for key in list(doc_data):
                if apply_fn.get(key+"_format_genre", False):
                    doc_data[key+"_"+lang] = format_genre(lang, str(doc_data[key]))
                elif apply_fn.get(key+"_format_date", False):
                    doc_data[key+"_"+lang] = format_date(lang, str(doc_data[key]))

        html = render_template(f'{template_id}.html',
                                **doc_data).encode('utf-8')
       
        recipients = resp_data.get('recipients',[])
        if testing :
            recipients = test_recipients

        msg = Message(email_subject, recipients=recipients)
        msg.html = html
        mail.send(msg)
        # save html to send in the job_work_dir for audit purpose
        file_path = os.path.join(job_work_dir, resp_data.get('id')+".html")
        with open(file_path, "wb") as f:
            f.write(html)
            
        logging.info(f"({job_id}) - respondent : {resp_data.get('id')} - EMAIL: {file_path}")
    #####
    
    
    ##### process emailing
    # init log.json of the job
    log_job = {'id':job_id, 'success':False, 'respondents' : []} 
    all_success = True
    test_mode = (len(test_recipients) > 0)
    print(len(test_recipients))
    for r in respondents:
        r_log = {'id':r.get('id'),'success':False, 'recipients': r.get('recipients', [])}
        try :
            process_respondent(resp_data=r, testing=test_mode)
        except BaseException as e:
            logging.error(f"({job_id}) - error - respondent : {r.get('id')} - {e}")
            r_log['success'] = False
            r_log['error'] = f"ABORT email {r.get('id')}  - process_respondent error - {e}"
        else :
            r_log['success'] = True
        finally:
            all_success = ((all_success and r_log['success']) == True)
            log_job['respondents'].append(r_log)
        if test_mode :
            break # only process first respondent in test_mode
        
    log_job['success']  = all_success
    with open(os.path.join(job_work_dir,"log.json"), "w", encoding="utf-8") as f :
        json.dump(log_job, f, indent=4)       
        

    ##### return json log
    r = Response(json.dumps(log_job), mimetype='application/json')
    r.headers['id'] = str(job_id)
    logging.info(f"({job_id}) - success : {log_job['success']}")
    return r



if __name__ == '__main__':
    app.run(debug=True, port=8001)
    logging.info('READY TO WORK')
