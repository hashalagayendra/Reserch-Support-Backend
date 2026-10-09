import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.portal_deps import get_current_user, verify_origin
from app.db.models import ApiKey, Project, User
from app.db.session import get_db
from app.schemas.portal import ApiKeyResponse, ProjectCreate, ProjectResponse

router = APIRouter()


def owned_project(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter_by(id=project_id, user_id=user.id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return db.query(Project).filter_by(user_id=user.id).order_by(Project.created_at.desc(), Project.id.desc()).all()


@router.post("", response_model=ProjectResponse, status_code=201, dependencies=[Depends(verify_origin)])
def create_project(data: ProjectCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = Project(name=data.name, user_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return owned_project(project_id, user, db)


@router.get("/{project_id}/api-keys", response_model=list[ApiKeyResponse])
def list_keys(project_id: int, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    owned_project(project_id, user, db)
    response.headers["Cache-Control"] = "no-store"
    return db.query(ApiKey).filter_by(project_id=project_id).order_by(ApiKey.id.desc()).all()


@router.post("/{project_id}/api-keys", response_model=ApiKeyResponse, status_code=201,
             dependencies=[Depends(verify_origin)])
def generate_key(project_id: int, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    owned_project(project_id, user, db)
    key = ApiKey(project_id=project_id, key_value="rk_" + secrets.token_urlsafe(32))
    db.add(key)
    db.commit()
    db.refresh(key)
    response.headers["Cache-Control"] = "no-store"
    return key


@router.delete("/{project_id}/api-keys/{key_id}", status_code=204, dependencies=[Depends(verify_origin)])
def revoke_key(project_id: int, key_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    owned_project(project_id, user, db)
    key = db.query(ApiKey).filter_by(id=key_id, project_id=project_id).first()
    if not key:
        raise HTTPException(404, "API key not found")
    db.delete(key)
    db.commit()
