from flask import Blueprint, render_template

bp = Blueprint('introduce', __name__, url_prefix='/introduce')

@bp.route('/')
def show() :
    return render_template('introduce_page.html') 