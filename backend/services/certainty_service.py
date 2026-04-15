from sqlalchemy.orm import Session
from models.database import Lead, CertaintySnapshot, Agency
from datetime import datetime, timedelta

class CertaintyService:
    
    @staticmethod
    def calculate_revenue_certainty(db: Session, agency_id: int) -> dict:
        """Calculate revenue certainty based on HOT/WARM leads only (COLD leads excluded)"""
        
        # Get agency settings
        agency = db.query(Agency).filter(Agency.id == agency_id).first()
        monthly_target = agency.monthly_target if agency else 500000
        avg_deal_size = agency.avg_deal_size if agency else 50000
        
        # Daily target (monthly_target / 30)
        daily_target = monthly_target / 30
        
        # Get CURRENT MONTH's leads (not just today)
        today = datetime.utcnow()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        leads_this_month = db.query(Lead).filter(
            Lead.agency_id == agency_id,
            Lead.created_at >= first_day_of_month
        ).all()
        
        # Count leads by category (only from current month)
        hot_count = len([l for l in leads_this_month if l.score_category == "HOT"])
        warm_count = len([l for l in leads_this_month if l.score_category == "WARM"])
        cold_count = len([l for l in leads_this_month if l.score_category == "COLD"])
        total_leads = hot_count + warm_count + cold_count
        
        # Conversion rates: HOT = 50%, WARM = 20% (COLD excluded from revenue)
        hot_conversion = 0.5
        warm_conversion = 0.2
        
        # Estimated revenue from HOT and WARM leads only (COLD excluded)
        estimated_revenue = (
            (hot_count * hot_conversion * avg_deal_size) +
            (warm_count * warm_conversion * avg_deal_size)
        )
        
        # Revenue certainty percentage (0-100) based on monthly target
        if monthly_target > 0:
            revenue_certainty = min(100, int((estimated_revenue / monthly_target) * 100))
        else:
            revenue_certainty = 50
        
        # Risk level based on revenue certainty
        if revenue_certainty >= 70:
            risk_level = "LOW"
        elif revenue_certainty >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Save snapshot
        snapshot = CertaintySnapshot(
            agency_id=agency_id,
            total_leads_today=total_leads,
            hot_leads_count=hot_count,
            warm_leads_count=warm_count,
            cold_leads_count=cold_count,
            estimated_revenue_today=int(estimated_revenue),
            revenue_certainty_percent=revenue_certainty,
            risk_level=risk_level,
            snapshot_date=datetime.utcnow()
        )
        db.add(snapshot)
        db.commit()
        
        return {
            "total_leads_this_month": total_leads,
            "hot_count": hot_count,
            "warm_count": warm_count,
            "cold_count": cold_count,
            "estimated_revenue_this_month": int(estimated_revenue),
            "revenue_certainty_percent": revenue_certainty,
            "risk_level": risk_level,
            "monthly_target": monthly_target,
            "avg_deal_size": avg_deal_size
        }
    
    @staticmethod
    def get_latest_certainty(db: Session, agency_id: int) -> dict:
        """Get the most recent certainty snapshot"""
        
        snapshot = db.query(CertaintySnapshot).filter(
            CertaintySnapshot.agency_id == agency_id
        ).order_by(CertaintySnapshot.snapshot_date.desc()).first()
        
        if not snapshot:
            return CertaintyService.calculate_revenue_certainty(db, agency_id)
        
        # Also get agency settings
        agency = db.query(Agency).filter(Agency.id == agency_id).first()
        
        return {
            "total_leads_this_month": snapshot.total_leads_today,
            "hot_count": snapshot.hot_leads_count,
            "warm_count": snapshot.warm_leads_count,
            "cold_count": snapshot.cold_leads_count,
            "estimated_revenue_this_month": snapshot.estimated_revenue_today,
            "revenue_certainty_percent": snapshot.revenue_certainty_percent,
            "risk_level": snapshot.risk_level,
            "snapshot_date": snapshot.snapshot_date.isoformat() if snapshot.snapshot_date else None,
            "monthly_target": agency.monthly_target if agency else 500000,
            "avg_deal_size": agency.avg_deal_size if agency else 50000
        }