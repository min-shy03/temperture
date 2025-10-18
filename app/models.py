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

# 센서 위치 정보
class Locations(db.Model) :
    location = db.Column(db.String(200), primary_key=True, nullable=False)
    readings = db.relationship('SensorDatas', backref=db.backref('location_info'))
    # 교실 추가 전까진 Null인 채로 있어야함으로 Null 허용
    purpose = db.Column(db.String(200), nullable=True)

