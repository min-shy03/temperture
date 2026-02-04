import bcrypt
from app import create_app, db
from app.models import Admins

def create_admin():
    app = create_app()
    with app.app_context():
        print("\n--- [관리자 계정 추가] ---")
        
        # 1. 정보 입력받기
        name = input("이름 입력: ").strip()
        std_num = input("학번 입력 (로그인 ID): ").strip()
        password = input("비밀번호 입력: ").strip()

        if not name or not std_num or not password:
            print("❌ 오류: 모든 정보를 입력해야 합니다.")
            return

        # 2. 중복 확인
        if Admins.query.filter_by(std_num=std_num).first():
            print(f"❌ 오류: 이미 존재하는 학번({std_num})입니다.")
            return

        # 3. 비밀번호 암호화 및 저장
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_admin = Admins(name=name, std_num=std_num, password=hashed_pw)

        try:
            db.session.add(new_admin)
            db.session.commit()
            print(f"✅ 성공! '{name}' 관리자가 추가되었습니다.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ DB 저장 실패: {e}")

if __name__ == "__main__":
    create_admin()
