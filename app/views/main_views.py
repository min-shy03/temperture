from flask import Blueprint, render_template, redirect, url_for, abort
from app.models import Locations, SensorDatas, MonthDatas, Recommend
from sqlalchemy import desc
import datetime

bp = Blueprint('main', __name__, url_prefix='/')

# 기본 서버 주소로 요청 시 교실 별 url로 리다이렉트하기
@bp.route('/')
def main():
    return render_template('main_page.html')

