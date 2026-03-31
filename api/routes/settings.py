from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user
from models.user_settings import UserSettings
from schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter()

@router.get("/", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    # Auto-create default settings if none exist
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        
    return settings

@router.put("/", response_model=SettingsResponse)
def update_settings(update_data: SettingsUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
    
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        
    for key, value in update_data.model_dump().items():
        setattr(settings, key, value)
        
    db.commit()
    db.refresh(settings)
    return settings
