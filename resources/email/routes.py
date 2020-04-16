
from flask import Blueprint, Response, render_template, make_response, abort, request, json, url_for
from flask_mail import Mail, Message
import os
import secrets
import logging
import shutil
from jsonschema import validate, ValidationError
from bs4 import BeautifulSoup
from typing import Dict, List
##########################
from mailing.resources.utils import format_genre, format_date


bp = Blueprint('resource_email', __name__)
mail = Mail()
pwd = os.path.dirname(__file__)
@bp.record
def copy_appconfig(setup_state):
    mail.init_app(setup_state.app) 
    bp.config = dict([(key,value) for key,value in setup_state.app.config.items()])
    #load validator SCHEMA of the resource (to only load schema once)
    with open(os.path.join(pwd, "validator.schema"))as f:
        bp.config['SCHEMA'] = json.loads(f.read())


@bp.route("/email", methods=["POST"])
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
        validate(instance=respondents, schema=bp.config['SCHEMA'])
    except ValidationError:
        logging.error(f"({job_id}) ABORT -respondents json application/json not valide")
        abort(403, "respondents json application/json not valide") 
    except:
        logging.error(f"({job_id}) ABORT - respondents json application/json file corrupt")
        abort(403, "respondents json application/json file corrupt") 

    # check if all block lang are in the template
    langs = []
    _ = [langs.extend(r.get('apply_lang')) for r in respondents]
    template_path = os.path.join(bp.config['TEMPLATE_DIR'], f"{template_id}.html")
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
    job_work_dir = os.path.join(bp.config['TMP_DIR'], job_id)
    if not os.path.exists(job_work_dir):
        os.makedirs(job_work_dir)

    if not os.path.exists(job_work_dir):
        logging.error(f"({job_id}) ABORT - permission mkdir job_work_dir failed")
        abort(500, "OSError, permission mkdir job_work_dir failed") 
    # save json data file received and validaded  
    with open(os.path.join(job_work_dir,"data.json"), "x") as f:
        f.write(json.dumps(respondents))
    
       
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
            logging.error(f"({job_id}) - error - respondent : {r} - {e}")
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
    
    # ajouter resume job par email
    return r

    
