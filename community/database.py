# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 127.0.0.1 계정 정보 (비밀번호는 꼭 본인 걸로!)
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://server:server123@127.0.0.1:3306/community_db"

# DB 엔진 생성: DB와의 통로를 뚫는 역할
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,         # 500만 건 대응을 위해 연결 통로를 10개 확보
    max_overflow=20       # 사람 몰릴 때 대비해 추가 통로 20개 확보
)

# 세션 생성기: 실제 쿼리를 보낼 때마다 하나씩 꺼내 쓰는 도구
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency Injection: API 함수가 실행될 때 DB 연결을 빌려주는 역할
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()