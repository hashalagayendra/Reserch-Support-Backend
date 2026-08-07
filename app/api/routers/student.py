from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services import student as service

router = APIRouter()

@router.get("/", response_model=List[StudentResponse])
def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve students."""
    return service.get_students(db, skip=skip, limit=limit)

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student."""
    return service.create_student(db, student)

@router.get("/{student_id}", response_model=StudentResponse)
def read_student(student_id: int, db: Session = Depends(get_db)):
    """Get a specific student by ID."""
    return service.get_student_or_404(db, student_id)

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    """Update a specific student."""
    return service.update_student(db, student_id, student)

@router.delete("/{student_id}", response_model=StudentResponse)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a specific student."""
    return service.delete_student(db, student_id)
