# coach/management/commands/smoke_test.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Income, CashEntry
from coach.models import AdviceCard, CoachingSettings
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = "Run smoke test: seed small data for a user, run agent, check advice"

    def handle(self, *args, **options):
        u, created = User.objects.get_or_create(username='smoketest', defaults={'email': 'smoke@example.com'})
        if created:
            u.set_password('smoke123')
            u.save()
        today = date.today()
        Income.objects.filter(user=u).delete()
        CashEntry.objects.filter(user=u).delete()
        Income.objects.create(user=u, amount=100, date=today - timedelta(days=2), income_type='personal')
        Income.objects.create(user=u, amount=100, date=today - timedelta(days=1), income_type='personal')
        CashEntry.objects.create(user=u, amount=400, date=today - timedelta(days=1), description='big_spend', is_income=False)

        cs, _ = CoachingSettings.objects.get_or_create(user=u)
        cs.low_income_threshold = 500
        cs.save()

        from django.core.management import call_command
        call_command('run_coach_agent')

        count = AdviceCard.objects.filter(user=u).count()
        self.stdout.write(self.style.SUCCESS(f"smoke_test advice count for user 'smoketest': {count}"))
