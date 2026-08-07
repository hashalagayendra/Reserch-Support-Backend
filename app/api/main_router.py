from fastapi import APIRouter
from app.api.routers import student

api_router = APIRouter()

# Include the student router without the security dependency
api_router.include_router(
    student.router, 
    prefix="/students", 
    tags=["students"]
)
