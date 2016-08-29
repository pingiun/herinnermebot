from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class Herinnering(Base):
    __tablename__ = 'herinneringen'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    timestamp = Column(DateTime)
    message = Column(String)
    from_chat_id = Column(Integer)
    from_message_id = Column(Integer)

    def __init__(self,
                 user_id=None,
                 timestamp=None,
                 message=None,
                 from_chat_id=None,
                 from_message_id=None,
                 id=None):
        self.id = id
        self.user_id = user_id
        self.timestamp = timestamp
        self.message = message
        self.from_chat_id = from_chat_id
        self.from_message_id = from_message_id
