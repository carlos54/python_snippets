from flask import Blueprint
import os

bp = Blueprint('template', __name__)

@bp.record
def copy_appconfig(setup_state):
    bp.config = dict([(key,value) for key,value in setup_state.app.config.items()])


@bp.route("/template", methods=["GET"])
def list_template():
    """ return print log """
    return "ok" 


@bp.route("/template/<template_id>/<lang>", methods=["GET"])
def show_template(template_id, lang):
    """ return base mail template  """
    return render_template(f'{template_id}_{lang}.html')


@bp.route("/template/<template_id>", methods=["GET"])
def show_etemplate(template_id):
    """ return base email template  """
    return render_template(f'{template_id}_{lang}.html')



@bp.route("/template/<template_id>/<lang>", methods=["POST"])
def transfer_template(template_id, lang):
    """ transfer the new mail template to make it avalaible"""
    pass


@bp.route("/template/<template_id>", methods=["POST"])
def transfer_etemplate(template_id):
    """ transfer the new email template to make it avalaible"""
    pass


@bp.route("/template/<template_id>/<lang>", methods=["DELETE"])
def delete_template(template_id, lang):
    """ delete exiting mail template """
    pass

@bp.route("/template/<template_id>", methods=["DELETE"])
def delete_etemplate(template_id):
    """ delete exiting email template """
    pass


@bp.route("/template/<template_id>/<lang>", methods=["PUT"])
def replace_template(template_id, lang):
    """ replace exiting mail template """
    pass


@bp.route("/template/<template_id>", methods=["PUT"])
def replace_etemplate(template_id):
    """ replace exiting email template """
    pass
