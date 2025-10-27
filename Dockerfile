# 파이썬 3.11 슬림 버전 이미지 사용 (라이브러리와 호환 확인)
FROM python:3.11-slim

# 컨테이너 내 작업 폴더 설정
WORKDIR /app

# 라이브러리 목록 파일 먼저 복사
COPY requirements.txt requirements.txt

# 파이썬 라이브러리 설치 (캐시 사용 안 함, pip 업그레이드)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 나머지 앱 코드 전체 복사
COPY . .

# Flask가 사용할 포트 노출
EXPOSE 5000

# Flask 앱 실행 명령어 (외부 접속 허용)
# FLASK_APP 환경 변수는 docker-compose에서 설정
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]