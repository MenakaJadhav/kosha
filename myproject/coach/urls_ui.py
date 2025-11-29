# coach/urls_ui.py
from django.urls import path
from . import views_ui

app_name = "coach"

urlpatterns = [
    path('', views_ui.dashboard_page, name='dashboard_ui'),         # optional root
    path('dashboard/', views_ui.dashboard_page, name='dashboard'),  # keep name 'dashboard' used by other templates
    path('advice/', views_ui.advice_page, name='advice_ui'),
    path('advice/mark-read/', views_ui.mark_advice_read, name='mark_read'),
    path('heatmap/', views_ui.heatmap_page, name='heatmap_ui'),
    path('goals/', views_ui.goals_page, name='goals_ui'),
]
