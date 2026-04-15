from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Agency(Base):
    __tablename__ = "agencies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False, index=True)
    settings = Column(Text, nullable=True)  # JSON stored as string
    monthly_target = Column(Integer, default=500000)  # Monthly revenue target in rupees
    avg_deal_size = Column(Integer, default=50000)    # Average deal size in rupees
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="agency")
    leads = relationship("Lead", back_populates="agency")
    scoring_rules = relationship("ScoringRule", back_populates="agency")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    full_name = Column(String(200), nullable=True)
    role = Column(String(50), default="owner")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agency = relationship("Agency", back_populates="users")

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    external_id = Column(String(200), nullable=True, index=True)  # For IG/WhatsApp IDs
    source = Column(String(50), nullable=False)  # instagram, website, whatsapp, ads
    name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    status = Column(String(50), default="new")  # new, contacted, converted, lost
    score = Column(Integer, default=0)
    score_category = Column(String(20), default="COLD")  # HOT, WARM, COLD
    first_contact = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_handled = Column(Boolean, default=False)  # NEW: User has marked this lead as handled
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agency = relationship("Agency", back_populates="leads")
    answers = relationship("LeadAnswer", back_populates="lead")
    events = relationship("LeadEvent", back_populates="lead")
    
    __table_args__ = (
        Index('idx_agency_score', 'agency_id', 'score'),
        Index('idx_agency_status', 'agency_id', 'status'),
    )

class LeadAnswer(Base):
    __tablename__ = "lead_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="answers")

class LeadEvent(Base):
    __tablename__ = "lead_events"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # message_received, followup_sent, converted, lost, handled, unhandled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lead = relationship("Lead", back_populates="events")

class ScoringRule(Base):
    __tablename__ = "scoring_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    name = Column(String(200), nullable=False)
    condition_field = Column(String(100), nullable=False)  # urgency, budget, business_type, etc.
    condition_operator = Column(String(20), default="contains")  # contains, equals, greater_than
    condition_value = Column(String(500), nullable=False)
    score_modifier = Column(Integer, nullable=False)  # +10, -5, etc.
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # order of evaluation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agency = relationship("Agency", back_populates="scoring_rules")

class CertaintySnapshot(Base):
    __tablename__ = "certainty_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    total_leads_today = Column(Integer, default=0)
    hot_leads_count = Column(Integer, default=0)
    warm_leads_count = Column(Integer, default=0)
    cold_leads_count = Column(Integer, default=0)
    leads_waiting_long = Column(Integer, default=0)  # > 24h no response
    avg_response_time_minutes = Column(Float, default=0)
    estimated_revenue_today = Column(Integer, default=0)
    revenue_certainty_percent = Column(Integer, default=50)
    risk_level = Column(String(20), default="MEDIUM")
    snapshot_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agency = relationship("Agency")