from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm) :
    std_num = StringField('학번', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])