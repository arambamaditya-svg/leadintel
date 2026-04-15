"""
ONE-TIME SETUP SCRIPT
Run this once to add scoring rules to ALL existing agencies
"""

from db import SessionLocal
from models.database import Agency, ScoringRule

def setup_scoring_for_all_agencies():
    db = SessionLocal()
    
    agencies = db.query(Agency).all()
    
    if not agencies:
        print("❌ No agencies found. Please register an agency first.")
        db.close()
        return
    
    rules_data = [
        ("urgency_signal", "urgency", "asap|urgent|today|now|immediately", 25),
        ("budget_signal", "budget", "lakh|crore|thousand|lac", 20),
        ("business_signal", "business_type", "agency|startup|business|company", 15),
    ]
    
    for agency in agencies:
        db.query(ScoringRule).filter(ScoringRule.agency_id == agency.id).delete()
        
        for name, field, value, points in rules_data:
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
        
        print(f"✅ Added {len(rules_data)} rules for {agency.name} (subdomain: {agency.subdomain})")
    
    db.commit()
    db.close()
    print("\n🎉 Scoring rules setup complete!")

if __name__ == "__main__":
    setup_scoring_for_all_agencies()