from flask import Blueprint, render_template, jsonify, Response, stream_with_context, request, current_app
from .. import db, redis_client
from ..models import SensorDatas, Locations, MonthDatas, Recommend
from sqlalchemy import desc, or_
import pytz
from datetime import datetime
import json
from ..__init__ import calculate_monthly_average

bp = Blueprint('temp', __name__, url_prefix='/temp')

@bp.route('/')
def show() :
    # 목적이 정해지지 않은(추가 되지 않은 교실을 제외한 교실 목록 가져오기)
    location_list = Locations.query.order_by(Locations.location).all()
    
    unassigned_locations = Locations.query.filter(or_(Locations.purpose == None, Locations.purpose == '')).order_by(Locations.location).all()

    if not location_list :
        return render_template('404.html')

    default_location = location_list[0].location
    selected_location = request.args.get('location', default=default_location, type=str)
    
    # 이상한 호실로 입력되면 404호 표시
    selected_location_obj = None

    for loc in location_list :
        if loc.location == selected_location :
            selected_location_obj = loc
            break

    if not selected_location_obj :
        selected_location_obj = location_list[0]
        selected_location = selected_location_obj.location

    purpose = selected_location_obj.purpose or "목적 미지정"

    # 가장 최신 데이터 띄워놓기
    latest_reading = SensorDatas.query.filter_by(location=selected_location).order_by(desc(SensorDatas.record_date)).first()
    temp = latest_reading.temp
    humi = latest_reading.humi
    
    # 한국 기준 시간 받아와서 추천 온도 띄우기
    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    current_date_kst = now_kst.strftime("%m월 %d일")
    current_month = now_kst.month

    recommend_temp = Recommend.query.filter_by(month=current_month).first().recommend_temp

    # 월별 데이터 받아오기
    month_data_list = []
    if selected_location :
        month_data_list = MonthDatas.query.filter_by(location=selected_location).order_by(MonthDatas.month).all()

    month_data_dict = {data.month : data for data in month_data_list}

    return render_template(
        'temp_page.html', 
        location_list=location_list, 
        selected_location=selected_location, 
        unassigned_locations=unassigned_locations,
        purpose=purpose,
        temp=temp,
        humi=humi,
        month_data_dict=month_data_dict,
        current_date=current_date_kst,
        recommend_temp=recommend_temp
    )

@bp.route('/month-data')
def month_data() :
    selected_location = request.args.get('location', default='404호', type=str)

    month_data_list = MonthDatas.query.filter_by(location=selected_location).order_by(MonthDatas.month).all()
    month_data_dict = {data.month : data for data in month_data_list}

    return render_template('temp_page_month_data_box.html', month_data_dict=month_data_dict)

@bp.route('/stream')
def stream() :
    client_location = request.args.get('location', '404호', type=str)
    last_yielded_date = None

    pubsub = redis_client.pubsub()
    # 센서가 업데이트 되면 메세지를 보낼 'sensor_updates' 채널을 구독하여 메세지 오는지 항시 관찰
    pubsub.subscribe('sensor_updates')

    def event_stream() :
        nonlocal last_yielded_date

        app = current_app._get_current_object()

        for message in pubsub.listen() :
            print(f"Redis 메세지 수신 : {message}")

            if message['type'] != 'message' :
                continue
            
            channel = message['channel']

            if channel == 'sensor_updates' :
                kst = pytz.timezone('Asia/Seoul')
                now_kst = datetime.now(kst)
                current_date = now_kst.date()

                # 하루가 바뀌면 날짜 초기화 및 달이 바뀌면 추천 온도 초기화
                if last_yielded_date != current_date :
                    current_date_str = now_kst.strftime("%m월 %d일")
                    with app.app_context() :
                        recommend_temp = Recommend.query.filter_by(month=now_kst.month).first().recommend_temp

                    # 파이썬 데이터를 JSON 문자열로 변환하는 함수.
                    # ensure_ascii = False 를 통해 한글이 깨지지 않도록 함
                    date_update_json = json.dumps({
                        "date_str" : current_date_str,
                        "recommend_temp" : recommend_temp
                    }, ensure_ascii=False)

                    # yield = 값을 반환 하면서도 함수를 멈추지 않고 유지하는 키워드
                    # 값의 뒤에 \n\n를 붙이는 이유는 이벤트가 하나 끝났다는 신호임
                    yield f"event: date_update\ndata: {date_update_json}\n\n"
                    last_yielded_date = current_date
                
                try :
                    message_data = message['data']
                    data = json.loads(message_data)
                    updated_location = data.get('location')

                    if updated_location == client_location :
                        temp = data.get('temp')
                        humi = data.get('humi')

                        if temp is not None and humi is not None :
                            data_json = json.dumps({"temp" : float(temp), "humi" : float(humi)}, ensure_ascii=False)
                            sse_message = f"data: {data_json}\n\n"
                            yield sse_message
                
                except Exception as e :
                    print(f"SSE 센서 데이터 처리 오류 : {e}, 받은 데이터: {message['data']}")
            
            elif channel == 'month_update' :
                print("월별 데이터 갱신 신호(SSE) 전송")

                yield f"event: month_data_update\ndata: refresh\n\n"
    
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')

@bp.route('/api/location/<string:location_name>', methods=['GET', 'PUT', 'DELETE'])
def manage_location(location_name) :
    location = Locations.query.filter_by(location=location_name).first()

    if not location :
        return jsonify({"success" : False, "message": "해당 교실을 찾을 수 없습니다." }), 404
    
    if request.method == 'GET' :
        return jsonify({
            "success" : True,
            "location" : location.location,
            "purpose" : location.purpose or ""    
        })
    
    if request.method == 'PUT' :
        data = request.json
        new_purpose = data.get('purpose')

        if not new_purpose or len(new_purpose.strip()) == 0 :
            return jsonify({"success" : False, "message": "교실 목적을 입력하세요."}), 400
        
        try :
            location.purpose = new_purpose
            db.session.commit()
            return jsonify({"success": True, "message": f"'{location_name}' 정보가 수정되었습니다."})
        except Exception as e :
            db.session.rollback()
            return jsonify({"success": False, "message": f"수정 중 오류 발생: {str(e)}"}), 500
        
    if request.method == 'DELETE' :
        try :
            db.session.delete(location)
            db.session.commit()
            return jsonify({"success": True, "message": f"'{location_name}' 교실이 삭제되었습니다."})
        
        except Exception as e :
            db.session.rollback()
            return jsonify({"success": False, "message": f"삭제 중 오류 발생: {str(e)}"}), 500
        
@bp.route('/test-month-job')
def test_momth_job() :
    
    try :
        calculate_monthly_average()

        return "월 평균 계산 작업 수동 실행 완료."
    except Exception as e :
        return f"작업 실행 중 오류 발생 : {str(e)}"