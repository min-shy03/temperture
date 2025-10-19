from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

import config

# db, migrate 객체 생성
db = SQLAlchemy()
migrate = Migrate()

# 객체 초기화 함수
def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # ORM (object relational mapping) = 데이터베이스 테이블을 파이썬 클래스로 만들어 관리하는 기술
    db.init_app(app)
    migrate.init_app(app, db)
    from . import models
    
    from .views import main_views, api_views
    app.register_blueprint(main_views.bp)
    app.register_blueprint(api_views.bp)
    
    return app