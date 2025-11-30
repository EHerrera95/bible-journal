from django.urls import path
from . import views

urlpatterns = [
    path("today/", views.today_view, name="today"),
    path("journal/today/", views.journal_today_view, name="journal_today"),
    path("journal/history/", views.journal_history_view, name="journal_history"),
    ]
