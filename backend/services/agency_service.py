from sqlalchemy.orm import Session
from models.database import Agency, User
from datetime import datetime
import secrets
from utils.auth import get_password_hash

def create_agency(db: Session, name: str, subdomain: str, owner_email: str, owner_password: str):
    """Create a new agency with its owner user"""
    
    # Check if subdomain exists
    existing = db.query(Agency).filter(Agency.subdomain == subdomain).first()
    if existing:
        return None, "Subdomain already taken"
    
    # Create agency with default values
    agency = Agency(
        name=name,
        subdomain=subdomain,
        settings="{}",
        monthly_target=500000,  # Explicit default
        avg_deal_size=50000      # Explicit default
    )
    db.add(agency)
    db.flush()
    
    # Create owner user
    user = User(
        agency_id=agency.id,
        email=owner_email,
        password_hash=get_password_hash(owner_password),
        full_name=owner_email.split("@")[0],
        role="owner"
    )
    db.add(user)
    db.commit()
    db.refresh(agency)
    
    return agency, None

def get_agency_by_subdomain(db: Session, subdomain: str):
    return db.query(Agency).filter(Agency.subdomain == subdomain).first()