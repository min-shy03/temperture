from flask import Blueprint, render_template, request
from app.models import Lectures

bp = Blueprint('time-table', __name__, url_prefix='/time-table')

@bp.route('/')
def show() :
    grade = request.args.get('grade', default=1, type=int)
    semester = request.args.get('semester', default=1, type=int)
    
    slots = Lectures.query.filter_by(grade=grade, semester=semester).all()

    time_table = {}
    for slot in slots :
        key = f"{slot.day}_{slot.period}"
        time_table[key] = slot

    return render_template('time_table.html', time_table=time_table, grade=grade, semester=semester)