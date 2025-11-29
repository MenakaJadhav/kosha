# coach/management/commands/run_coach_agent.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from coach.group_a_client import get_daily_income
from coach.models import CoachingSettings, AdviceCard
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = "Run the lightweight coach agent to generate advice cards"

    def handle(self, *args, **options):
        users = User.objects.all()
        for u in users:
            try:
                settings, _ = CoachingSettings.objects.get_or_create(user=u)
                daily = get_daily_income(u)
                if not daily:
                    continue

                # sorted totals
                items = sorted(daily.items(), key=lambda x: x[0])
                totals = [v for (_, v) in items]
                last7 = totals[-7:] if len(totals) >= 7 else totals
                if not last7:
                    continue
                avg7 = sum(last7) / len(last7)

                # low income advice
                if avg7 < settings.low_income_threshold:
                    recent = AdviceCard.objects.filter(
                        user=u, tag="low_income",
                        created_at__gte=date.today() - timedelta(days=2)
                    )
                    if not recent.exists():
                        AdviceCard.objects.create(
                            user=u,
                            title="Income is low recently",
                            body=(f"Your average income over the last {len(last7)} days is "
                                  f"{round(avg7,2)}, which is below your threshold of "
                                  f"{settings.low_income_threshold}. Consider reducing discretionary expenses or building a buffer."),
                            tag="low_income",
                            meta={"avg7": round(avg7,2)}
                        )

                # expense ratio check (30-day window)
                from accounts.models import Income, CashEntry
                from django.db.models import Sum
                since = date.today() - timedelta(days=30)
                total_income = float(Income.objects.filter(user=u, date__gte=since).aggregate(Sum('amount'))['amount__sum'] or 0)
                total_cash_income = float(CashEntry.objects.filter(user=u, is_income=True, date__gte=since).aggregate(Sum('amount'))['amount__sum'] or 0)
                total_expenses = float(CashEntry.objects.filter(user=u, is_income=False, date__gte=since).aggregate(Sum('amount'))['amount__sum'] or 0)
                net_income = total_income + total_cash_income

                if net_income > 0:
                    expense_ratio = total_expenses / net_income
                    if expense_ratio > settings.high_expense_ratio:
                        recent = AdviceCard.objects.filter(
                            user=u, tag="high_expense",
                            created_at__gte=date.today() - timedelta(days=3)
                        )
                        if not recent.exists():
                            AdviceCard.objects.create(
                                user=u,
                                title="Your expenses are high",
                                body=(f"Your spending is {round(expense_ratio*100,1)}% of your earnings over the last 30 days. "
                                      "Try cutting non-essential spending or set a small weekly limit."),
                                tag="high_expense",
                                meta={"expense_ratio": round(expense_ratio,3)}
                            )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error for user {u.username}: {e}"))

        self.stdout.write(self.style.SUCCESS("Agent run completed."))
