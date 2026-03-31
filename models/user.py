from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True)

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    roles = relationship("UserRole", back_populates="user", foreign_keys="[UserRole.user_id]")
    portfolios = relationship("Portfolio", back_populates="owner")
    scenarios = relationship("Scenario", back_populates="creator")
    simulation_runs = relationship("SimulationRun", back_populates="initiator")
    reports = relationship("Report", back_populates="generator")
    audit_logs = relationship("AuditLog", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profile"

    profile_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), unique=True, nullable=False)
    full_name = Column(String)
    phone = Column(String)
    department = Column(String)
    bio = Column(String)
    avatar_url = Column(String)

    user = relationship("User", back_populates="profile")


class Role(Base):
    __tablename__ = "role"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String, nullable=False)
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    can_create = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)

    users = relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_role"

    user_id = Column(Integer, ForeignKey("user.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("role.role_id"), primary_key=True)
    assigned_at = Column(Date, default=func.current_date())
    assigned_by = Column(Integer, ForeignKey("user.user_id"))

    user = relationship("User", foreign_keys=[user_id], back_populates="roles")
    role = relationship("Role", back_populates="users")
