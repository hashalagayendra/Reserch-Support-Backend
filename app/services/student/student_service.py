from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.models import Student
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from typing import List, Optional

def get_student(db: Session, student_id: int) -> Optional[Student]:
    return db.query(Student).filter(Student.id == student_id).first()

def get_student_or_404(db: Session, student_id: int) -> Student:
    student = get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

def get_student_by_email(db: Session, email: str) -> Optional[Student]:
    return db.query(Student).filter(Student.email == email).first()

def get_students(db: Session, skip: int = 0, limit: int = 100) -> List[Student]:
    return db.query(Student).offset(skip).limit(limit).all()

def create_student(db: Session, student: StudentCreate) -> Student:
    # Service logic: Check if email is already registered
    existing_student = get_student_by_email(db, student.email)
    if existing_student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # CRUD logic: Create the student
    db_student = Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def update_student(db: Session, student_id: int, student_update: StudentUpdate) -> Student:
    # Service logic: Ensure student exists
    db_student = get_student_or_404(db, student_id)
    
    # CRUD logic: Update the student
    update_data = student_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student

def delete_student(db: Session, student_id: int) -> Student:
    # Service logic: Ensure student exists
    db_student = get_student_or_404(db, student_id)
    
    # CRUD logic: Delete the student
    db.delete(db_student)
    db.commit()
    return db_student
