import sqlite3
import os
from app import create_app, db
from app.models import Locations, SensorDatas, MonthDatas, Recommend, Admins, Lectures, ClassMember

SQLITE_DB = 'old_data.db'

def migrate():
    app = create_app()
    with app.app_context():
        print("--- [시작] 데이터 이관 작업 시작 ---")
        if not os.path.exists(SQLITE_DB):
            print(f"오류: {SQLITE_DB} 파일을 찾을 수 없습니다.")
            return

        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        def transfer(table_name, ModelClass):
            print(f"[{table_name}] 이동 중...", end=" ")
            try:
                cur.execute(f"SELECT * FROM {table_name}")
                rows = cur.fetchall()
                for row in rows:
                    data = dict(row)
                    instance = ModelClass(**data)
                    db.session.add(instance)
                db.session.commit()
                print(f"-> 완료! ({len(rows)}개)")
            except Exception as e:
                db.session.rollback()
                print(f"-> 실패: {e}")

        transfer('locations', Locations)
        transfer('admins', Admins)
        transfer('recommend', Recommend)
        transfer('lectures', Lectures)
        transfer('class_member', ClassMember)
        transfer('month_datas', MonthDatas)
        transfer('sensor_datas', SensorDatas)

        conn.close()
        print("--- [끝] 모든 데이터가 MySQL로 성공적으로 옮겨졌습니다! ---")

if __name__ == '__main__':
    migrate()
