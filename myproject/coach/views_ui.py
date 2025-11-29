# coach/views_ui.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .group_a_client import get_daily_income, fallback_mock_data
from .models import SavedGoal, AdviceCard, CoachingSettings
from accounts.models import Income, CashEntry
from django.db.models import Sum
from datetime import date, timedelta

@login_required
def dashboard_page(request):
    """
    Render server-side dashboard with:
    - expense analysis summary (30 days)
    - low-income check
    - recent advice preview
    - recent incomes/cash (optional)
    """
    # Expense analysis (30 days)
    since = date.today() - timedelta(days=30)
    incomes_qs = Income.objects.filter(user=request.user, date__gte=since)
    cash_qs = CashEntry.objects.filter(user=request.user, date__gte=since)

    total_income = float(incomes_qs.aggregate(Sum('amount'))['amount__sum'] or 0)
    total_cash_income = float(cash_qs.filter(is_income=True).aggregate(Sum('amount'))['amount__sum'] or 0)
    total_expenses = float(cash_qs.filter(is_income=False).aggregate(Sum('amount'))['amount__sum'] or 0)
    net_income = total_income + total_cash_income
    expense_ratio = (total_expenses / net_income) if net_income > 0 else None

    # low income check using CoachingSettings + daily incomes
    daily = get_daily_income(request.user)
    used_fallback = False
    if not daily:
        daily = fallback_mock_data()
        used_fallback = True

    totals = sorted(daily.items(), key=lambda x: x[0])
    totals_only = [v for (_, v) in totals]
    last_three = totals_only[-3:] if len(totals_only) >= 3 else totals_only
    avg_recent = sum(last_three) / len(last_three) if last_three else 0
    settings_obj, _ = CoachingSettings.objects.get_or_create(user=request.user)
    low_status = "LOW" if avg_recent < settings_obj.low_income_threshold else "OK"

    # recent advice preview (3)
    recent_advice = AdviceCard.objects.filter(user=request.user).order_by('-created_at')[:3]

    context = {
        "total_income": round(net_income,2),
        "total_expenses": round(total_expenses,2),
        "expense_ratio": round(expense_ratio,2) if expense_ratio is not None else None,
        "avg_recent": round(avg_recent,2),
        "low_status": low_status,
        "recent_advice": recent_advice,
        "used_fallback": used_fallback,
    }
    return render(request, "coach/dashboard.html", context)


@login_required
def advice_page(request):
    """
    List advice cards. Allow marking as read (AJAX POST to /coach/ui/advice/mark_read/)
    """
    cards = AdviceCard.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "coach/advice.html", {"cards": cards})


@login_required
def mark_advice_read(request):
    """
    POST endpoint called from JS to mark a card read. Expects 'card_id' in POST.
    Returns JSON success; for simplicity this view redirects for non-AJAX.
    """
    if request.method != "POST":
        return redirect("coach:advice_ui")
    card_id = request.POST.get("card_id")
    if not card_id:
        messages.error(request, "Missing card id.")
        return redirect("coach:advice_ui")
    try:
        card = AdviceCard.objects.get(id=card_id, user=request.user)
        card.read = True
        card.save()
        # If AJAX, return simple JSON
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            from django.http import JsonResponse
            return JsonResponse({"ok": True})
        messages.success(request, "Marked read")
    except AdviceCard.DoesNotExist:
        messages.error(request, "Card not found")
    return redirect("coach:advice_ui")


@login_required
def heatmap_page(request):
    """
    Uses the same logic as weekly_heatmap API. Renders a simple heatmap table.
    """
    weeks = int(request.GET.get("weeks", 4))
    since = date.today() - timedelta(weeks=weeks)
    daily = get_daily_income(request.user)
    # filter and convert keys to date objects
    filtered = { (d if isinstance(d, date) else date.fromisoformat(str(d))): amt
                 for d, amt in daily.items() if (d if isinstance(d, date) else date.fromisoformat(str(d))) >= since }
    weekday_totals = {0:0,1:0,2:0,3:0,4:0,5:0,6:0}
    raw = []
    for d, amt in filtered.items():
        weekday_totals[d.weekday()] += amt
        raw.append({"date": str(d), "amount": amt})
    names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    weekdays = {names[k]: round(v,2) for k,v in weekday_totals.items()}
    return render(request, "coach/heatmap.html", {"weekdays": weekdays, "raw": raw})


@login_required
def goals_page(request):
    """
    GET -> show goals and the form to add.
    POST -> create a new goal (regular form POST)
    """
    if request.method == "POST":
        name = request.POST.get("name")
        target = request.POST.get("target_amount")
        deadline = request.POST.get("deadline") or None
        if not name or not target:
            messages.error(request, "Please provide a name and target amount.")
        else:
            try:
                g = SavedGoal.objects.create(
                    user=request.user,
                    name=name,
                    target_amount=float(target),
                    deadline=deadline
                )
                messages.success(request, f"Goal '{g.name}' created.")
                return redirect("coach:goals_ui")
            except Exception as e:
                messages.error(request, f"Error creating goal: {e}")
    goals = SavedGoal.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "coach/goals.html", {"goals": goals})
