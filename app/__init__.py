from flask import Flask
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func, extract
import config
import redis
from datetime import datetime, timedelta
import pytz
import os

# db, migrate 객체 생성
db = SQLAlchemy()
migrate = Migrate()

csrf = CSRFProtect()
# 우체국 같은 느낌 메세지를 주고받는 용도
redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
scheduler = APScheduler()

def calculate_monthly_average() :
    app = create_app()
    from .models import SensorDatas, MonthDatas, Locations
    with app.app_context() :
        try :
            kst = pytz.timezone('Asia/Seoul')
            today_kst = datetime.now(kst).date()

            first_day_of_current_month = today_kst.replace(day=1)
            last_day_of_previous_month = first_day_of_current_month - timedelta(seconds=1)

            target_year = last_day_of_previous_month.year
            target_month = last_day_of_previous_month.month

            monthly_averages = db.session.query(
                SensorDatas.location, 
                func.avg(SensorDatas.temp).label('avg_temp'),
                func.avg(SensorDatas.humi).label('avg_humi') 
            ).filter(
                extract('year', SensorDatas.record_date) == target_year,
                extract('month', SensorDatas.record_date) == target_month
            ).group_by(
                SensorDatas.location
            ).all()

            if not monthly_averages :
                print(f"{target_year}년 {target_month} 월 데이터가 없어 스킵합니다.")
                return
            
            for avg_data in monthly_averages :
                data_to_upsert = MonthDatas(
                    month=target_month,
                    location=avg_data.location,
                    avg_temp=avg_data.avg_temp,
                    avg_humi=avg_data.avg_humi
                )
                db.session.merge(data_to_upsert)
            
            db.session.commit()
            print(f"[{datetime.now()}] {target_month}월 평균 덮어쓰기 완료")

            SensorDatas.query.filter(
                extract('year', SensorDatas.record_date) == target_year,
                extract('month', SensorDatas.record_date) == target_month,
            ).delete(synchronize_session=False)
            db.session.commit()
            print(f"[{datetime.now()}] {target_year}년 {target_month}월 SensorDatas 삭제 완료")

            redis_client.publish('month_update', 'data_updated')
            print(f"[{datetime.now()}] Redis 'month_updates' 채널에 신호 전송 완료")

        except Exception as e :
            db.session.rollback()
            print(f"월별 평균 계산 중 오류 발생: {e}")
        
        finally :
            print("ㅡㅡㅡ 월별 평균 계산 종료 ㅡㅡㅡ")

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

    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true' :
        scheduler.init_app(app)
        scheduler.start()

        if not scheduler.get_job('Monthly Average Task'):
            scheduler.add_job(
                id='Monthly Average Task',
                func=calculate_monthly_average,
                trigger='cron',
                month='*',
                day=1,
                hour=2,
                minute=0
            )
    return app