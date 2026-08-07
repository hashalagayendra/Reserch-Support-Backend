from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ApiKey

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(
    api_key_header: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> ApiKey:
    """
    Dependency to validate the API Key provided in the header.
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="API Key is missing"
        )
    
    # Query the database to check if the api key exists
    api_key = db.query(ApiKey).filter(ApiKey.key_value == api_key_header).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate API Key"
        )
        
    return api_key
