from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from db import get_db
from models.database import Agency, Lead, LeadAnswer
from services.scoring_service import ScoringService
from services.certainty_service import CertaintyService
from pydantic import BaseModel

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

class WebhookLeadRequest(BaseModel):
    source: str = "webhook"
    name: Optional[str] = "Unknown Lead"
    contact: str  # email or phone
    answers: Optional[Dict[str, str]] = {}

def get_agency_by_api_key(db: Session, api_key: str):
    """Validate API key and return agency"""
    return db.query(Agency).filter(Agency.api_key == api_key).first()

@router.post("/leads")
async def webhook_lead_intake(
    request: WebhookLeadRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    # 1. Validate API Key
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-KEY header required")
    
    agency = get_agency_by_api_key(db, x_api_key)
    if not agency:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    # 2. Determine if contact is email or phone
    email = None
    phone = None
    if "@" in request.contact:
        email = request.contact
    else:
        phone = request.contact
    
    # 3. Create lead (reusing your exact pattern from lead_routes.py)
    lead = Lead(
        agency_id=agency.id,
        source=request.source,
        name=request.name,
        email=email,
        phone=phone,
        first_contact=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        status="NEW",
        is_handled=False
    )
    db.add(lead)
    db.flush()
    
    # 4. Store answers (reusing your exact pattern)
    for question, answer in request.answers.items():
        lead_answer = LeadAnswer(
            lead_id=lead.id,
            question=question,
            answer=answer
        )
        db.add(lead_answer)
    
    db.commit()
    
    # 5. Score the lead (reusing your exact scoring service)
    score_result = ScoringService.calculate_score(db, lead.id, agency.id)
    
    # 6. Update revenue certainty (reusing your exact certainty service)
    CertaintyService.calculate_revenue_certainty(db, agency.id)
    
    # 7. Return success (matching your lead_routes response pattern)
    return {
        "status": "success",
        "lead_id": lead.id,
        "score": score_result["score"],
        "category": score_result["category"]
    }