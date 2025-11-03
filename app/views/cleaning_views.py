from flask import Blueprint, render_template, request, jsonify
from app.models import ClassMember
from .. import db
import random

bp = Blueprint('cleaning', __name__, url_prefix='/cleaning')

@bp.route('/')
def show() :
    grade = request.args.get('grade', default=1, type=int)

    unchecked_list_unsorted = ClassMember.query.filter_by(grade=grade, check=False).all()
    checked_list_unsorted = ClassMember.query.filter_by(grade=grade, check=True).all()
    this_week_member_list_unsorted = ClassMember.query.filter_by(grade=grade, this_week=True).all()

    unchecked_list = sorted(unchecked_list_unsorted, key=lambda member : member.name)
    checked_list = sorted(checked_list_unsorted, key=lambda member : member.name)
    this_week_member_list = sorted(this_week_member_list_unsorted, key=lambda member : member.name)

    return render_template(
        'cleaning_page.html', 
        grade=grade, 
        unchecked_list=unchecked_list,
        checked_list=checked_list,
        this_week_member_list=this_week_member_list
    )

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
    
@bp.route('/api/grade-members', methods=['GET'])
def get_members_by_grade() :
    grade = request.args.get('grade')

    if not grade :
        return jsonify({"success" : False, "message" : "학년이 필요합니다."}), 400
    
    member_unsorted = ClassMember.query.filter_by(grade=grade).all()
    members = sorted(member_unsorted, key=lambda m: m.name)

    student_list = []
    for s in members :
        student_list.append({
            "id" : s.id,
            "name" : s.name,
            "position" : s.position,
            "gender" : s.gender
        })

    return jsonify(student_list)

@bp.route('/api/member/<int:student_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_mamber(student_id) :
    member = ClassMember.query.get_or_404(student_id)

    if request.method == 'GET' :
        return jsonify({
            "success" : True,
            "id" : member.id,
            "name" : member.name,
            "gender" : member.gender,
            "position" : member.position    
        })
    
    elif request.method == 'PUT' :
        data = request.json
        
        member.gender = data.get('gender')
        member.position = data.get('position')

        try :
            db.session.commit()
            return jsonify({"success" : True, "message" : "학생 정보가 수정되었습니다."})
        except Exception as e :
            db.session.rollback()
            return jsonify({"success" : False, "message" : f"수정 실패 {str(e)}"}), 500
    
    elif request.method == 'DELETE' :
        try :
            db.session.delete(member)
            db.session.commit()
            return jsonify({"success" : True, "message" : "학생이 삭제되었습니다."})
        except Exception as e :
            db.session.rollback()
            return jsonify({"success" : False, "message" : f"삭제 실패 {str(e)}"}), 500
        
@bp.route('/api/draw', methods=['POST'])
def draw() :
    grade = request.args.get('grade')

    # 학년 모든 멤버 가져오기
    all_members = ClassMember.query.filter_by(grade=grade).all()

    # <조건>
    # 1. 그룹에는 무조건 여자가 1명은 들어가야 한다.
    # 2. len(unchecked_members)가 4 보다 작으면 나머지 인원을 이번주에 넣고 
    #    check 리셋 후 남은 멤버 수 만큼 랜덤으로 낑겨 넣는다.
    # 3. 저번 주에 한 사람들은 이번 주 명단에서 제외 한다.

    # 안 한 사람 리스트 (뽑아야 할 사람 리스트)
    unchecked_list = [member for member in all_members if member.check == False]

    # 저번주에 한 사람 리스트
    last_week_list = [member for member in all_members if member.this_week]

    # 이번주에 할 사람 리스트
    this_week_list = []

    # 뽑아야 할 사람 수 (기본 4명)
    num_to_draw = 4

    # 뽑혀야 하는 인원 리스트 
    deserve_list = []

    # 안 한 사람이 4명 미만이면
    if len(unchecked_list) < 4 :
        # 이번주 명단에 일단 다 넣기
        this_week_list.extend(unchecked_list)

        # 뽑아야 할 인원 수 계산
        num_to_draw -= len(unchecked_list)

        # 모든 인원 전부 check 변경
        for member in all_members :
            member.check = False

        # 저번주에 했던 사람은 제외
        for member in last_week_list :
            member.check = True

        # 이번 주에 들어간 사람, 저번 주에 했던 사람 제외하고 다 뽑힐 가능성이 있는 사람으로 취급
        deserve_list = [member for member in all_members if member.check == False and member not in this_week_list]

    # 일반 경우
    else :
        # 안 한 사람 리스트가 곧 뽑힐 사람
        deserve_list = unchecked_list

    # 이번주 당번에 여자가 있는지 확인
    is_in_woman = any(member.gender == "여" for member in this_week_list)

    # 뽑힐 사람 중 여자와 남자 구분
    deserve_woman_list = [member for member in deserve_list if member.gender == "여"]
    deserve_man_list = [member for member in deserve_list if member.gender == "남"]

    # 최종 뽑을 사람 리스트
    final_list = []

    # 만약 이번주 당번에 여자가 없다면
    if not is_in_woman :
        # 뽑을 수 있는 여자가 있다면
        if deserve_woman_list :
            # 여자 리스트 중 한 명을 뽑고 당번에 넣기
            this_week_woman = random.choice(deserve_woman_list)
            this_week_list.append(this_week_woman)
            num_to_draw -= 1

            # 마지막으로 뽑힐 사람은 남자 뿐
            final_list = deserve_man_list

        # 뽑을 수 있는 여자가 없다면
        else :
            # 어쩔 수 없이 남자만 뽑음
            final_list = deserve_man_list
    # 이번 주 당번에 이미 여자가 있다면
    else :
        # 무조건 남자만 뽑음
        final_list = deserve_man_list

    # (혹시 모를 예외 처리) 만약 남은 사람이 뽑을 사람보다 크면 뽑을 사람을 남은 사람만큼 줄이기
    if len(final_list) < num_to_draw :
        num_to_draw = len(final_list)

    # 아직 뽑을 사람이 남았다면
    if num_to_draw > 0 :
        # 남은 인원 만큼 마무리 뽑기
        final_member = random.sample(final_list, num_to_draw)
        this_week_list.extend(final_member)
    
    try :
        for member in last_week_list :
            member.this_week = False
        
        for member in this_week_list :
            member.this_week = True
            member.check = True

        db.session.commit()

        new_member_list = sorted([member.name for member in this_week_list])

        return jsonify({'success' : True, 'message' : "청소 당번을 새로 뽑았습니다.", 'new_members' : new_member_list})
    
    except Exception as e :
        db.session.rollback()
        return jsonify({'success' : False, 'message' : f'DB 저장 오류 {str(e)}'}), 500