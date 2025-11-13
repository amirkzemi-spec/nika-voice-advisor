import os
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker

# ====================================================
# 📦 Database path & connection
# ====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nika_data.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ====================================================
# 👤 User table (for login)
# ====================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    confirmed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)



# ====================================================
# 🌍 Visa Programs (used in RAG)
# ====================================================
class VisaProgram(Base):
    __tablename__ = "visa_programs"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String)
    visa_type = Column(String)
    requirements = Column(String)
    eligibility = Column(String)
    duration = Column(String)
    fee = Column(String)
    benefits = Column(String)
    application_link = Column(String)
    source_url = Column(String)
    last_updated = Column(String)


# ====================================================
# 🎓 Scholarships (used in RAG)
# ====================================================
class Scholarship(Base):
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    country = Column(String)
    degree_level = Column(String)
    funding_type = Column(String)
    deadline = Column(String)
    min_gpa = Column(Float)
    description = Column(String)


# ====================================================
# 🧩 Schema creation helper
# ====================================================
def init_db():
    print("🚀 Creating unified database schema...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables ready in:", DB_PATH)


if __name__ == "__main__":
    init_db()
