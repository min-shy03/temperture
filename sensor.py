# 라즈베리파이 센서 데이터 전송 코드 (가짜 코드 흉내만 내는 목적)
import time
import random
import requests

SERVER_URL = "http://210.101.236.204:5000/api/sensor-data"

# 5번 실행
while True :
    json_datas = {
        "location" : "404호",
        "temp" : round(21 + random.random(),1),
        "humi" : round(61 + random.random(),1)
    }

    res = requests.post(SERVER_URL, json=json_datas)

    print("status code :", res.status_code)

    time.sleep(60)