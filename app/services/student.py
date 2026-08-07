from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.crud import student as crud
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from typing import List

def get_student_or_404(db: Session, student_id: int):
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student

def get_students(db: Session, skip: int = 0, limit: int = 100) -> List[StudentResponse]:
    return crud.get_students(db, skip=skip, limit=limit)

def create_student(db: Session, student: StudentCreate) -> StudentResponse:
    # Check if email is already registered
    existing_student = crud.get_student_by_email(db, student.email)
    if existing_student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_student(db, student)

def update_student(db: Session, student_id: int, student_update: StudentUpdate) -> StudentResponse:
    db_student = get_student_or_404(db, student_id)
    return crud.update_student(db, db_student, student_update)

def delete_student(db: Session, student_id: int) -> StudentResponse:
    db_student = get_student_or_404(db, student_id)
    return crud.delete_student(db, db_student)
