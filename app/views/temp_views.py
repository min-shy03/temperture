from flask import Blueprint, render_template, jsonify, Response, stream_with_context, request
from .. import db, redis_client
from ..models import SensorDatas, Locations, MonthDatas
from sqlalchemy import desc

bp = Blueprint('temp', __name__, url_prefix='/temp')

@bp.route('/')
def show() :
    location_list = Locations.query.filter(Locations.purpose != None).order_by(Locations.location).all()

    default_location = '404호'
    selected_location = request.args.get('location', default='404호', type=str)
    
    if not any(loc.location == selected_location for loc in location_list) :
        selected_location = default_location

    purpose = Locations.query.filter(Locations.location==selected_location).first().purpose

    month_data_list = []

    if selected_location :
        month_data_list = MonthDatas.query.filter_by(location=selected_location).order_by(MonthDatas.month).all()

    return render_template(
        'temp_page.html', 
        location_list=location_list, 
        selected_location=selected_location, 
        purpose=purpose,
        month_data=month_data_list
    )


@bp.route('/stream')
def stream() :
    pubsub = redis_client.pubsub()
    # 센서가 업데이트 되면 메세지를 보낼 'sensor_updates' 채널을 구독하여 메세지 오는지 항시 관찰
    pubsub.subscribe('sensor_updates')

    def event_stream() :
        for message in pubsub.listen() :
            print(f"Redis 메세지 수신 : {message}")

            if message['type'] == 'message' :
                latest_data = SensorDatas.query.order_by(desc(SensorDatas.record_date)).first()
                temp = latest_data.temp
                humi = latest_data.humi

                data_json = jsonify({'temp' : temp, 'humi' : humi}).get_data(as_text=True)
                sse_message = f"data: {data_json}\n\n"
                yield sse_message
    
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')