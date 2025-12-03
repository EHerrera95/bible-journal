from django.contrib import admin
from .models import ReadingPlan, PlanDay, Profile, JournalEntry, BiblePassage


@admin.register(ReadingPlan)
class ReadingPlanAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PlanDay)
class PlanDayAdmin(admin.ModelAdmin):
    list_display = ("plan", "day_number", "passages", "key_verse_ref")
    list_filter = ("plan",)
    ordering = ("plan", "day_number")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "reading_plan", "plan_start_date")
    list_filter = ("reading_plan",)


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "entry_date", "plan_day", "created_at")
    list_filter = ("user", "entry_date", "plan_day")
    search_fields = ("user__username", "scripture", "observation")


@admin.register(BiblePassage)
class BiblePassageAdmin(admin.ModelAdmin):
    list_display = ("reference",)
    search_fields = ("reference",)

