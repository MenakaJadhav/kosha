from django.db import models
from django.contrib.auth.models import User

class Income(models.Model):
    TYPE_CHOICES = (
        ('business', 'Business'),
        ('personal', 'Personal'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    date = models.DateField()
    income_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.amount} on {self.date}"

class CashEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    amount = models.FloatField()
    date = models.DateField()
    is_income = models.BooleanField(default=True)  # True = income, False = expense

    def __str__(self):
        return f"{self.description} - {self.amount}"
