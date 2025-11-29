# coach/management/commands/seed_demo_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Income, CashEntry
from coach.models import SavedGoal, CoachingSettings
from datetime import date, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = "Seed demo users + incomes/cash entries + goals (non-destructive)"

    def handle(self, *args, **options):
        demo_users = [
            {"username": "demo1", "email": "demo1@example.com", "password": "demo123"},
            {"username": "demo2", "email": "demo2@example.com", "password": "demo123"},
        ]

        for du in demo_users:
            u, created = User.objects.get_or_create(username=du["username"], defaults={"email": du["email"]})
            if created:
                u.set_password(du["password"])
                u.save()
                self.stdout.write(self.style.SUCCESS(f"Created user {u.username}"))

            cs, _ = CoachingSettings.objects.get_or_create(user=u)
            cs.low_income_threshold = 300.0
            cs.high_expense_ratio = 0.5
            cs.save()

            today = date.today()
            # incomes last 30 days
            for i in range(30):
                d = today - timedelta(days=i)
                base = 250 if d.weekday() < 5 else 150
                val = max(20, base + random.randint(-80, 150))
                Income.objects.update_or_create(user=u, date=d, defaults={"amount": val, "income_type": random.choice(['business','personal'])})

            # cash expenses (random)
            for i in range(30):
                d = today - timedelta(days=i)
                if random.random() < 0.6:
                    amt = random.randint(20, 500)
                    desc = random.choice(["groceries","transport","coffee","bills","shopping"])
                    CashEntry.objects.create(user=u, description=desc, amount=amt, date=d, is_income=False)

            SavedGoal.objects.get_or_create(user=u, name="Emergency fund", defaults={"target_amount": 5000})
            SavedGoal.objects.get_or_create(user=u, name="Vacation", defaults={"target_amount": 1500})

            self.stdout.write(self.style.SUCCESS(f"Seeded data for {u.username}"))

        self.stdout.write(self.style.SUCCESS("Demo seed completed."))
