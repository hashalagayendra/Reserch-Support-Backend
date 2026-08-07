from sqlalchemy.orm import Session
from app.db.models import Student
from app.schemas.student import StudentCreate, StudentUpdate
from typing import List, Optional

def get_student(db: Session, student_id: int) -> Optional[Student]:
    return db.query(Student).filter(Student.id == student_id).first()

def get_student_by_email(db: Session, email: str) -> Optional[Student]:
    return db.query(Student).filter(Student.email == email).first()

def get_students(db: Session, skip: int = 0, limit: int = 100) -> List[Student]:
    return db.query(Student).offset(skip).limit(limit).all()

def create_student(db: Session, student: StudentCreate) -> Student:
    db_student = Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def update_student(db: Session, db_student: Student, student_update: StudentUpdate) -> Student:
    update_data = student_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return db_student

def delete_student(db: Session, db_student: Student) -> Student:
    db.delete(db_student)
    db.commit()
    return db_student
