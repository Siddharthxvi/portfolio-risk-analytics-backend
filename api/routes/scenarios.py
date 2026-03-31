from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from models.simulation import Scenario
from schemas.scenario import ScenarioCreate, ScenarioResponse
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.get("/", response_model=List[ScenarioResponse])
def get_scenarios(db: Session = Depends(get_db)):
    return db.query(Scenario).all()

@router.post("/", response_model=ScenarioResponse)
def create_scenario(scenario: ScenarioCreate, db: Session = Depends(get_db)):
    creator_id = 1 
    db_scen = Scenario(
        name=scenario.name, 
        description=scenario.description, 
        interest_rate_shock_bps=scenario.interest_rate_shock_bps,
        volatility_multiplier=scenario.volatility_multiplier,
        equity_shock_pct=scenario.equity_shock_pct,
        created_by=creator_id
    )
    db.add(db_scen)
    try:
        db.commit()
        db.refresh(db_scen)
        return db_scen
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e.orig))

@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scen = db.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scen

@router.delete("/{scenario_id}")
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
