from flask import Blueprint, render_template, jsonify, Response, stream_with_context, request
from .. import db, redis_client
from ..models import SensorDatas, Locations, MonthDatas, Recommend
from sqlalchemy import desc
import pytz
from datetime import datetime
import json

bp = Blueprint('temp', __name__, url_prefix='/temp')

@bp.route('/')
def show() :
    # 목적이 정해지지 않은(추가 되지 않은 교실을 제외한 교실 목록 가져오기)
    location_list = Locations.query.filter(Locations.purpose != None).order_by(Locations.location).all()
    
    # 기본 값은 404호 고정
    default_location = '404호'
    selected_location = request.args.get('location', default='404호', type=str)
    
    # 이상한 호실로 입력되면 404호 표시
    if not any(loc.location == selected_location for loc in location_list) :
        selected_location = default_location

    for loc in location_list :
        if loc.location == selected_location :
            purpose = loc.purpose

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
        purpose=purpose,
        temp=temp,
        humi=humi,
        month_data_dict=month_data_dict,
        current_date=current_date_kst,
        recommend_temp=recommend_temp
    )


@bp.route('/stream')
def stream() :
    last_yielded_date = None

    pubsub = redis_client.pubsub()
    # 센서가 업데이트 되면 메세지를 보낼 'sensor_updates' 채널을 구독하여 메세지 오는지 항시 관찰
    pubsub.subscribe('sensor_updates')

    def event_stream() :
        nonlocal last_yielded_date

        for message in pubsub.listen() :
            print(f"Redis 메세지 수신 : {message}")

            if message['type'] == 'message' :
                kst = pytz.timezone('Asia/Seoul')
                now_kst = datetime.now(kst)
                current_date = now_kst.date()

                # 하루가 바뀌면 날짜 초기화 및 달이 바뀌면 추천 온도 초기화
                if last_yielded_date != current_date :
                    current_date_str = now_kst.strftime("%m월 %d일")
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

                latest_data = SensorDatas.query.order_by(desc(SensorDatas.record_date)).first()
                temp = latest_data.temp
                humi = latest_data.humi

                data_json = json.dumps({"temp" : float(temp), "humi" : float(humi)}, ensure_ascii=False)
                sse_message = f"data: {data_json}\n\n"
                yield sse_message
    
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')