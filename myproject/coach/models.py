# coach/models.py
from django.db import models
from django.contrib.auth.models import User

class CoachingSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    low_income_threshold = models.FloatField(default=300)
    notifications_enabled = models.BooleanField(default=True)
    high_expense_ratio = models.FloatField(default=0.6)  # if expense / income > this, warn

    def __str__(self):
        return f"Settings for {self.user.username}"


class SavedGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    target_amount = models.FloatField()
    current_amount = models.FloatField(default=0)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def progress(self):
        if self.target_amount <= 0:
            return 0
        return (self.current_amount / self.target_amount) * 100

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class AdviceCard(models.Model):
    """
    A generated advice card (rule-based). Stored so frontend can show cards,
    and agent can avoid duplicates (by tag + user + recent timestamp).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    tag = models.CharField(max_length=50, blank=True)  # e.g., "low_income", "savings_tip"
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    meta = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.user.username}] {self.title}"
