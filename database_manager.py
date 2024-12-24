from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

from models.base import Base

class DatabaseManager:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def __del__(self):
        self.session.close()
        self.engine.dispose()