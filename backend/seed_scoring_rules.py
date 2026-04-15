import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from db import SessionLocal
from models.database import Agency, ScoringRule

def seed_rules_for_agency(agency_id: int):
    db = SessionLocal()
    
    rules = [
        {
            "name": "Urgency signal",
            "condition_field": "urgency",
            "condition_operator": "contains",
            "condition_value": "asap|urgent|today|now|immediately",
            "score_modifier": 25,
            "priority": 1
        },
        {
            "name": "Budget mention",
            "condition_field": "budget",
            "condition_operator": "contains",
            "condition_value": "lakh|crore|thousand|lac",
            "score_modifier": 20,
            "priority": 2
        },
        {
            "name": "Business clarity",
            "condition_field": "business_type",
            "condition_operator": "contains",
            "condition_value": "agency|startup|business|company",
            "score_modifier": 15,
            "priority": 3
        },
        {
            "name": "Time-waster signals",
            "condition_field": "budget",
            "condition_operator": "contains",
            "condition_value": "free|cheap|low budget|no budget",
            "score_modifier": -30,
            "priority": 4
        }
    ]
    
    for rule_data in rules:
        rule = ScoringRule(
            agency_id=agency_id,
            name=rule_data["name"],
            condition_field=rule_data["condition_field"],
            condition_operator=rule_data["condition_operator"],
            condition_value=rule_data["condition_value"],
            score_modifier=rule_data["score_modifier"],
            priority=rule_data["priority"],
            is_active=True
        )
        db.add(rule)
    
    db.commit()
    db.close()
    print(f"Scoring rules added for agency {agency_id}")

if __name__ == "__main__":
    # Get first agency
    db = SessionLocal()
    agency = db.query(Agency).first()
    db.close()
    
    if agency:
        seed_rules_for_agency(agency.id)
    else:
        print("No agency found. Register an agency first.")