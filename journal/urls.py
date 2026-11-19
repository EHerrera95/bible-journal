from django.urls import path
from . import views

urlpatterns = [
    path("",                                views.home_view,            name="home"),
    path("today/",                          views.today_view,           name="today"),

    # Reading plans
    path("plans/",                          views.plans_view,           name="plans"),
    path("plans/select/",                   views.select_plan_view,     name="select_plan"),

    # Plan schedule
    path("schedule/",                       views.schedule_view,        name="schedule"),
    path("schedule/mark/",                  views.mark_plan_day_view,   name="mark_plan_day"),

    # Journal entries
    path("journal/today/",                  views.journal_today_view,   name="journal_today"),
    path("journal/free/",                   views.journal_free_view,    name="journal_free"),
    path("journal/history/",               views.journal_history_view,  name="journal_history"),

    # Entry detail / edit / backfill — accepts any YYYY-MM-DD date
    path("journal/entry/<str:entry_date_str>/", views.journal_entry_view, name="journal_entry"),

    # Backfill shortcut: /journal/backfill/?date=2025-03-15
    path("journal/backfill/",              views.journal_backfill_view, name="journal_backfill"),

    # Bible progress & reading tracking
    path("progress/",                       views.progress_view,        name="progress"),
    path("mark-read/",                      views.mark_read_view,       name="mark_read"),

    # Daily verse + notifications
    path("verse/",                          views.verse_view,           name="verse"),
    path("settings/notifications/",         views.notifications_view,   name="notifications"),
    path("push/subscribe/",                 views.push_subscribe_view,  name="push_subscribe"),
    path("push/unsubscribe/",               views.push_unsubscribe_view, name="push_unsubscribe"),
    path("push/test/",                      views.push_test_view,       name="push_test"),

    # Mobile app (PWA) — must live at the site root
    path("manifest.webmanifest",            views.manifest_view,        name="manifest"),
    path("sw.js",                           views.service_worker_view,  name="service_worker"),

    # AJAX
    path("api/verse-count/",               views.verse_count_view,      name="verse_count"),
]
