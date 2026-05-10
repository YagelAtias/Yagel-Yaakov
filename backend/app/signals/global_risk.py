from statistics import median, mean
from sqlalchemy.orm import Session
from ..db import models

class GlobalRiskEngine:
    """
    Calculates a student's long-term 'Global Risk Profile'.
    Fuses the median of their historical audio/text distress logs
    with their academic grade trends to prevent single-day outliers
    from skewing the data, as requested by clinical guidelines.
    """
    def __init__(self, db: Session):
        self.db = db

    def calculate_student_risk(self, student_id: int) -> dict:
        # 1. Fetch the last 10 distress logs for this student
        logs = self.db.query(models.DistressLog).filter(
            models.DistressLog.student_id == student_id
        ).order_by(models.DistressLog.timestamp.desc()).limit(10).all()
        
        # 2. Fetch the last 10 grades across all subjects
        grades = self.db.query(models.Grade).filter(
            models.Grade.student_id == student_id
        ).order_by(models.Grade.date_recorded.desc()).limit(10).all()
        
        if not logs:
            return {
                "global_risk_score": 0.0,
                "baseline_median": 0.0,
                "baseline_average": 0.0,
                "blended_baseline": 0.0,
                "grade_trend": "stable",
                "multiplier_applied": 1.0,
                "has_recent_critical": False,
                "logs_analyzed": 0,
                "grades_analyzed": len(grades),
                "status": "insufficient_data"
            }
            
        # BASELINE CALCULATION
        # As requested, we fuse BOTH the Median and the Average.
        # Median prevents a single outlier (one bad day) from throwing off the whole score.
        # Average ensures we don't completely ignore severe spikes.
        # We use a 70/30 split favoring the median for stability.
        scores = [log.overall_score for log in logs]
        distress_median = median(scores)
        distress_average = mean(scores)
        
        baseline_score = (distress_median * 0.7) + (distress_average * 0.3)
        
        # ACADEMIC FUSION (GRADE TRENDS)
        grade_multiplier = 1.0
        grade_trend = "stable"
        
        if len(grades) >= 4:
            # Compare the average of their 2 most recent grades against their previous 2 grades
            recent_avg = sum(g.score for g in grades[:2]) / 2
            old_avg = sum(g.score for g in grades[2:4]) / 2
            
            point_difference = old_avg - recent_avg
            
            if point_difference >= 15:
                # Severe academic drop! (e.g., 90 to 70). This is a strong indicator of distress.
                grade_multiplier = 1.3
                grade_trend = "severe_drop"
            elif point_difference >= 7:
                # Mild decline
                grade_multiplier = 1.1
                grade_trend = "decline"
            elif point_difference <= -10:
                # Academic improvement! (e.g., 70 to 85). This dampens the risk score.
                grade_multiplier = 0.85
                grade_trend = "improvement"

        # CRITICAL SAFETY OVERRIDE
        # If any of their last 3 interactions contained critical safety triggers (self-harm),
        # we completely ignore positive grade dampeners and multiply the risk.
        has_recent_critical = any(log.has_critical_alert for log in logs[:3])
        if has_recent_critical:
            grade_multiplier = max(grade_multiplier, 1.4)
            
        # FINAL CALCULATION
        final_risk = min(baseline_score * grade_multiplier, 1.0)
        
        return {
            "global_risk_score": round(final_risk, 2),
            "baseline_median": round(distress_median, 2),
            "baseline_average": round(distress_average, 2),
            "blended_baseline": round(baseline_score, 2),
            "grade_trend": grade_trend,
            "multiplier_applied": round(grade_multiplier, 2),
            "has_recent_critical": has_recent_critical,
            "logs_analyzed": len(logs),
            "grades_analyzed": len(grades)
        }
