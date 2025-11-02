from flask import Blueprint, render_template, request, jsonify, g
from app.models import Lectures
from .. import db
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('time-table', __name__, url_prefix='/time-table')

@bp.route('/')
def show() :
    # JS를 이용해서 만든 url에서 grade값과 semester값 가져오기
    grade = request.args.get('grade', default=1, type=int)
    semester = request.args.get('semester', default=1, type=int)
    
    # 학년과 학기를 만족하는 강의 목록 가져오기
    slots = Lectures.query.filter_by(grade=grade, semester=semester).all()

    time_table = {}
    for slot in slots :
        # 각 [요일_교시]를 키로 하여 딕셔너리 생성
        key = f"{slot.day}_{slot.period}"
        time_table[key] = slot

    return render_template('time_table.html', time_table=time_table, grade=grade, semester=semester)

@bp.route('/api/update', methods=['POST',])
def update() :
    # 로그인이 안돼있을 경우
    if not g.admin :
        return jsonify({'success' : False, 'message' : '관리자 권한 필요'}), 403
    
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': '잘못된 요청'}), 400
    
    grade = data.get('grade')
    semester = data.get('semester')
    day = data.get('day')
    period = data.get('period')
    lecture_name = data.get('lecture_name', '').strip()
    professor = data.get('professor').strip()
    classroom = data.get('classroom').strip()
    color = data.get('color', '#FFFFFF')

    if not all([grade, semester, day, period, lecture_name, professor, classroom]) :
        return jsonify({'success' : False, 'message' : '모든 필드를 입력해야 합니다.'})
    
    try :
        slot = Lectures.query.filter_by(grade=grade, semester=semester, day=day, period=period).first()

        if not slot :
            slot = Lectures(
                grade = grade, semester=semester, day=day, period=period,
                lecture_name=lecture_name, professor=professor,
                classroom=classroom, color=color
            )
            db.session.add(slot)
            print(f"API - 추가 : {grade}-{semester}/{day}/{period} - {lecture_name}")
        else :
            slot.lecture_name = lecture_name
            slot.professor = professor
            slot.classroom = classroom
            slot.color = color
            print(f"API - 수정 : {grade}-{semester}/{day}/{period} - {lecture_name}")
        
        db.session.commit()
        return jsonify({'success': True, 'message': '저장 완료'}), 200
    
    except Exception as e :
        db.session.rollback()
        print(f"API Update 오류: {e}")
        return jsonify({'success':False, 'message': f'DB 저장 실패 : {e}'}), 500
    
@bp.route('/api/delete', methods=['POST'])
def delete() :
    if not g.admin :
        return jsonify({'success' : False, 'message' : '관리자 권한 필요'}), 403
    
    data = request.get_json()

    if not data :
        return jsonify({'success': False, 'message': '잘못된 요청'}), 400
    
    grade = data.get('grade')
    semester = data.get('semester')
    day = data.get('day')
    period = data.get('period')

    if not all([grade, semester, day, period]) :
        return jsonify({'success': False, 'message': '필수 정보 누락'}), 400
    
    try :
        slot = Lectures.query.filter_by(grade=grade,semester=semester,day=day,period=period).first()

        if slot :
            db.session.delete(slot)
            db.session.commit()
            print(f"API - 삭제 : {grade}-{semester}/{day}/{period}")
            return jsonify({'success' : True, 'message':'삭제 완료'}), 200
        else :
            print(f"API - 삭제 실패 (데이터 없음) : {grade}-{semester}/{day}/{period}")
            return jsonify({'success' : False, 'message':'삭제할 데이터 없음'}), 404
        
    except Exception as e :
        db.session.rollback()
        print(f"API Delete 오류 : {e}")
        return jsonify({'success' : False, 'message':f'DB 삭제 실패: {e}'}), 500