from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Report(Base):
    __tablename__ = "report"

    report_id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("simulation_run.run_id"))
    generated_by = Column(Integer, ForeignKey("users.user_id"))
    title = Column(String)
    generated_at = Column(DateTime, default=func.now())
    format = Column(String)
    summary = Column(Text)

    simulation_run = relationship("SimulationRun", back_populates="reports")
    generator = relationship("User", back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    entity_type = Column(String)
    entity_id = Column(Integer)
    operation = Column(String)
    old_value = Column(Text)
    new_value = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    ip_address = Column(String)

    user = relationship("User", back_populates="audit_logs")
