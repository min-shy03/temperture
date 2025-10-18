import os

BASE_DIR = os.path.dirname(__file__)

# 데이터베이스 접속 주소
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(BASE_DIR, 'temp.db'))
# SQLAlchemy 이벤트 처리 옵션
SQLALCHEMY_TRACK_MODIFICATIONS = False