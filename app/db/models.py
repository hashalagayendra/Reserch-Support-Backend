from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.session import Base

class Student(Base):
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


class ProjectApiKey(Base):
    """
    Association Object for the many-to-many relationship between Project and ApiKey.
    Using a class instead of a Table allows you to easily add extra fields in the future
    (like `assigned_at`, `permissions`, etc.).
    """
    __tablename__ = "project_apikeys"

    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    apikey_id = Column(Integer, ForeignKey("api_keys.id", ondelete="CASCADE"), primary_key=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, index=True, nullable=False)

    user = relationship("User", back_populates="projects")
    api_keys = relationship("ApiKey", secondary="project_apikeys", back_populates="projects")
    ai_tools = relationship("AITool", back_populates="project", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_value = Column(String, unique=True, index=True, nullable=False)

    projects = relationship("Project", secondary="project_apikeys", back_populates="api_keys")


class AITool(Base):
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

