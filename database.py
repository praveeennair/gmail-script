from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Email(Base):
    __tablename__ = 'emails'

    id = Column(String(50), primary_key=True)
    thread_id = Column(String(50))
    sender = Column(String(255))
    recipient = Column(String(255))
    subject = Column(String(255))
    body = Column(Text)
    received_date = Column(DateTime)
    labels = Column(String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'sender': self.sender,
            'recipient': self.recipient,
            'subject': self.subject,
            'body': self.body,
            'received_date': self.received_date,
            'labels': self.labels.split(',') if self.labels else []
        }

def init_db(db_url='sqlite:///emails.db'):
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()