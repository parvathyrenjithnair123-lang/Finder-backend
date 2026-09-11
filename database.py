from sqlalchemy import create_engine, Column, String, Integer, Float, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./finder.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TitleModel(Base):
    __tablename__ = "titles"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)
    coverUrl = Column(String)
    description = Column(String)
    country = Column(String)
    year = Column(Integer)
    genres = Column(JSON)  # Stores list of strings
    tags = Column(JSON)    # Stores list of strings
    rating = Column(Float)
    whereToWatch = Column(JSON)

def init_db():
    Base.metadata.create_all(bind=engine)