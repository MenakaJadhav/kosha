# coach/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health),
    path('low-income-alert/', views.low_income_alert),

    path('expense-analysis/', views.expense_analysis),
    path('advice/', views.advice_feed),

    path('goals/', views.goals_list_create),
    path('goals/<int:pk>/', views.goal_detail),

    path('buffer/', views.emergency_buffer),
    path('heatmap/', views.weekly_heatmap),
]
