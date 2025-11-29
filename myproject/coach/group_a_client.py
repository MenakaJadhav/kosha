# coach/group_a_client.py
from accounts.models import Income, CashEntry
from django.db.models import Sum

def get_daily_income(user):
    incomes = Income.objects.filter(user=user).values("date").annotate(total=Sum("amount"))
    cash = CashEntry.objects.filter(user=user, is_income=True).values("date").annotate(total=Sum("amount"))

    combined = {}
    for entry in incomes:
        d = entry["date"]
        combined[d] = combined.get(d, 0) + float(entry["total"] or 0)

    for entry in cash:
        d = entry["date"]
        combined[d] = combined.get(d, 0) + float(entry["total"] or 0)

    # return dict keyed by date objects -> totals
    return combined


def get_transactions(user):
    """
    Return two querysets/dicts for incomes and cash entries for more granular analysis.
    """
    incomes = list(Income.objects.filter(user=user).values("date", "amount", "income_type", "source"))
    cash = list(CashEntry.objects.filter(user=user).values("date", "amount", "description", "is_income"))
    return incomes, cash


def fallback_mock_data():
    return {
        # date strings are fine for fallback
        "2025-01-01": 500,
        "2025-01-02": 200,
        "2025-01-03": 700,
        "2025-01-04": 300,
    }
