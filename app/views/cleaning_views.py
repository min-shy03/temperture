from flask import Blueprint, render_template, request, jsonify
from app.models import ClassMember
from .. import db

bp = Blueprint('cleaning', __name__, url_prefix='/cleaning')

@bp.route('/')
def show() :
    grade = request.args.get('grade', default=1, type=int)

    return render_template('cleaning_page.html', grade=grade)

@bp.route('/api/add-member', methods=['POST'])
def add_member() :
    data = request.json

    grade = data.get('grade')
    name = data.get('name')
    gender = data.get('gender')
    position = data.get('position')
    
    if not all([grade, name, gender, position]) :
        return jsonify({'success' : False, 'message' : '모든 필드를 입력해야 합니다.'}), 400
    
    existing_member = ClassMember.query.filter_by(grade=grade, name=name).first()

    if existing_member :
        return jsonify({'success': False, 'message': f'{grade}학년에 이미 \'{name}\' 학생이 존재합니다.'}), 409

    try :
        member = ClassMember(grade=grade, name=name, gender=gender, position=position)
        db.session.add(member)
        db.session.commit()
        return jsonify({'success': True, 'message': '저장 완료'}), 200

    except Exception as e :
        db.session.rollback()
        print(f"API Update 오류: {e}")
        return jsonify({'success':False, 'message': f'DB 저장 실패 : {e}'}), 500