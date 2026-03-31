from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True, index=True)
    default_iterations = Column(Integer, default=10000, nullable=False)
    default_horizon_days = Column(Integer, default=252, nullable=False)
    default_confidence_level = Column(Float, default=0.95, nullable=False)

    user = relationship("User", backref="settings")
