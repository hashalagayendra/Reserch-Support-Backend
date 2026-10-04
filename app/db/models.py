from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Table, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.session import Base

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Student(Base, TimestampMixin):
    """
    Database model representing a Student (Legacy).
    """
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, index=True, nullable=False)

    user = relationship("User", back_populates="projects")
    api_keys = relationship("ApiKey", back_populates="project", cascade="all, delete-orphan")
    ai_tools = relationship("AITool", back_populates="project", cascade="all, delete-orphan")


class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    key_value = Column(String, unique=True, index=True, nullable=False)

    project = relationship("Project", back_populates="api_keys")


class AITool(Base, TimestampMixin):
    __tablename__ = "ai_tools"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    tool_title = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    argument = Column(JSON, nullable=True)
    api_url = Column(String, nullable=True)
    http_method = Column(String, nullable=True)
    headers = Column(JSON, nullable=True)
    vector_data = Column(Vector(1024))  # 1024 is default for Voyage-4-lite embeddings

    project = relationship("Project", back_populates="ai_tools")

