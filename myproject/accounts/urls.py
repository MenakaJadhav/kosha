from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name="signup"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),

    path('dashboard/', views.dashboard_view, name="dashboard"),

    path('income/add/', views.income_entry_view, name="income_entry"),
    path('income/history/', views.income_history_view, name="income_history"),
    path('income/variability/', views.income_variability_view, name="income_variability"),

    path('cash/add/', views.cash_entry_view, name="cash_entry"),
]
