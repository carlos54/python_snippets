from flask import Blueprint, jsonify, json, Response, abort, request
import logging
import os
import secrets
import re
import string 
from bs4 import BeautifulSoup
####
from mailing.resources.utils import convert_date

bp = Blueprint('template', __name__)

 
@bp.record
def copy_appconfig(setup_state):
    bp.config = dict([(key,value) for key,value in setup_state.app.config.items()])

def template_exist(template_name:str) -> bool:
    templates = json.loads(list_template().data)
    for t in templates:
        if t.get('name') == template_name:
            return True
    return False
    
    
@bp.route("/template", methods=["GET"])
def list_template():
    """ List all template avalaible
     return application/json [{id:str, modified:str (date '%d %b %Y')}] """
    all_template = []
    for entry in os.scandir(bp.config.get("TEMPLATE_DIR")):
        if entry.is_file() and entry.name.endswith(".html"):
            template_file = {'name': entry.name,
                             'modified':convert_date(entry.stat().st_mtime)}
            #extract id and lang
            template_id, *lang = entry.name.split("_")
            if len(lang) == 0:
                template_id, _ = entry.name.split(".")
            else:
                lang, _ = lang[0].split(".")
                template_file.update({'lang' : lang})
            template_file.update({'id' : template_id})
            all_template.append(template_file)
                 
    return jsonify(all_template)


@bp.route("/template/<template_id>/<lang>", methods=["GET"])
def show_template(template_id, lang):
    """ return base mail template  """
    return render_template(f'{template_id}_{lang}.html')


@bp.route("/template/<template_id>", methods=["GET"])
def show_etemplate(template_id):
    """ return base email template  """
    return render_template(f'{template_id}.html')



@bp.route("/template/<lang>", methods=["POST"])
def transfer_template(lang):
    """ transfer the new mail template to make it avalaible
    for mail template we need one template.html for each lang
    needed post payload :
    - "template_id" : str (no special charactere allowed)
    - "html_file" : template .html file
    """
    job_id = secrets.token_hex(8)
    logging.info("******** POST /template/<lang>  - id : %s", job_id)
    ### check post data
    lang = lang.casefold()
    if not lang in bp.config.get("LANG_ALLOWED").split(";"):
        logging.error(f"({job_id}) ABORT - LANG_ NOT ALLOWED : {lang}")
        abort(403, F"ABORT - lang not allowed : '{lang}'")
    
    template_id = request.form.get('template_id') 
    if not template_id :
        logging.error(f"({job_id}) ABORT - Missing data payload - template_id : str")
        abort(403, "Missing data payload - template_id : str")
    
    #template_id contains special caractere
    template_id = template_id.replace(" ", "")
    invalidcharacters = set(string.punctuation)
    if any(char in invalidcharacters for char in template_id):
        logging.error(f"({job_id}) ABORT - template_id - special character not allowed : '{template_id}'")
        abort(403, f"ABORT - template_id - special character not allowed : '{template_id}'")
        
   
    #template name already exit ?
    template_name = "".join([template_id, "_", lang, ".html"])
    if template_exist(template_name):
        logging.error(f"({job_id}) ABORT - template already exist : {template_name}")
        abort(403, f"ABORT - template already exist (use PUT methode to update it) : {template_name}")

    
    #template file exit and is parsable html
    html_bytes = request.files.get("html_file")
    if not html_bytes :
        logging.error(f"({job_id}) ABORT - Missing data payload - html_file : text/html")
        abort(403, "ABORT - missing data file payload html_file : text/html")
    
    #it´s html ?
    try :
        content = html_bytes.read().decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')
        if not soup.find("body"):
            logging.error(f"({job_id}) ABORT - template html_file is not html")
            abort(403, "ABORT - template html_file is not html")
    except:
        logging.error(f"({job_id}) ABORT - template html_file is not html")
        abort(403, "ABORT - template html_file is not html")
    
    
    #template seems ok, save it
    file = os.path.join(bp.config.get("TEMPLATE_DIR"),template_name)
    with open(file, "x") as f:
        f.write(content)
    
    success = (os.path.exists(file))
    
    res = {'log_id':job_id, 'success':success,
           'template_id': template_id,
           'lang':lang, 'template_name':template_name}

    logging.info(f"({job_id}) - : {res}")
    return jsonify(res)


@bp.route("/template", methods=["POST"])
def transfer_etemplate():
    """ transfer the new email template to make it avalaible
    for email template all the lang are in same template.hmtl
    the block for each lang have to be handle by the Jinga syntaxe, like :
    {% if apply_lang_fr %} ... {% endif %}
    needed post payload :
    - "template_id" : str (no special charactere allowed)
    - "html_file" : template .html file
    """
    job_id = secrets.token_hex(8)
    logging.info("******** POST /template - id : %s", job_id)
    ### check post data
    template_id = request.form.get('template_id') 
    if not template_id :
        logging.error(f"({job_id}) ABORT - Missing data payload - template_id : str")
        abort(403, "Missing data payload - template_id : str")
    
    #template_id contains special caractere
    template_id = template_id.replace(" ", "")
    invalidcharacters = set(string.punctuation)
    if any(char in invalidcharacters for char in template_id):
        logging.error(f"({job_id}) ABORT - template_id - special character not allowed : '{template_id}'")
        abort(403, f"ABORT - template_id - special character not allowed : '{template_id}'")
        
    
    #template name already exit ?
    template_name = "".join([template_id, ".html"])
    if template_exist(template_name):
        logging.error(f"({job_id}) ABORT - template already exist : {template_name}")
        abort(403, f"ABORT - template already exist (use PUT methode to update it) : {template_name}")

    
    #template file exit and is parsable html
    html_bytes = request.files.get("html_file")
    if not html_bytes :
        logging.error(f"({job_id}) ABORT - Missing data payload - html_file : text/html")
        abort(403, "ABORT - missing data file payload html_file : text/html")
    
    #it´s html ?
    try :
        content = html_bytes.read().decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')
        if not soup.find("body"):
            logging.error(f"({job_id}) ABORT - template html_file is not html")
            abort(403, "ABORT - template html_file is not html")
    except:
        logging.error(f"({job_id}) ABORT - template html_file is not html")
        abort(403, "ABORT - template html_file is not html")
    
    
    #template seems ok, save it
    file = os.path.join(bp.config.get("TEMPLATE_DIR"),template_name)
    with open(file, "x") as f:
        f.write(content)
    success = (os.path.exists(file))
    
    res = {'log_id':job_id, 'success':success,
           'template_id': template_id, 'template_name':template_name}

    logging.info(f"({job_id}) - : {res}")
    return jsonify(res)


@bp.route("/template/<template_id>/<lang>", methods=["DELETE"])
def delete_template(template_id, lang):
    """ delete exiting mail template """
    job_id = secrets.token_hex(8)
    logging.info("******** DELETE /template/<template_id>/<lang> - id : %s", job_id)
    
    ### check template_id
    template_name = "".join([template_id,"_",lang,".html"])
    if not template_exist(template_name):
        logging.error(f"({job_id}) ABORT - template doesn't exist : {template_name}")
        abort(403, f"ABORT - template doesn't exist : {template_name}")
    
    
    #template seems ok, remove it
    file = os.path.join(bp.config.get("TEMPLATE_DIR"), template_name)
    os.remove(file)
    success = (not os.path.exists(file))

    res = {'log_id':job_id, 'success': success,
           'template_id': template_id, 'template_name':template_name}

    logging.info(f"({job_id}) - : {res}")
    return jsonify(res)

@bp.route("/template/<template_id>", methods=["DELETE"])
def delete_etemplate(template_id):
    """ delete exiting email template """
    job_id = secrets.token_hex(8)
    logging.info("******** DELETE /template/<template_id> - id : %s", job_id)
    
    ### check template_id
    template_name = "".join([template_id, ".html"])
    if not template_exist(template_name):
        logging.error(f"({job_id}) ABORT - template doesn't exist : {template_name}")
        abort(403, f"ABORT - template doesn't exist : {template_name}")
    
    
    #template seems ok, remove it
    file = os.path.join(bp.config.get("TEMPLATE_DIR"), template_name)
    os.remove(file)
    success = (not os.path.exists(file))

    res = {'log_id':job_id, 'success': success,
           'template_id': template_id, 'template_name':template_name}

    logging.info(f"({job_id}) - : {res}")
    return jsonify(res)


@bp.route("/template/<template_id>/<lang>", methods=["PUT"])
def replace_template(template_id, lang):
    """ replace exiting mail template 
    needed put payload :
     - "html_file" : template .html file
    """
    job_id = secrets.token_hex(8)
    logging.info("******** PUT /template/<template_id>/<lang> - id : %s", job_id)
    
    lang = lang.casefold()
    if not lang in bp.config.get("LANG_ALLOWED").split(";"):
        logging.error(f"({job_id}) ABORT - lang not allowed : {lang}")
        abort(403, F"ABORT - lang not allowed : '{lang}'")
        
    ### check template_id
    #template_id contains special caractere
    template_id = template_id.replace(" ", "")
    invalidcharacters = set(string.punctuation)
    if any(char in invalidcharacters for char in template_id):
        logging.error(f"({job_id}) ABORT - template_id - special character not allowed : '{template_id}'")
        abort(403, f"ABORT - template_id - special character not allowed : '{template_id}'")
   
    template_name = "".join([template_id,"_", lang, ".html"])
    if not template_exist(template_name):
        logging.error(f"({job_id}) ABORT - template doesn't exist : {template_name}")
        abort(403, f"ABORT - template doesn't exist : {template_name}")
    
    #template file exit and is parsable html
    html_bytes = request.files.get("html_file")
    if not html_bytes :
        logging.error(f"({job_id}) ABORT - Missing data payload - html_file : text/html")
        abort(403, "ABORT - missing data file payload html_file : text/html")
    
    #it´s html ?
    try :
        content = html_bytes.read().decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')
        if not soup.find("body"):
            logging.error(f"({job_id}) ABORT - template html_file is not html")
            abort(403, "ABORT - template html_file is not html")
    except:
        logging.error(f"({job_id}) ABORT - template html_file is not html")
        abort(403, "ABORT - template html_file is not html")
    
    
    #template seems ok, save it
    file = os.path.join(bp.config.get("TEMPLATE_DIR"),template_name)
    with open(file, "w") as f:
        f.write(content)
    success = (os.path.exists(file))
    
    res = {'log_id':job_id, 'success':success,
           'template_id': template_id, 'lang':lang,
           'template_name':template_name}

    logging.info(f"({job_id}) - : {res}")
    return jsonify(res)


@bp.route("/template/<template_id>", methods=["PUT"])
def replace_etemplate(template_id):
    """ replace exiting email template
    for email template all the lang are in same template.hmtl
    the block for each lang have to be handle by the Jinga syntaxe, like :
    {% if apply_lang_fr %} ... {% endif %}
     needed put payload :
    - "html_file" : template .html file
    """
    job_id = secrets.token_hex(8)
    logging.info("******** PUT /template/<template_id> - id : %s", job_id)
    
    ### check template_id
    #template_id contains special caractere
    template_id = template_id.replace(" ", "")
    invalidcharacters = set(string.punctuation)
    if any(char in invalidcharacters for char in template_id):
        logging.error(f"({job_id}) ABORT - template_id - special character not allowed : '{template_id}'")
        abort(403, f"ABORT - template_id - special character not allowed : '{template_id}'")
   
    template_name = "".join([template_id, ".html"])
    if not template_exist(template_name):
        logging.error(f"({job_id}) ABORT - template doesn't exist : {template_name}")
        abort(403, f"ABORT - template doesn't exist : {template_name}")
    
    
    #template file exit and is parsable html
    html_bytes = request.files.get("html_file")
    if not html_bytes :
        logging.error(f"({job_id}) ABORT - Missing data payload - html_file : text/html")
        abort(403, "ABORT - missing data file payload html_file : text/html")
    
    #it´s html ?
    try :
        content = html_bytes.read().decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')
        if not soup.find("body"):
            logging.error(f"({job_id}) ABORT - template html_file is not html")
            abort(403, "ABORT - template html_file is not html")
    except:
        logging.error(f"({job_id}) ABORT - template html_file is not html")
        abort(403, "ABORT - template html_file is not html")
    
    
    #template seems ok, save it
    file = os.path.join(bp.config.get("TEMPLATE_DIR"),template_name)
    with open(file, "w") as f:
        f.write(content)
    success = (os.path.exists(file))
    
    res = {'log_id':job_id, 'success':success,
           'template_id': template_id, 'template_name':template_name}

    logging.info(f"({job_id}) - : {res}")
    return jsonify(res)
