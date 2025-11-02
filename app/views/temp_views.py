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
    # 센서가 존재하는 모든 교실 리스트 가져오기
    location_list = Locations.query.order_by(Locations.location).all()

    # or_ 을 사용해 filter() 함수에 or 조건 사용함
    # Locations 테이블에서 purpose가 none이거나 빈 칸인 것들을 전부 가져오기
    unassigned_locations = Locations.query.filter(or_(Locations.purpose == None, Locations.purpose == '')).order_by(Locations.location).all()

    # 교실이 하나도 없으면 404 페이지로 이동
    if not location_list :
        return render_template('404.html')
    
    default_location = location_list[0].location

    # url에서 location값을 가져오기, 없으면 default는 location_list의 첫번째 값, 타입은 str
    selected_location = request.args.get('location', default=default_location, type=str)
    
    selected_location_obj = None
    # 교실 리스트에서 현재 선택된 교실과 같은 객체 탐색 후 저장
    for loc in location_list :
        if loc.location == selected_location :
            selected_location_obj = loc
            break

    # 만약 현재 선택된 교실과 같은 교실이 없으면 default(location_list의 첫번짜 값) 값으로 지정
    if not selected_location_obj :
        selected_location_obj = location_list[0]
        selected_location = selected_location_obj.location

    # 현재 선택된 교실이 purpose값이 존재하면 띄우고, 없으면 "목적 미지정 출력"
    purpose = selected_location_obj.purpose or "목적 미지정"

    # SensorDatas 테이블에서 현재 선택된 테이블의 가장 최신의 데이터를 가져 온 후 온도와 습도 저장
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
    # 현재 url에서 location값 받아오기
    selected_location = request.args.get('location', type=str)

    # location 값이 없으면 db에서 가져온 교실 리스트중 가장 처음 location 값으로 설정
    if not selected_location :
        selected_location = Locations.query.order_by(Locations.location).first().location

    # selected_location 값으로 MonthDatas 테이블에서 해당 교실의 1월부터 12월까지 데이터 전부 받아오기
    month_data_list = MonthDatas.query.filter_by(location=selected_location).order_by(MonthDatas.month).all()

    # 박스 생성을 위해 딕셔너리로 월 별값 저장
    month_data_dict = {data.month : data for data in month_data_list}

    # 박스 생성 전용 html 파일로 딕셔너리 값 보내기
    return render_template('temp_page_month_data_box.html', month_data_dict=month_data_dict)

@bp.route('/stream')
def stream() :
    client_location = request.args.get('location', type=str)

    if not client_location :
        client_location = Locations.query.order_by(Locations.location).first().location

    last_yielded_date = None

    pubsub = redis_client.pubsub()
    # 센서가 업데이트 되면 메세지를 보낼 'sensor_updates' 채널을 구독하여 메세지 오는지 항시 관찰
    pubsub.subscribe('sensor_updates')

    def event_stream() :
        nonlocal last_yielded_date

        app = current_app._get_current_object()

        # listen()이 호출되면 센서에서 데이터가 올 때까지 일시 정지 후 메세지가 오면 수신
        # for문에 수신한 메세지 객체 넘겨줌
        # 이 for문은 무한 반복하며 계속 신호를 받는다.
        for message in pubsub.listen() :
            print(f"Redis 메세지 수신 : {message}")

            # 센서에서 보낸 데이터는
            # 일종의 택배 상자에 담겨서 이런식으로 온다!
            # message = {
            #     # 1. 운송장 정보 (Metadata)
            #     'type': 'message',
            #     'channel': 'sensor_updates', # <--- 'sensor_updates' 채널에서 왔음!
            #     'pattern': None,

            #     # 2. 실제 내용물 (Payload)
            #     'data': '{"location": "404호", "temp": 25.5, "humi": 60.0}' # <--- 센서가 보낸 JSON 문자열
            # } 
            
            # 그래서 이런식으로 제대로 왔는지 확인이 가능한 것!
            if message['type'] != 'message' :
                continue
            
            # 어떤 채널에서 왔는지도 구분이 가능하다.
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
                    # JSON 문자열을 파이션 딕셔너리로 번역해주는 함수
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
    
    # stream_with_context = 플라스크가 현재 요청이 어떤 요청이였는지 까먹지 않게 해주는 함수
    # mimetype = 이 요청이 어떤 데이터인지 알려주는 라벨
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')

@bp.route('/api/location/<string:location_name>', methods=['GET', 'PUT', 'DELETE'])
def manage_location(location_name) :
    location = Locations.query.filter_by(location=location_name).first()

    if not location :
        # 파이션 딕셔너리를 입력받아 JSON 문자열로 치환 후 HTTP 응답 헤더를 붙여 포장 한 뒤 이 응답이 JSON 데이터임을 알려줌.
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

# 수동 월별 평균 계산 테스트용 api
@bp.route('/test-month-job')
def test_momth_job() :
    
    try :
        calculate_monthly_average()

        return "월 평균 계산 작업 수동 실행 완료."
    except Exception as e :
        return f"작업 실행 중 오류 발생 : {str(e)}"