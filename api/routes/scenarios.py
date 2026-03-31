from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.auth import require_role, get_current_user
from models.simulation import Scenario
from schemas.scenario import ScenarioCreate, ScenarioResponse, ScenarioUpdate
from sqlalchemy.exc import IntegrityError

router = APIRouter()

ReadAccess  = Depends(require_role("ADMIN", "ANALYST", "VIEWER"))
WriteAccess = Depends(require_role("ADMIN", "ANALYST"))


@router.get("/", response_model=List[ScenarioResponse], dependencies=[ReadAccess])
def get_scenarios(db: Session = Depends(get_db)):
    return db.query(Scenario).all()


@router.get("/{scenario_id}", response_model=ScenarioResponse, dependencies=[ReadAccess])
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scen = db.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scen


@router.post("/", response_model=ScenarioResponse)
def create_scenario(
    scenario: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN", "ANALYST")),
):
    db_scen = Scenario(
        name=scenario.name,
        description=scenario.description,
        interest_rate_shock_bps=scenario.interest_rate_shock_bps,
        volatility_multiplier=scenario.volatility_multiplier,
        equity_shock_pct=scenario.equity_shock_pct,
        created_by=current_user["user_id"],
    )
    db.add(db_scen)
    try:
        db.commit()
        db.refresh(db_scen)
        return db_scen
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))


@router.put("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("ADMIN", "ANALYST")),
):
    """
    Partially update a scenario — only provided fields are changed.
    Access: ADMIN, ANALYST
    """
    scen = db.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(scen, field, value)

    try:
        db.commit()
        db.refresh(scen)
        return scen
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))


@router.delete("/{scenario_id}", dependencies=[WriteAccess])
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scen = db.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(scen)
    try:
        db.commit()
        return {"detail": "Scenario deleted"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))
