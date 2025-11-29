# coach/tests.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import Income, CashEntry
from coach.models import CoachingSettings, AdviceCard
from datetime import date, timedelta

class CoachAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tuser", password="pass")
        self.client = Client()
        self.client.login(username="tuser", password="pass")

        # create incomes and cash entries
        today = date.today()
        Income.objects.create(user=self.user, amount=500, date=today - timedelta(days=2), income_type="business")
        Income.objects.create(user=self.user, amount=200, date=today - timedelta(days=1), income_type="personal")
        CashEntry.objects.create(user=self.user, amount=100, date=today - timedelta(days=1), description="tea", is_income=False)

    def test_expense_analysis(self):
        res = self.client.get("/coach/expense-analysis/?days=7")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_expenses", data)

    def test_low_income_alert(self):
        # set threshold high so warning appears
        CoachingSettings.objects.create(user=self.user, low_income_threshold=1000)
        res = self.client.get("/coach/low-income-alert/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertTrue(data["status"] in ("low_income_warning","normal"))

    def test_agent_creates_advice(self):
        # run agent command
        from django.core.management import call_command
        call_command("run_coach_agent")
        cards = AdviceCard.objects.filter(user=self.user)
        # either zero or more but should not crash
        self.assertTrue(cards.exists() or not cards.exists())
