from flask import Flask
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, extract
import config
import redis
# from .models import SensorDatas, MonthDatas
# from . import db

# db, migrate 객체 생성
db = SQLAlchemy()
migrate = Migrate()

csrf = CSRFProtect()
# 우체국 같은 느낌 메세지를 주고받는 용도
redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
scheduler = APScheduler()

# def calculate_monthly_average() :
#     app = create_app()
#     with app.app_context() :


# 객체 초기화 함수
def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # ORM (object relational mapping) = 데이터베이스 테이블을 파이썬 클래스로 만들어 관리하는 기술
    db.init_app(app)
    migrate.init_app(app, db)
    from . import models
    
    from .views import main_views, sensor_views, login_views, time_table_views, introduce_views, temp_views
    app.register_blueprint(main_views.bp)
    app.register_blueprint(sensor_views.bp)
    app.register_blueprint(login_views.bp)
    app.register_blueprint(time_table_views.bp)
    app.register_blueprint(temp_views.bp)
    app.register_blueprint(introduce_views.bp)

    csrf.init_app(app)

    return app