from flask import Blueprint, url_for, render_template, request, session, flash, redirect, g
from app.models import Admins
from app.forms import LoginForm
import bcrypt

bp = Blueprint('login', __name__, url_prefix='/login')

@bp.route('/', methods=['GET', 'POST'])
def login() :
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit() :
        error = None
        admin = Admins.query.filter_by(std_num=form.std_num.data).first()

        if not admin :
            error = "존재하지 않는 학번입니다."
        
        elif not bcrypt.checkpw(form.password.data.encode('utf-8'), admin.password.encode('utf-8')) :
            error = "비밀번호가 올바르지 않습니다."
        
        if error is None :
            session.clear()
            session['admin_id'] = admin.id

            next_url = request.form.get('next')

            if not next_url or not next_url.startswith('/') :
                next_url = url_for('main.main')

            return redirect(next_url)
        
        flash(error)

    return render_template('login_page.html', form=form)

@bp.before_app_request
def load_logged_in_admin() :
    admin_id = session.get('admin_id')
    if admin_id is None :
        g.admin = None
    else :
        g.admin = Admins.query.get(admin_id)

@bp.route('/logout/')
def logout() :
    session.clear()
    next_url = request.args.get('next')

    if not next_url or not next_url.startswith('/') :
        next_url = url_for('main.main')
    return redirect(next_url)