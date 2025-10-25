from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm) :
    std_num = StringField('학번', validators=[DataRequired("학번을 입력하세요.")])
    password = PasswordField('비밀번호', validators=[DataRequired("비밀번호를 입력하세요.")])