from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from services.agency_service import create_agency, get_agency_by_subdomain
from models.database import Agency, ScoringRule, User
from utils.auth import verify_password, create_access_token, get_password_hash, get_current_agency
from pydantic import BaseModel

router = APIRouter(prefix="/api/agencies", tags=["Agencies"])

class AgencyCreateRequest(BaseModel):
    name: str
    subdomain: str
    email: str
    password: str

class AgencyResponse(BaseModel):
    id: int
    name: str
    subdomain: str

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class AgencySettingsRequest(BaseModel):
    monthly_target: int
    avg_deal_size: int

@router.get("/")
def list_agencies(db: Session = Depends(get_db)):
    """List all agencies"""
    agencies = db.query(Agency).all()
    return [{"id": a.id, "name": a.name, "subdomain": a.subdomain} for a in agencies]

@router.post("/register", response_model=AgencyResponse)
def register_agency(request: AgencyCreateRequest, db: Session = Depends(get_db)):
    agency, error = create_agency(
        db=db,
        name=request.name,
        subdomain=request.subdomain,
        owner_email=request.email,
        owner_password=request.password
    )
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    # AUTO-ADD SCORING RULES FOR NEW AGENCY
    default_rules = [
        ("urgency_signal", "urgency", "asap|urgent|today|now|immediately", 25),
        ("budget_signal", "budget", "lakh|crore|thousand|lac", 20),
        ("business_signal", "business_type", "agency|startup|business|company", 15),
    ]
    
    for name, field, value, points in default_rules:
        rule = ScoringRule(
            agency_id=agency.id,
            name=name,
            condition_field=field,
            condition_operator="contains",
            condition_value=value,
            score_modifier=points,
            priority=1,
            is_active=True
        )
        db.add(rule)
    
    db.commit()
    print(f"✅ Auto-added {len(default_rules)} scoring rules for new agency: {agency.name}")
    
    return AgencyResponse(id=agency.id, name=agency.name, subdomain=agency.subdomain)

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"user_id": user.id, "agency_id": user.agency_id})
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "agency_id": user.agency_id,
            "agency_name": user.agency.name
        }
    )

# ===== SPECIFIC PATHS FIRST (BEFORE DYNAMIC {subdomain}) =====

@router.get("/scoring-rules")
def get_scoring_rules(
    agency: Agency = Depends(get_current_agency), 
    db: Session = Depends(get_db)
):
    """Get all scoring rules for the current agency"""
    print("🔥 GET /scoring-rules was called!")
    rules = db.query(ScoringRule).filter(ScoringRule.agency_id == agency.id).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "field": r.condition_field,
            "keywords": r.condition_value,
            "points": r.score_modifier,
            "is_active": r.is_active
        }
        for r in rules
    ]

@router.post("/scoring-rules")
def create_scoring_rule(
    request: dict,
    agency: Agency = Depends(get_current_agency), 
    db: Session = Depends(get_db)
):
    """Create a new scoring rule"""
    print("🔥 POST /scoring-rules was called!")
    field = request.get("field")
    keywords = request.get("keywords")
    points = request.get("points")
    
    if not field or not keywords or points is None:
        raise HTTPException(status_code=400, detail="Missing required fields: field, keywords, points")
    
    new_rule = ScoringRule(
        agency_id=agency.id,
        name=request.get("name", f"{field}_rule"),
        condition_field=field,
        condition_operator="contains",
        condition_value=keywords,
        score_modifier=points,
        priority=db.query(ScoringRule).filter(ScoringRule.agency_id == agency.id).count() + 1,
        is_active=True
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return {"id": new_rule.id, "success": True}

@router.put("/scoring-rules/{rule_id}")
def update_scoring_rule(
    rule_id: int,
    request: dict,
    agency: Agency = Depends(get_current_agency), 
    db: Session = Depends(get_db)
):
    """Update an existing scoring rule"""
    print(f"🔥 PUT /scoring-rules/{rule_id} was called!")
    rule = db.query(ScoringRule).filter(
        ScoringRule.id == rule_id, 
        ScoringRule.agency_id == agency.id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    if "keywords" in request:
        rule.condition_value = request["keywords"]
    if "points" in request:
        rule.score_modifier = request["points"]
    if "is_active" in request:
        rule.is_active = request["is_active"]
    
    db.commit()
    return {"success": True}

@router.delete("/scoring-rules/{rule_id}")
def delete_scoring_rule(
    rule_id: int,
    agency: Agency = Depends(get_current_agency), 
    db: Session = Depends(get_db)
):
    """Delete a scoring rule"""
    print(f"🔥 DELETE /scoring-rules/{rule_id} was called!")
    rule = db.query(ScoringRule).filter(
        ScoringRule.id == rule_id, 
        ScoringRule.agency_id == agency.id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(rule)
    db.commit()
    return {"success": True}

@router.get("/settings/me")
def get_my_agency_settings(
    agency: Agency = Depends(get_current_agency),
    db: Session = Depends(get_db)
):
    """Get current agency settings"""
    return {
        "monthly_target": agency.monthly_target,
        "avg_deal_size": agency.avg_deal_size
    }

@router.put("/settings/me")
def update_my_agency_settings(
    request: AgencySettingsRequest,
    agency: Agency = Depends(get_current_agency),
    db: Session = Depends(get_db)
):
    """Update current agency settings"""
    agency.monthly_target = request.monthly_target
    agency.avg_deal_size = request.avg_deal_size
    db.commit()
    
    return {
        "success": True,
        "monthly_target": agency.monthly_target,
        "avg_deal_size": agency.avg_deal_size
    }

# ===== DYNAMIC PATHS LAST =====

@router.get("/{subdomain}")
def get_agency(subdomain: str, db: Session = Depends(get_db)):
    agency = get_agency_by_subdomain(db, subdomain)
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    return AgencyResponse(id=agency.id, name=agency.name, subdomain=agency.subdomain)

@router.get("/{subdomain}/rules")
def get_agency_rules_by_subdomain(subdomain: str, db: Session = Depends(get_db)):
    """Get all scoring rules for an agency by subdomain"""
    agency = db.query(Agency).filter(Agency.subdomain == subdomain).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agency not found")
    
    rules = db.query(ScoringRule).filter(ScoringRule.agency_id == agency.id).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "condition_field": r.condition_field,
            "condition_operator": r.condition_operator,
            "condition_value": r.condition_value,
            "score_modifier": r.score_modifier,
            "is_active": r.is_active,
            "priority": r.priority
        }
        for r in rules
    ]