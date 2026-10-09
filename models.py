import os
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Float,
    ForeignKey, DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, default="player")
    balance = Column(Float, default=1000)
    energy = Column(Integer, default=10)
    max_energy = Column(Integer, default=10)
    last_energy_update = Column(DateTime, default=datetime.utcnow)
    last_bonus = Column(DateTime, nullable=True)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    total_cars_obtained = Column(Integer, default=0)
    country = Column(String, default="germany")
    created_at = Column(DateTime, default=datetime.utcnow)

    cars = relationship("UserCar", back_populates="user", cascade="all, delete-orphan")


class UserCar(Base):
    __tablename__ = "user_cars"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    brand = Column(String, nullable=False)
    model = Column(String, default="")
    year = Column(Integer, nullable=False)
    color = Column(String, nullable=False)
    rarity = Column(String, nullable=False)
    condition = Column(Integer, default=100)
    price = Column(Float, nullable=False)
    obtained_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="cars")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
