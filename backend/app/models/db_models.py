import os
from datetime import datetime
from sqlalchemy import create_engine, inspect, text, Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

os.makedirs("data", exist_ok=True)
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    path = Column(String)
    pages = Column(Integer, default=0)
    chunks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True)
    mode = Column(String)  # naive | rerank | agent
    question = Column(Text)
    report = Column(Text)
    citations = Column(JSON)
    latency_s = Column(Float)
    tokens = Column(Integer)
    cost_usd = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class EvalResult(Base):
    __tablename__ = "eval_results"
    id = Column(Integer, primary_key=True)
    setup = Column(String)  # naive | rerank | agent
    hit_rate = Column(Float)
    faithfulness = Column(Float)
    avg_latency_s = Column(Float)
    avg_cost_usd = Column(Float)
    n_questions = Column(Integer, default=0)
    by_category = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
    # create_all never alters existing tables, so add columns older databases lack
    cols = {c["name"] for c in inspect(engine).get_columns("eval_results")}
    if "by_category" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE eval_results ADD COLUMN by_category JSON"))
