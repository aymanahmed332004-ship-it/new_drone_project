from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# رابط قاعدة البيانات (يتم إنشاء الملف في مجلد المشروع)
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# إعداد المحرك (Engine) - مع تفعيل خاصية تعدد الخيوط لـ SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# إعداد الجلسة (Session) - لفتح وإغلاق التعامل مع الداتابيز
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# تعريف القاعدة الأساسية للجداول
Base = declarative_base()

# دالة لجلب الجلسة (ضرورية لعمل الـ Dependency Injection في FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
