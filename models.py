from sqlalchemy import Column, Integer, String, Text
from .database import Base


class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String)
    topic = Column(String)
    text = Column(Text)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text)
    question_type = Column(String)  
    options = Column(Text)
    answer = Column(String)
    difficulty = Column(String)
    chunk_id = Column(Integer)


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer)
    user_answer = Column(String)
    correct = Column(String)
