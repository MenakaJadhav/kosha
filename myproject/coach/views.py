# coach/views.py
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.http import require_GET, require_http_methods
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta, date
import statistics

from .models import CoachingSettings, SavedGoal, AdviceCard
from .group_a_client import get_daily_income, get_transactions, fallback_mock_data
from accounts.models import Income, CashEntry  # direct access if needed

CACHE_TIMEOUT = 60  # seconds, tweak as needed

# --------- Health (keep) ----------
def health(request):
    return JsonResponse({"status": "ok", "module": "coach"})


# --------- Low income alert (cache it) ----------
@login_required
@require_GET
def low_income_alert(request):
    cache_key = f"low_income:{request.user.id}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    data = get_daily_income(request.user)
    used_fallback = False
    if not data:
        data = fallback_mock_data()
        used_fallback = True

    # sort by date and compute average of last 3 days
    items = sorted(data.items(), key=lambda x: x[0])
    totals = [v for (_, v) in items]
    if not totals:
        resp = {"status": "no_data", "message": "No income data"}
        cache.set(cache_key, resp, CACHE_TIMEOUT)
        return JsonResponse(resp)

    last_three = totals[-3:] if len(totals) >= 3 else totals
    avg_recent = sum(last_three) / len(last_three)

    settings_obj, _ = CoachingSettings.objects.get_or_create(user=request.user)
    threshold = settings_obj.low_income_threshold

    status = "low_income_warning" if avg_recent < threshold else "normal"
    resp = {
        "status": status,
        "average_recent": round(avg_recent, 2),
        "threshold": threshold,
        "data_points": len(totals),
        "used_fallback": used_fallback
    }
    cache.set(cache_key, resp, CACHE_TIMEOUT)
    return JsonResponse(resp)


# --------- Expense Analysis ----------
@login_required
@require_GET
def expense_analysis(request):
    """
    Returns:
      - total_income (sum over period)
      - total_cash_income
      - total_expenses (cash entries where is_income=False)
      - expense_ratio = expenses / income
      - top expense descriptions
    Optional query params:
      - days=30 (analysis window)
    """
    days = int(request.GET.get("days", 30))
    cache_key = f"expense_analysis:{request.user.id}:{days}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    # window
    since = date.today() - timedelta(days=days)
    incomes_qs = Income.objects.filter(user=request.user, date__gte=since)
    cash_qs = CashEntry.objects.filter(user=request.user, date__gte=since)

    total_income = float(incomes_qs.aggregate(Sum('amount'))['amount__sum'] or 0)
    total_cash_income = float(cash_qs.filter(is_income=True).aggregate(Sum('amount'))['amount__sum'] or 0)
    total_expenses = float(cash_qs.filter(is_income=False).aggregate(Sum('amount'))['amount__sum'] or 0)
    # include incomes as part of total income (already done)
    net_income = total_income + total_cash_income

    expense_ratio = (total_expenses / net_income) if net_income > 0 else None

    # top expense descriptions
    descs = cash_qs.filter(is_income=False).values('description').annotate(total=Sum('amount')).order_by('-total')[:5]
    top_expenses = [{"description": d['description'] or "unknown", "amount": float(d['total'])} for d in descs]

    result = {
        "days": days,
        "total_income": round(net_income, 2),
        "total_cash_income": round(total_cash_income, 2),
        "total_expenses": round(total_expenses, 2),
        "expense_ratio": round(expense_ratio, 2) if expense_ratio is not None else None,
        "top_expenses": top_expenses
    }
    cache.set(cache_key, result, CACHE_TIMEOUT)
    return JsonResponse(result)


# --------- Advice feed ----------
@login_required
@require_GET
def advice_feed(request):
    """
    Return recent advice cards for the user. Optional ?unread_only=1
    """
    unread_only = request.GET.get("unread_only") == "1"
    qs = AdviceCard.objects.filter(user=request.user)
    if unread_only:
        qs = qs.filter(read=False)
    cards = []
    for c in qs[:50]:
        cards.append({
            "id": c.id,
            "title": c.title,
            "body": c.body,
            "tag": c.tag,
            "created_at": c.created_at,
            "read": c.read,
            "meta": c.meta
        })
    return JsonResponse({"cards": cards})


# --------- Goals endpoints (simple) ----------
@login_required
@require_http_methods(["GET","POST"])
def goals_list_create(request):
    if request.method == "GET":
        qs = SavedGoal.objects.filter(user=request.user).order_by('-created_at')
        data = []
        for g in qs:
            data.append({
                "id": g.id,
                "name": g.name,
                "target_amount": g.target_amount,
                "current_amount": g.current_amount,
                "deadline": g.deadline,
                "progress": round(g.progress(),2)
            })
        return JsonResponse({"goals": data})
    else:  # POST create
        import json
        body = json.loads(request.body.decode() or "{}")
        name = body.get("name")
        target = body.get("target_amount")
        deadline = body.get("deadline")
        if not name or not target:
            return HttpResponseBadRequest("name and target_amount required")
        g = SavedGoal.objects.create(user=request.user, name=name, target_amount=float(target),
                                     deadline=deadline)
        return JsonResponse({"id": g.id, "name": g.name})


@login_required
@require_http_methods(["GET","PUT","DELETE"])
def goal_detail(request, pk):
    try:
        g = SavedGoal.objects.get(id=pk, user=request.user)
    except SavedGoal.DoesNotExist:
        return JsonResponse({"error":"not found"}, status=404)

    if request.method == "GET":
        return JsonResponse({
            "id": g.id,
            "name": g.name,
            "target_amount": g.target_amount,
            "current_amount": g.current_amount,
            "deadline": g.deadline,
            "progress": round(g.progress(), 2)
        })
    elif request.method == "DELETE":
        g.delete()
        return JsonResponse({"deleted": True})
    else:  # PUT update
        import json
        data = json.loads(request.body.decode() or "{}")
        g.name = data.get("name", g.name)
        g.target_amount = float(data.get("target_amount", g.target_amount))
        g.current_amount = float(data.get("current_amount", g.current_amount))
        g.deadline = data.get("deadline", g.deadline)
        g.save()
        return JsonResponse({"updated": True})


# --------- Emergency buffer calculator ----------
@login_required
@require_GET
def emergency_buffer(request):
    """
    Calculates recommended emergency buffer = average monthly expense * months_buffer
    months_buffer is from settings or default 3.
    """
    months = int(request.GET.get("months", 3))
    # compute avg monthly expense from cash entries (expenses only)
    since = date.today() - timedelta(days=90)  # 3 months window
    cash_qs = CashEntry.objects.filter(user=request.user, is_income=False, date__gte=since)
    total_expenses_90 = float(cash_qs.aggregate(Sum('amount'))['amount__sum'] or 0)
    avg_monthly = (total_expenses_90 / 3.0) if total_expenses_90 else 0
    recommended = avg_monthly * months
    return JsonResponse({
        "avg_monthly_expense": round(avg_monthly,2),
        "months": months,
        "recommended_buffer": round(recommended,2)
    })


# --------- Weekly earnings heatmap ----------
@login_required
@require_GET
def weekly_heatmap(request):
    """
    Returns earnings aggregated by weekday for last N weeks.
    Output format:
      {"weekdays": {"Mon": total, ...}, "raw": [{date: total}, ...]}
    """
    weeks = int(request.GET.get("weeks", 4))
    since = date.today() - timedelta(weeks=weeks)
    daily = get_daily_income(request.user)
    # filter by date >= since
    filtered = {d: amt for d, amt in daily.items() if (d if isinstance(d, date) else date.fromisoformat(str(d))) >= since}
    # weekday aggregation 0-Mon .. 6-Sun
    weekday_totals = {0:0,1:0,2:0,3:0,4:0,5:0,6:0}
    raw = []
    for d, amt in filtered.items():
        dobj = d if isinstance(d, date) else date.fromisoformat(str(d))
        weekday_totals[dobj.weekday()] += amt
        raw.append({"date": str(dobj), "amount": amt})
    # map to names
    names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    return JsonResponse({
        "weekdays": {names[k]: round(v,2) for k,v in weekday_totals.items()},
        "raw": raw
    })
