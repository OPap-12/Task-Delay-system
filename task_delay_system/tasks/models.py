from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta

# Constants for risk calculations
HIGH_RISK_THRESHOLD = 70
MODERATE_RISK_THRESHOLD = 40
OVERDUE_RISK = 100
TODAY_RISK = 90
TOMORROW_RISK = 80
DAY_AFTER_RISK = 70
WEEK_RISK = 50
DEFAULT_RISK = 20

PRIORITY_ADJUSTMENTS = {
    'high': 10,
    'medium': 0,
    'low': -10
}

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_delayed(self):
        """Check if task is delayed"""
        if self.completed and self.completed_at:
            return self.completed_at.date() > self.due_date
        return timezone.now().date() > self.due_date

    def is_at_risk(self):
        """Check if task is at risk (due within 2 days)"""
        if self.completed:
            return False
        days_left = (self.due_date - timezone.now().date()).days
        return 0 <= days_left <= 2

    def days_until_due(self):
        """Calculate days until due date"""
        return (self.due_date - timezone.now().date()).days

    def completion_probability(self):
        """
        Predict completion probability based on:
        - Days until due date
        - Task priority
        - Historical completion rate (if available)
        """
        days_left = self.days_until_due()
        
        # Base probability on days left
        if days_left < 0:
            base_prob = 0.1  # Overdue tasks have low probability
        elif days_left == 0:
            base_prob = 0.3  # Due today
        elif days_left <= 2:
            base_prob = 0.5  # At risk
        elif days_left <= 7:
            base_prob = 0.7  # Due within week
        else:
            base_prob = 0.9  # Plenty of time
        
        # Adjust based on priority
        priority_multiplier = {
            'high': 1.1,
            'medium': 1.0,
            'low': 0.9
        }
        
        final_prob = base_prob * priority_multiplier.get(self.priority, 1.0)
        return min(1.0, max(0.0, final_prob))  # Clamp between 0-1

    def delay_prediction(self):
        """
        Predict likelihood of delay based on:
        - Days until due date
        - Priority level
        - Current status
        """
        if self.completed:
            return 0.0  # Already completed
        
        days_left = self.days_until_due()
        
        if days_left < 0:
            return 1.0  # Already delayed
        elif days_left == 0:
            return 0.8  # High risk of delay today
        elif days_left <= 2:
            return 0.6  # Moderate risk
        elif days_left <= 7:
            return 0.3  # Low risk
        else:
            return 0.1  # Very low risk

    def risk_score(self):
        """
        Calculate overall risk score (0-100)
        Higher score = higher risk
        """
        if self.completed:
            return 0

        days_left = self.days_until_due()
        base_score = 0

        # Days-based risk using constants
        if days_left < 0:
            base_score = OVERDUE_RISK  # Overdue
        elif days_left == 0:
            base_score = TODAY_RISK
        elif days_left == 1:
            base_score = TOMORROW_RISK
        elif days_left == 2:
            base_score = DAY_AFTER_RISK
        elif days_left <= 7:
            base_score = WEEK_RISK
        else:
            base_score = DEFAULT_RISK

        # Priority adjustment using constants
        final_score = base_score + PRIORITY_ADJUSTMENTS.get(self.priority, 0)
        return max(0, min(100, final_score))  # Clamp between 0-100

    def get_status(self):
        """Get human-readable status"""
        if self.completed:
            if self.is_delayed():
                return "Completed (Delayed)"
            return "Completed"
        elif self.is_delayed():
            return "Overdue"
        elif self.is_at_risk():
            return "At Risk"
        else:
            return "Pending"
