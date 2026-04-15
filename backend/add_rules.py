from db import SessionLocal
from models.database import Agency, ScoringRule

db = SessionLocal()

# Get the agency
agency = db.query(Agency).filter(Agency.subdomain == "demoagency").first()

if not agency:
    print("Agency not found! Please create agency first.")
    print("Run: curl -X POST http://localhost:8000/api/agencies/register -H 'Content-Type: application/json' -d '{\"name\":\"Demo Agency\",\"subdomain\":\"demoagency\",\"email\":\"admin@demo.com\",\"password\":\"admin123\"}'")
    exit()

print(f"Agency found: {agency.name} (ID: {agency.id})")

# Delete existing rules for this agency (optional, to avoid duplicates)
db.query(ScoringRule).filter(ScoringRule.agency_id == agency.id).delete()
db.commit()
print("Cleared existing rules")

# Add fresh rules
rules_data = [
    {
        "name": "Urgency signal",
        "field": "urgency",
        "value": "asap|urgent|today|now|immediately",
        "modifier": 25
    },
    {
        "name": "Budget mention",
        "field": "budget",
        "value": "lakh|crore|thousand|lac",
        "modifier": 20
    },
    {
        "name": "Business clarity",
        "field": "business_type",
        "value": "agency|startup|business|company",
        "modifier": 15
    },
    {
        "name": "Time-waster signal",
        "field": "budget",
        "value": "free|cheap|low budget|no budget",
        "modifier": -30
    }
]

for rule_data in rules_data:
    rule = ScoringRule(
        agency_id=agency.id,
        name=rule_data["name"],
        condition_field=rule_data["field"],
        condition_operator="contains",
        condition_value=rule_data["value"],
        score_modifier=rule_data["modifier"],
        priority=1,
        is_active=True
    )
    db.add(rule)

db.commit()
print(f"Added {len(rules_data)} scoring rules for agency {agency.id}")

# Verify
rules = db.query(ScoringRule).filter(ScoringRule.agency_id == agency.id).all()
print("\n--- Current Rules ---")
for r in rules:
    print(f"  {r.name}: {r.condition_field} contains '{r.condition_value}' -> {r.score_modifier} points")

db.close()