import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 데이터베이스 접속 주소
# 환경 변수 DATABASE_URL이 없으면 기본 sqlite 사용
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///{}'.format(os.path.join(BASE_DIR, 'temp.db'))

SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get('SECRET_KEY') or "dev-key-1234" # 실제 배포 시엔 .env에 설정
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))