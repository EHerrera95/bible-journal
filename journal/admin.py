from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from .models import ReadingPlan, PlanDay, Profile, JournalEntry, BiblePassage, ReadingRecord, PlanDayCompletion


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
        text = obj.scripture or ""
        return text[:80] + "…" if len(text) > 80 else text
    scripture_preview.short_description = "Scripture (preview)"


class ReadingRecordInline(admin.TabularInline):
    model            = ReadingRecord
    extra            = 0
    fields           = ("book_id", "chapter", "start_verse", "end_verse", "date_read", "source")
    show_change_link = True


# ── ReadingPlan ───────────────────────────────────────────────────────────────

@admin.register(ReadingPlan)
class ReadingPlanAdmin(admin.ModelAdmin):
    list_display  = ("name", "day_count", "needs_key_verses", "description")
    search_fields = ("name",)
    inlines       = [PlanDayInline]

    def day_count(self, obj):
        return obj.days.count()
    day_count.short_description = "# Days"

    def needs_key_verses(self, obj):
        """How many days still have a default :1 key verse."""
        defaulted = obj.days.filter(key_verse_ref__endswith=":1").count()
        total = obj.days.count()
        if defaulted == 0:
            return format_html('<span style="color:#2e7d32;">✓ All set</span>')
        return format_html(
            '<span style="color:#b5862e;">{} / {} need updating</span>',
            defaulted, total
        )
    needs_key_verses.short_description = "Key Verses"


# ── PlanDay ───────────────────────────────────────────────────────────────────

class KeyVerseStatusFilter(admin.SimpleListFilter):
    """Filter PlanDays by whether their key verse looks like a default (:1)."""
    title        = "Key Verse Status"
    parameter_name = "kv_status"

    def lookups(self, request, model_admin):
        return (
            ("default", "⚠ Still default (:1)"),
            ("set",     "✓ Manually set"),
        )

    def queryset(self, request, queryset):
        if self.value() == "default":
            return queryset.filter(key_verse_ref__endswith=":1")
        if self.value() == "set":
            return queryset.exclude(key_verse_ref__endswith=":1")
        return queryset


@admin.register(PlanDay)
class PlanDayAdmin(admin.ModelAdmin):
    list_display   = (
        "plan", "day_number", "passages",
        "key_verse_display", "kv_status_icon", "entry_count",
    )
    list_display_links = ("day_number", "passages")
    list_filter    = ("plan", KeyVerseStatusFilter)
    search_fields  = ("passages", "key_verse_ref")
    ordering       = ("plan", "day_number")

    # ── Enable inline editing of key_verse_ref directly from the list ────────
    list_editable  = ("key_verse_display_edit",) if False else ()  # placeholder

    fieldsets = (
        ("Reading", {
            "fields": ("plan", "day_number", "passages"),
        }),
        ("Key Verse", {
            "fields": ("key_verse_ref",),
            "description": (
                "The key verse is shown to users on the Today dashboard and "
                "in journal prompts. Format: <strong>Book Chapter:Verse</strong> "
                "— e.g. <em>John 3:16</em> or <em>Romans 8:28</em>."
            ),
        }),
    )

    # ── Custom columns ────────────────────────────────────────────────────────

    def key_verse_display(self, obj):
        """Show the key verse with a subtle edit hint."""
        return obj.key_verse_ref or "—"
    key_verse_display.short_description = "Key Verse"
    key_verse_display.admin_order_field = "key_verse_ref"

    def kv_status_icon(self, obj):
        """Traffic-light indicator: default (:1) vs manually set."""
        if obj.key_verse_ref and obj.key_verse_ref.endswith(":1"):
            return format_html(
                '<span title="Defaulted to :1 — consider updating" '
                'style="color:#b5862e; font-size:1rem;">⚠</span>'
            )
        if obj.key_verse_ref:
            return format_html(
                '<span title="Key verse set" '
                'style="color:#2e7d32; font-size:1rem;">✓</span>'
            )
        return format_html('<span style="color:#999;">—</span>')
    kv_status_icon.short_description = "✓"

    def entry_count(self, obj):
        return obj.journal_entries.count()
    entry_count.short_description = "Entries"

    # ── Bulk action: reset to :1 defaults (useful if you want to start over) ─

    actions = ["flag_for_review", "bulk_edit_hint"]

    def flag_for_review(self, request, queryset):
        """Reset selected key verses to a blank value so they stand out."""
        updated = queryset.update(key_verse_ref="")
        self.message_user(
            request,
            f"{updated} key verse(s) cleared — they'll show as ⚠ for your attention.",
        )
    flag_for_review.short_description = "Clear key verse (flag for manual update)"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("plan")


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

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.source == ReadingRecord.SOURCE_JOURNAL:
            return ("journal_entry", "source")
        return ()

    def whole_chapter_flag(self, obj):
        return obj.is_whole_chapter()
    whole_chapter_flag.boolean = True
    whole_chapter_flag.short_description = "Whole Chapter?"

    actions = ["mark_as_manual"]

    def mark_as_manual(self, request, queryset):
        updated = queryset.update(source=ReadingRecord.SOURCE_MANUAL)
        self.message_user(request, f"{updated} record(s) updated to manual source.")
    mark_as_manual.short_description = "Mark selected as manually added"

@admin.register(PlanDayCompletion)
class PlanDayCompletionAdmin(admin.ModelAdmin):
    list_display    = ("user", "plan_day", "source", "completed_at", "journal_entry")
    list_filter     = ("source", "plan_day__plan")
    search_fields   = ("user__username",)
    raw_id_fields   = ("user", "plan_day", "journal_entry")
    ordering        = ("-completed_at",)
    readonly_fields = ("completed_at",)

# ── Daily verse & push ───────────────────────────────────────────────────────

from .models import DailyVerse, PushSubscription  # noqa: E402


@admin.register(DailyVerse)
class DailyVerseAdmin(admin.ModelAdmin):
    list_display  = ("date", "reference", "translation", "source")
    list_filter   = ("source", "translation")
    search_fields = ("reference", "text")
    date_hierarchy = "date"


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display    = ("user", "created_at", "user_agent")
    readonly_fields = ("endpoint", "p256dh", "auth", "user_agent", "created_at")
