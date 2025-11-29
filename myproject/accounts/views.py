from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from .forms import SignupForm, LoginForm, IncomeForm, CashEntryForm
from .models import Income, CashEntry
import datetime
from django.db.models import Sum
from datetime import date, timedelta

# ------------------------------
# USER AUTH
# ------------------------------

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')

# ------------------------------
# DASHBOARD
# ------------------------------

@login_required
def dashboard_view(request):
    incomes = Income.objects.filter(user=request.user).order_by('-date')[:5]
    cash = CashEntry.objects.filter(user=request.user).order_by('-date')[:5]
    return render(request, 'accounts/dashboard.html', {
        'incomes': incomes,
        'cash': cash
    })

# ------------------------------
# INCOME
# ------------------------------

@login_required
def income_entry_view(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            return redirect('income_history')
    else:
        form = IncomeForm()
    return render(request, 'accounts/income_form.html', {'form': form})


@login_required
def income_history_view(request):
    incomes = Income.objects.filter(user=request.user).order_by('-date')
    return render(request, 'accounts/income_history.html', {'incomes': incomes})


@login_required
def income_variability_view(request):
    # ---------- STEP 1: Fetch Income + Cash entries ----------
    incomes = Income.objects.filter(user=request.user)
    cash_entries = CashEntry.objects.filter(user=request.user)  # includes both income and expenses

    if not incomes.exists() and not cash_entries.exists():
        return render(request, 'accounts/variability.html', {"msg": "No income or cash data available"})

    # ---------- STEP 2: Group by dates ----------
    # Get all unique dates from both incomes and cash entries
    income_dates = set(incomes.values_list('date', flat=True))
    cash_dates = set(cash_entries.values_list('date', flat=True))
    dates = income_dates.union(cash_dates)

    daily_totals = []
    net_values = []

    for d in dates:
        # sum of Income.amount on date d
        income_total = incomes.filter(date=d).aggregate(total=Sum('amount'))['total'] or 0

        # cash entries split by is_income flag
        cash_income_total = cash_entries.filter(date=d, is_income=True).aggregate(total=Sum('amount'))['total'] or 0
        cash_expense_total = cash_entries.filter(date=d, is_income=False).aggregate(total=Sum('amount'))['total'] or 0

        # net total = income + cash incomes - cash expenses
        net_total = (income_total + cash_income_total) - cash_expense_total

        # keep consistent key name 'total_income' to avoid breaking any templates that expect it,
        # but its value is now the net (income minus expenses)
        daily_totals.append({
            'date': d,
            'income_total': round(income_total, 2),
            'cash_income_total': round(cash_income_total, 2),
            'cash_expense_total': round(cash_expense_total, 2),
            'total_income': round(net_total, 2),   # preserved name for backward compatibility
        })

        net_values.append(net_total)

    # ---------- STEP 3: Calculate average net income ----------
    if net_values:
        avg_income = sum(net_values) / len(net_values)
    else:
        avg_income = 0

    # ---------- STEP 4: Render result ----------
    return render(request, 'accounts/variability.html', {
        'avg_income': round(avg_income, 2),
        'daily_totals': sorted(daily_totals, key=lambda x: x['date'], reverse=True)
    })

# ------------------------------
# CASH ENTRY
# ------------------------------

@login_required
def cash_entry_view(request):
    if request.method == 'POST':
        form = CashEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            return redirect('dashboard')
    else:
        form = CashEntryForm()
    return render(request, 'accounts/cash_entry.html', {'form': form})

@login_required
def income_history_view(request):
    incomes = Income.objects.filter(user=request.user).order_by("income_type", "-date")

    grouped_income = {}
    for entry in incomes:
        grouped_income.setdefault(entry.income_type, []).append(entry)

    cash_entries = CashEntry.objects.filter(user=request.user).order_by("-date")

    return render(request, "accounts/income_history.html", {
        "grouped_income": grouped_income,
        "cash_entries": cash_entries
    })

