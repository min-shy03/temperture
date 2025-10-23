from flask import Blueprint, render_template

bp = Blueprint('time-table', __name__, url_prefix='/time-table')

@bp.route('/')
def show() :
    return render_template('time_table.html')