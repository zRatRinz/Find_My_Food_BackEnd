from sqlmodel import create_engine, Session
from app.core.config import DBURL

engine = create_engine(
    DBURL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=300,
)

def get_db():
    with Session(engine) as db:
        yield db