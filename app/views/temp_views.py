from flask import Blueprint, render_template

bp = Blueprint('temp', __name__, url_prefix='/temp')

@bp.route('/')
def show() :
    return render_template('temp_page.html')