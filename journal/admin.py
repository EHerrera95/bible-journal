from django.contrib import admin
from django.utils.html import format_html
from .models import ReadingPlan, PlanDay, Profile, JournalEntry, BiblePassage, ReadingRecord


# ── Inlines ───────────────────────────────────────────────────────────────────

class PlanDayInline(admin.TabularInline):
    model            = PlanDay
    extra            = 1
    fields           = ("day_number", "passages", "key_verse_ref")
    ordering         = ("day_number",)
    show_change_link = True


class JournalEntryInline(admin.TabularInline):
    model            = JournalEntry
    extra            = 0
    fields           = ("entry_date", "journal_type", "passage_ref", "scripture_preview")
    readonly_fields  = ("entry_date", "scripture_preview")
    show_change_link = True

    def scripture_preview(self, obj):
        return (obj.scripture or "")[:80] + "…" if len(obj.scripture or "") > 80 else obj.scripture
    scripture_preview.short_description = "Scripture (preview)"


class ReadingRecordInline(admin.TabularInline):
    model            = ReadingRecord
    extra            = 0
    fields           = ("book_id", "chapter", "start_verse", "end_verse", "date_read", "source")
    show_change_link = True


# ── ReadingPlan ───────────────────────────────────────────────────────────────

@admin.register(ReadingPlan)
class ReadingPlanAdmin(admin.ModelAdmin):
    list_display  = ("name", "day_count", "description")
    search_fields = ("name",)
    inlines       = [PlanDayInline]

    def day_count(self, obj):
        return obj.days.count()
    day_count.short_description = "# Days"


# ── PlanDay ───────────────────────────────────────────────────────────────────

@admin.register(PlanDay)
class PlanDayAdmin(admin.ModelAdmin):
    list_display  = ("plan", "day_number", "passages", "key_verse_ref", "entry_count")
    list_filter   = ("plan",)
    search_fields = ("passages", "key_verse_ref")
    ordering      = ("plan", "day_number")

    def entry_count(self, obj):
        return obj.journal_entries.count()
    entry_count.short_description = "Journal Entries"


# ── Profile ───────────────────────────────────────────────────────────────────

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display   = ("user", "reading_plan", "plan_start_date", "current_day")
    list_filter    = ("reading_plan",)
    search_fields  = ("user__username",)
    raw_id_fields  = ("user",)

    def current_day(self, obj):
        return obj.current_day_number()
    current_day.short_description = "Current Day #"


# ── BiblePassage ──────────────────────────────────────────────────────────────

@admin.register(BiblePassage)
class BiblePassageAdmin(admin.ModelAdmin):
    list_display  = ("reference", "entry_count")
    search_fields = ("reference",)

    def entry_count(self, obj):
        return obj.journal_entries.count()
    entry_count.short_description = "Linked Entries"


# ── JournalEntry ──────────────────────────────────────────────────────────────

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display    = (
        "user", "entry_date", "journal_type", "passage_display",
        "scripture_preview", "created_at", "updated_at",
    )
    list_filter     = ("journal_type", "user", "plan_day__plan")
    search_fields   = ("user__username", "scripture", "observation", "passage_ref")
    date_hierarchy  = "entry_date"
    ordering        = ("-entry_date",)
    readonly_fields = ("created_at", "updated_at", "passage_display")
    raw_id_fields   = ("user", "plan_day")
    filter_horizontal = ("passages",)

    fieldsets = (
        ("Entry Info", {
            "fields": (
                "user", "journal_type", "entry_date",
                "plan_day", "passage_ref", "passage_display",
            ),
        }),
        ("SOAP", {
            "fields": ("scripture", "observation", "application", "prayer"),
        }),
        ("Legacy / Meta", {
            "classes": ("collapse",),
            "fields": ("passages", "created_at", "updated_at"),
        }),
    )

    def passage_display(self, obj):
        return obj.display_passage
    passage_display.short_description = "Resolved Passage"

    def scripture_preview(self, obj):
        text = obj.scripture or ""
        return text[:60] + "…" if len(text) > 60 else text
    scripture_preview.short_description = "Scripture"


# ── ReadingRecord ─────────────────────────────────────────────────────────────

@admin.register(ReadingRecord)
class ReadingRecordAdmin(admin.ModelAdmin):
    list_display   = (
        "user", "book_id", "chapter", "start_verse", "end_verse",
        "date_read", "source", "whole_chapter_flag",
    )
    list_filter    = ("source", "book_id", "user")
    search_fields  = ("user__username", "book_id")
    date_hierarchy = "date_read"
    ordering       = ("book_id", "chapter", "start_verse")
    raw_id_fields  = ("user", "journal_entry")

    fieldsets = (
        ("Who & When", {
            "fields": ("user", "date_read", "source", "journal_entry"),
        }),
        ("What", {
            "fields": ("book_id", "chapter", "start_verse", "end_verse"),
        }),
    )

    # Allow editing all fields except source-linked journal entry (read-only
    # when created from a journal save; editable when added manually)
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.source == ReadingRecord.SOURCE_JOURNAL:
            return ("journal_entry", "source")
        return ()

    def whole_chapter_flag(self, obj):
        return obj.is_whole_chapter()
    whole_chapter_flag.boolean = True
    whole_chapter_flag.short_description = "Whole Chapter?"

    # Quick action: mark selected records as manual source
    actions = ["mark_as_manual"]

    def mark_as_manual(self, request, queryset):
        updated = queryset.update(source=ReadingRecord.SOURCE_MANUAL)
        self.message_user(request, f"{updated} record(s) updated to manual source.")
    mark_as_manual.short_description = "Mark selected as manually added"
