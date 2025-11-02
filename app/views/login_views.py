from flask import Blueprint, url_for, render_template, request, session, flash, redirect, g
from app.models import Admins
from app.forms import LoginForm
import bcrypt

bp = Blueprint('login', __name__, url_prefix='/login')

@bp.route('/', methods=['GET', 'POST'])
def login() :
    # GET으로 요청이 오면 html 파일에 입력받은 LoginForm을 제출하고
    # POST로 온다면 html 파일에서 입력받은 폼을 LoginForm에 대입
    form = LoginForm()

    # validate_on_submit()의 기능
    # 1. 폼이 제출되었는지 확인
    # 2. 데이터가 유효한지 확인 ex) DataRequired(필수 입력) 같은 경우
    # 3. CSRF 토큰이 올바른가??
    if request.method == 'POST' and form.validate_on_submit() :
        error = None 

        # 쿼리문 뜻 : Admins 테이블에서 std_num이 form의 std_num과 일치하는 객체를 하나만 가져와라.
        admin = Admins.query.filter_by(std_num=form.std_num.data).first()

        if not admin :
            error = "존재하지 않는 학번입니다."
        
        # Admins 테이블에 관리자 입력 시 bcrypt로 password 해시 처리 후 데이터베이스에 저장.
        # 그러므로 평범한 문자열로 들어온 form.password와 비교를 위해 checkpw 함수 사용
        elif not bcrypt.checkpw(form.password.data.encode('utf-8'), admin.password.encode('utf-8')) :
            error = "비밀번호가 올바르지 않습니다."
        
        if error is None :
            # 세션 : 일종의 학생증
            session.clear()
            # 학생증에 관리자 아이디 등록
            session['admin_id'] = admin.id

            # 현재 로그인 페이지에서 next값을 읽어옴
            next_url = request.form.get('next')

            # next_url 값이 없거나, next_url 값이 /로 시작하지 않으면 메인 페이지로 이동
            if not next_url or not next_url.startswith('/') :
                next_url = url_for('main.main')

            return redirect(next_url)
        
        flash(error)

    return render_template('login_page.html', form=form)

@bp.before_app_request
def load_logged_in_admin() :
    # 학생증에 관리자 아이디가 있는지 확인
    admin_id = session.get('admin_id')

    # 관리자 아이디가 없다면 일반 유저
    if admin_id is None :
        g.admin = None
    # 관리자 아이디가 있다면 db에서 진짜 관리자 정보를 꺼내
    # g(세션과는 다른 임시 정보 저장소)에 저장
    else :
        g.admin = Admins.query.get(admin_id)

@bp.route('/logout/')
def logout() :
    # 학생증을 다 사용했으니 버림
    session.clear()
    next_url = request.args.get('next')

    if not next_url or not next_url.startswith('/') :
        next_url = url_for('main.main')
    return redirect(next_url)