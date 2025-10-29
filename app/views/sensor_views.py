from flask import Blueprint, request, jsonify
from ..models import Locations, SensorDatas
from .. import db, redis_client
from sqlalchemy.exc import SQLAlchemyError
from app import csrf
import json

bp = Blueprint('sensor', __name__, url_prefix='/sensor')

# 센서로부터 들어오는 데이터 처리 API
@bp.route('/api/sensor-data', methods=('POST',))
@csrf.exempt
def sensor_data() :
    try :
        # 센서로부터 JSON 형식의 데이터 수집하기
        sensor_data = request.json
        if not sensor_data :
            raise ValueError("JSON 데이터가 없습니다.")
        
        location_name = sensor_data.get('location')
        temp = sensor_data.get('temp')
        humi = sensor_data.get('humi')

        # 데이터 누락 확인
        if not location_name:
            raise ValueError("필수 데이터 'location'이 누락되었습니다.")
        
        if temp is None :
            raise ValueError("필수 데이터 'temp'이 누락되었습니다.")
        
        if humi is None :
            raise ValueError("필수 데이터 'humi'이 누락되었습니다.")
        
        # 데이터 타입 확인
        try : 
            temp = float(temp)
            humi = float(humi)
        except (ValueError, TypeError) :
            raise ValueError("온도(temp) 또는 습도(humi)가 올바른 타입이 아닙니다.")
        
        # 위치 정보 존재 여부 확인
        location_obj = Locations.query.get(location_name)

        # 만약 Locations 테이블에 새로 들어온 location이 없다면 추가
        if not location_obj :
            new_location = Locations(location=location_name, purpose=None)
            db.session.add(new_location)
        
        new_data = SensorDatas(location=location_name, temp=temp, humi=humi)
        db.session.add(new_data)
        db.session.commit()

        data_to_send = {
            "location" : new_data.location,
            "temp" : float(new_data.temp),
            "humi" : float(new_data.humi)
        }

        message_json = json.dumps(data_to_send, ensure_ascii=False)
        # 'sensor_updates' 채널에 'new_data_arrived' 메세지 전송
        redis_client.publish('sensor_updates', message_json)

        return jsonify({"message": "데이터 저장 성공!"}), 201
    
    # 데이터 형식이 잘못되었을 경우
    except ValueError as e :
        # DB 변경사항 되돌리기
        db.session.rollback()
        print(f"데이터 입력 오류 : {e}")

        # '400 Bad Request' : 클라이언트가 잘못된 요청을 보냄
        return jsonify({"error" : str(e)}), 400
    
    except SQLAlchemyError as e :
        db.session.rollback()
        print(f"데이터베이스 오류 : {e}")
        
        # '500 Internal Server Error' : 서버 내부 문제 발생
        return jsonify({"error" : "데이터베이스 저장 중 오류가 발생했습니다."}), 500
    
    except Exception as e :
        db.session.rollback()
        print(f"예상치 못한 오류 : {e}")

        return jsonify({"error" : "서버 내부 오류가 발생했습니다."}), 500