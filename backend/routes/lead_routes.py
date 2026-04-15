from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.database import Lead, LeadAnswer, LeadEvent, Agency, ScoringRule
from services.scoring_service import ScoringService
from utils.auth import get_current_agency
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/leads", tags=["Leads"])

class LeadCreateRequest(BaseModel):
    source: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    answers: Dict[str, str]

class LeadScoreResponse(BaseModel):
    lead_id: int
    score: int
    category: str

@router.get("/schema")
def get_lead_schema(agency: Agency = Depends(get_current_agency)):
    """Return dynamic form schema for lead intake"""
    return {
        "fields": [
            {"key": "urgency", "label": "How soon do you need this?", "type": "text", "required": True},
            {"key": "budget", "label": "Estimated budget (₹)", "type": "text", "required": True},
            {"key": "business_type", "label": "What type of business?", "type": "text", "required": True},
        ]
    }

@router.post("/intake", response_model=LeadScoreResponse)
def intake_lead(
    request: LeadCreateRequest, 
    agency: Agency = Depends(get_current_agency),
    db: Session = Depends(get_db)
):
    """Create a new lead, collect answers, calculate score"""
    
    lead = Lead(
        agency_id=agency.id,
        source=request.source,
        name=request.name,
        email=request.email,
        phone=request.phone,
        first_contact=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        status="NEW",
        is_handled=False
    )
    db.add(lead)
    db.flush()
    
    for question, answer in request.answers.items():
        lead_answer = LeadAnswer(
            lead_id=lead.id,
            question=question,
            answer=answer
        )
        db.add(lead_answer)
    
    db.commit()
    
    score_result = ScoringService.calculate_score(db, lead.id, agency.id)
    
    return LeadScoreResponse(
        lead_id=score_result["lead_id"],
        score=score_result["score"],
        category=score_result["category"]
    )

@router.get("/")
def get_my_leads(
    agency: Agency = Depends(get_current_agency),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all leads for the current user's agency"""
    
    leads = db.query(Lead).filter(Lead.agency_id == agency.id).order_by(
        Lead.score.desc(), Lead.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": l.id,
            "name": l.name,
            "email": l.email,
            "phone": l.phone,
            "score": l.score,
            "category": l.score_category,
            "source": l.source,
            "status": l.status,
            "first_contact": l.first_contact.isoformat() if l.first_contact else None,
            "last_activity": l.last_activity.isoformat() if l.last_activity else None,
            "is_handled": l.is_handled if hasattr(l, 'is_handled') else False
        }
        for l in leads
    ]

@router.get("/{lead_id}")
def get_lead_details(
    lead_id: int, 
    agency: Agency = Depends(get_current_agency),
    db: Session = Depends(get_db)
):
    """Get full lead details with answers and events"""
    
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.agency_id == agency.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    answers = db.query(LeadAnswer).filter(LeadAnswer.lead_id == lead_id).all()
    events = db.query(LeadEvent).filter(LeadEvent.lead_id == lead_id).all()
    
    return {
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "score": lead.score,
        "category": lead.score_category,
        "source": lead.source,
        "status": lead.status,
        "first_contact": lead.first_contact.isoformat() if lead.first_contact else None,
        "last_activity": lead.last_activity.isoformat() if lead.last_activity else None,
        "is_handled": lead.is_handled if hasattr(lead, 'is_handled') else False,
        "answers": [{"question": a.question, "answer": a.answer} for a in answers],
        "events": [{"type": e.event_type, "notes": e.notes, "time": e.created_at.isoformat()} for e in events]
    }

@router.get("/certainty")
def get_revenue_certainty(
    agency: Agency = Depends(get_current_agency),
    db: Session = Depends(get_db)
):
    """Get revenue certainty for the agency"""
    from services.certainty_service import CertaintyService
    return CertaintyService.get_latest_certainty(db, agency.id)

@router.post("/certainty/refresh")
def refresh_revenue_certainty(
    agency: Agency = Depends(get_current_agency),
    db: Session = Depends(get_db)
):
    """Force refresh revenue certainty calculation"""
    from services.certainty_service import CertaintyService
    return CertaintyService.calculate_revenue_certainty(db, agency.id)

@router.post("/{lead_id}/handle")
def mark_handled(
    lead_id: int,
    agency: Agency = Depends(get_current_agency),
    db: Session = Depends(get_db)
):
    """Mark lead as handled (user has seen/responded to it)"""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.agency_id == agency.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.is_handled = True
    
    event = LeadEvent(
        lead_id=lead_id,
        event_type="handled",
        notes="Marked as handled from dashboard"
    )
    db.add(event)
    db.commit()
    
    return {"success": True, "message": "Lead marked as handled"}

@router.post("/{lead_id}/unhandle")
def mark_unhandled(
    lead_id: int,
    agency: Agency = Depends(get_current_agency),
    db: Session = Depends(get_db)
):
    """Mark lead as unhandled (user wants to revisit it)"""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.agency_id == agency.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.is_handled = False
    
    event = LeadEvent(
        lead_id=lead_id,
        event_type="unhandled",
        notes="Marked as unhandled from dashboard"
    )
    db.add(event)
    db.commit()
    
    return {"success": True, "message": "Lead marked as unhandled"}

@router.delete("/{lead_id}")
def delete_lead(
    lead_id: int,
    agency: Agency = Depends(get_current_agency),
    db: Session = Depends(get_db)
):
    """Delete a lead and all its related data"""
    
    lead = db.query(Lead).filter(
        Lead.id == lead_id,
        Lead.agency_id == agency.id
    ).first()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Delete related answers first (foreign key constraint)
    db.query(LeadAnswer).filter(LeadAnswer.lead_id == lead_id).delete()
    
    # Delete related events
    db.query(LeadEvent).filter(LeadEvent.lead_id == lead_id).delete()
    
    # Delete the lead
    db.delete(lead)
    db.commit()
    
    return {"success": True, "message": "Lead deleted successfully"}