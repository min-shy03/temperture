from app import db
from datetime import datetime, timezone

# 센서에서 보낸 데이터를 저장할 테이블
class SensorDatas(db.Model):
    # 각 데이터 고유 번호
    id = db.Column(db.Integer, primary_key=True)
    # 센서 위치 정보
    # Locations 테이블의 location을 연결시킨다. 
    location = db.Column(db.String(200), db.ForeignKey('locations.location', ondelete='CASCADE'),nullable=False)
    # 온도
    temp = db.Column(db.Numeric(4,1), nullable=False)
    # 습도
    humi = db.Column(db.Numeric(4,1), nullable=False)
    # 측정 시간
    record_date = db.Column(db.DateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))

# 센서 위치 정보 테이블
class Locations(db.Model) :
    # 센서의 위치 정보
    location = db.Column(db.String(200), primary_key=True, nullable=False)
    # 센서의 실시간 데이터를 역참조할 변수
    readings = db.relationship('SensorDatas', backref=db.backref('location_info'))
    # 센서의 월 별 평균을 역참조할 변수
    month_readings = db.relationship('MonthDatas', backref=db.backref('location_month_avg'))
    # 센서 목적 
    # 교실 추가 전까진 Null인 채로 있어야함으로 Null 허용
    purpose = db.Column(db.String(200), nullable=True)

# 월별 평균 온도 테이블
class MonthDatas(db.Model) :
    # 월
    month = db.Column(db.Integer, primary_key=True, nullable=False)
    # 위치 정보
    # Locations 테이블의 location 연결
    location = db.Column(db.String(200), db.ForeignKey('locations.location', ondelete='CASCADE'),primary_key=True, nullable=False)
    # 평균 온도
    avg_temp = db.Column(db.Numeric(4,1), nullable=False)
    # 평균 습도
    avg_humi = db.Column(db.Numeric(4,1), nullable=False)

# 추천 온도 테이블
class Recommend(db.Model) :
    # 월
    month = db.Column(db.Integer, primary_key=True, nullable=False)
    # 추천 온도
    recommend_temp = db.Column(db.String(200), nullable=False)

# 관리자 정보 테이블
class Admins(db.Model) :
    id = db.Column(db.Integer, primary_key=True)
    # 관리자 이름
    name = db.Column(db.String(200), nullable=False)
    # 관리자 학번
    std_num = db.Column(db.String(200), unique=True, nullable=False)
    # 관리자 비밀번호
    password = db.Column(db.String(200), nullable=False)

# 강의 정보 테이블
class Lectures(db.Model) :
    id = db.Column(db.Integer, primary_key=True)
    # 학년
    grade = db.Column(db.Integer, nullable=False)
    # 학기
    semester = db.Column(db.Integer, nullable=False)
    # 강의명
    lecture_name = db.Column(db.String(200), nullable=False)
    # 교수 정보
    professor = db.Column(db.String(200), nullable=False)
    # 요일
    day = db.Column(db.String(200), nullable=False)
    # 교시
    period = db.Column(db.Integer, nullable=False)
    # 강의실
    classroom = db.Column(db.String(200), nullable=False)
    # 강의 색상
    color = db.Column(db.String(7), nullable=True, default='#FFFFFF')