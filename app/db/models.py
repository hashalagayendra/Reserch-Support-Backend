from sqlalchemy import Column, Integer, String, Boolean
from app.db.session import Base

class Student(Base):
    """
    Database model representing a Student.
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
