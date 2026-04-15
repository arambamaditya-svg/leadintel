from sqlalchemy.orm import Session
from models.database import Lead, ScoringRule, LeadAnswer, LeadEvent
from datetime import datetime
import json

class ScoringService:
    
    @staticmethod
    def calculate_score(db: Session, lead_id: int, agency_id: int) -> dict:
        """Calculate lead score based on active scoring rules"""
        
        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.agency_id == agency_id).first()
        if not lead:
            return {"error": "Lead not found"}
        
        # Get all active rules for this agency
        rules = db.query(ScoringRule).filter(
            ScoringRule.agency_id == agency_id,
            ScoringRule.is_active == True
        ).order_by(ScoringRule.priority).all()
        
        # Get lead answers
        answers = db.query(LeadAnswer).filter(LeadAnswer.lead_id == lead_id).all()
        answers_dict = {a.question: a.answer for a in answers}
        
        # Start with base score
        total_score = 0
        applied_rules = []
        
        for rule in rules:
            # Check if condition field exists in answers
            field_value = answers_dict.get(rule.condition_field, "")
            
            if ScoringService._check_condition(field_value, rule.condition_operator, rule.condition_value):
                total_score += rule.score_modifier
                applied_rules.append({
                    "rule_id": rule.id,
                    "name": rule.name,
                    "modifier": rule.score_modifier
                })
        
        # Ensure score stays within 0-100
        final_score = max(0, min(100, total_score))
        
        # Determine category
        if final_score >= 70:
            category = "HOT"
        elif final_score >= 40:
            category = "WARM"
        else:
            category = "COLD"
        
        # Update lead
        lead.score = final_score
        lead.score_category = category
        lead.last_activity = datetime.utcnow()
        db.commit()
        
        # Log event
        event = LeadEvent(
            lead_id=lead_id,
            event_type="scored",
            notes=json.dumps({"score": final_score, "category": category, "rules_applied": applied_rules})
        )
        db.add(event)
        db.commit()
        
        return {
            "lead_id": lead_id,
            "score": final_score,
            "category": category,
            "rules_applied": applied_rules
        }
    
    @staticmethod
    def _check_condition(value: str, operator: str, condition_value: str) -> bool:
        """Evaluate a single condition - supports both pipe and comma separated keywords"""
        
        if not value:
            return False
        
        value_lower = value.lower().strip()
        cond_lower = condition_value.lower().strip()
        
        if operator == "contains":
            # Support both pipe and comma separation
            keywords = []
            if "|" in cond_lower:
                keywords = cond_lower.split("|")
            elif "," in cond_lower:
                keywords = [k.strip() for k in cond_lower.split(",")]
            else:
                keywords = [cond_lower]
            
            for keyword in keywords:
                if keyword and keyword.strip() in value_lower:
                    return True
            return False
        elif operator == "equals":
            return value_lower == cond_lower
        elif operator == "starts_with":
            return value_lower.startswith(cond_lower)
        elif operator == "greater_than":
            try:
                return float(value) > float(cond_lower)
            except:
                return False
        else:
            return False