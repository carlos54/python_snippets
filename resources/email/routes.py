
from flask import Blueprint, Response, render_template, make_response, abort, request, json, jsonify, url_for
from flask_mail import Mail, Message
import os
import secrets
import logging
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


@bp.route("/email/<mail_id>", methods=["GET"])
def get_email(mail_id):
    """ return email process status
    status : queued, started, deferred, finished, and failed
    """
    log_id = secrets.token_hex(8)
    logging.info("******** GET /email - log id : %s", log_id)
      
    q = bp.config['email_rq'] 
    job = q.fetch_job(mail_id)
    if not job:
        logging.error(f"({log_id}) ABORT - email don't exist : {mail_id}")
        abort(404, f"ABORT - email don't exist : {mail_id}")
    
    res = {'id':job.get_id(), 
            'statuts': job.get_status()}
    
    #add return object from the mail process to response
    if job.result:
        res.update(job.result)
        
    logging.info(f"({log_id}) - response : {res}")
    return jsonify(res)


@bp.route("/email", methods=["POST"])
def create_email():
    """ create email campaign trought app queue processing (asynchron)
    needed parameter :
    - "template_id" : str
    - "respondents" : json data (schema email_validator.schema)
    - ("test_recipients") : str (split ";") =>  "mail1@statec.lu;mail2@statec.lu"
    => return "application/json" with id and status
    """
   
    log_id = secrets.token_hex(8)
    logging.info("******** POST /email  - id : %s", log_id)
    

    ##### check post data param to process4
    test_recipients = [] # optional
    test_recipients_str = request.form.get('test_recipients', None)
    if test_recipients_str:
        try:
            test_recipients = list(str(test_recipients_str).split(";"))
        except:
            logging.error(f"({log_id}) ABORT - test_recipients  str (sep ;) not valide")
            abort(403, "ABORT - test_recipients  str (sep ;) not valid")  
    
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
            logging.error(f"({log_id}) ABORT - template **{template_id}** missing block lang : {lang}")
            abort(404, f"ABORT - template **{template_id}** missing block lang : {lang}")

    # check if template as title (use as subject of email)
    email_subject = BeautifulSoup(template_content, features="html.parser").title.string
    if not email_subject:
        logging.error(f"({log_id}) ABORT - the template has no title, title use as email subject")
        abort(500, "ABORT - the template has no title, title use as email subject") 
        
    # check if 1"id" is unique
    ids = [r.get('id') for r in respondents]
    if len(ids) != len(set(ids)):
        logging.error(f"({log_id}) ABORT - data issue : field *id* is not unique")
        abort(403, "data issue : field *id* is not unique")
    
    logging.info(f"({log_id}) - data valided : {template_id} / respondents : {len(respondents)}")
    #####
     
    ##### create working job directory
    job_work_dir = os.path.join(bp.config['TMP_DIR'], log_id)
    if not os.path.exists(job_work_dir):
        os.makedirs(job_work_dir)

    if not os.path.exists(job_work_dir):
        logging.error(f"({log_id}) ABORT - permission mkdir job_work_dir failed")
        abort(500, "OSError, permission mkdir job_work_dir failed") 
    # save json data file received and validaded  
    with open(os.path.join(job_work_dir,"data.json"), "x") as f:
        json.dump(respondents, f, indent=4)
    
    ### add job to the api queue for asynchrone execution
    q = bp.config['email_rq']
    params = {
            'log_id':log_id,
            'respondents':respondents,
            'job_work_dir': job_work_dir,
            'test_recipients' : test_recipients,
            'template_id':template_id,
            'email_subject':email_subject
            }
    job = q.enqueue(process_email,
                    result_ttl=60*60*24*360,
                    description = f"log_id : {log_id}",
                     **params)

    res = {'id':job.get_id(), 
            'statuts': job.get_status(),
            'template_id': template_id}


    logging.info(f"({log_id}) - process_email() add to queue : {res}")
    return jsonify(res)
    


#RUN trougth app queue (asynchron process)
def process_email(log_id:str, respondents:List, template_id:str,
                  test_recipients:List, job_work_dir:str,
                  email_subject:str) -> Dict[str, object]:
    
    
    ##### inner function to process one mail 
    def process_respondent(resp_data: Dict[str, object], test_mode:bool):

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

        # save html to send in the job_work_dir for audit purpose
        file_path = os.path.join(job_work_dir, f"{resp_data.get('id')}.html")
        with open(file_path, "wb") as f:
            f.write(html)
       
        #replace recipients in test_mode
        recipients = resp_data.get('recipients',[])
        if test_mode:
            recipients = test_recipients

        msg = Message(email_subject, recipients=recipients)
        msg.html = html
        #mail.send(msg)
       
            
        logging.info(f"({log_id}) - respondent : {resp_data.get('id')} - EMAIL: {file_path}")
    #####
    
    
    ##### process emailing
    # init log.json of the job
    all_success = True
    # test_mode : allow to generate one mail result to test_recipients
    test_mode = (len(test_recipients) > 0)
    job_res = {'log_id':log_id, 'success':False,
               'test_mode' :test_mode, 'respondents' : []} 
   
    for r in respondents:
        r_log = {'id':r.get('id'),'success':False, 'recipients': r.get('recipients', [])}
        process_respondent(resp_data=r, test_mode=test_mode)
        try :
            _ = "bbala"
        except BaseException as e:
            logging.error(f"({log_id}) - error - respondent : {r} - {e}")
            r_log['success'] = False
            r_log['error'] = f"ABORT email {r.get('id')}  - process_respondent error - {e}"
        else :
            r_log['success'] = True
        finally:
            all_success = ((all_success and r_log['success']) == True)
            job_res['respondents'].append(r_log)
        if test_mode :
            break # only process first respondent in test_mode
        
    job_res['success']  = all_success
    
    with open(os.path.join(job_work_dir,"log.json"), "w", encoding="utf-8") as f :
        json.dump(job_res, f, indent=4)       
    
    logging.info(f"({log_id}) - asynchron process_email() finished : {job_res}")
    return job_res

    
