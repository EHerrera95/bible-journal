from django.db import models
from django.contrib.auth.models import User
from datetime import date


class ReadingPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class PlanDay(models.Model):
    plan = models.ForeignKey(
        ReadingPlan,
        on_delete=models.CASCADE,
        related_name="days"
    )
    day_number = models.PositiveIntegerField()
    passages = models.CharField(max_length=255)      # e.g. "Genesis 1–3"
    key_verse_ref = models.CharField(max_length=100) # e.g. "Genesis 1:1"

    class Meta:
        unique_together = ("plan", "day_number")
        ordering = ["day_number"]

    def __str__(self):
        return f"{self.plan.name} - Day {self.day_number}"


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    reading_plan = models.ForeignKey(
        ReadingPlan,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profiles"
    )
    plan_start_date = models.DateField(null=True, blank=True)

    def current_day_number(self, today=None):
        if not self.reading_plan or not self.plan_start_date:
            return None
        today = today or date.today()
        delta = (today - self.plan_start_date).days
        return max(delta + 1, 1)

    def __str__(self):
        return f"Profile for {self.user.username}"


class BiblePassage(models.Model):
    """
    A free-text passage reference, used for freeform journal entries.
    e.g. "John 3:16-21"
    """
    reference = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.reference


class JournalEntry(models.Model):
    JOURNAL_TYPE_PLAN = "plan"
    JOURNAL_TYPE_FREE = "free"
    JOURNAL_TYPE_CHOICES = [
        (JOURNAL_TYPE_PLAN, "Reading Plan"),
        (JOURNAL_TYPE_FREE, "Free Form"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="journal_entries"
    )
    journal_type = models.CharField(
        max_length=10,
        choices=JOURNAL_TYPE_CHOICES,
        default=JOURNAL_TYPE_PLAN,
    )

    # Plan-based fields (used when journal_type == "plan")
    plan_day = models.ForeignKey(
        PlanDay,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="journal_entries"
    )

    # Free-form field (used when journal_type == "free")
    # Stores the user's typed or browsed passage reference, e.g. "John 3:16-21"
    passage_ref = models.CharField(max_length=200, blank=True, default="")

    entry_date = models.DateField()

    # Legacy M2M — kept for backward compatibility, not used in new flow
    passages = models.ManyToManyField(
        BiblePassage,
        related_name="journal_entries",
        blank=True,
    )

    # SOAP fields
    scripture    = models.TextField()
    observation  = models.TextField()
    application  = models.TextField()
    prayer       = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # One entry per user per day
        unique_together = ("user", "entry_date")
        ordering = ["-entry_date"]

    @property
    def display_passage(self):
        """Human-readable passage for both entry types."""
        if self.journal_type == self.JOURNAL_TYPE_FREE:
            return self.passage_ref or "—"
        if self.plan_day:
            return self.plan_day.passages
        return "—"

    def __str__(self):
        return f"{self.user.username} - {self.entry_date}"


class ReadingRecord(models.Model):
    """
    Tracks which parts of the Bible a user has read.

    - book_id:      3-letter book code from bible_data.py (e.g. "GEN", "JHN")
    - chapter:      1-indexed chapter number
    - start_verse:  null = entire chapter marked read
    - end_verse:    null = entire chapter marked read
    - source:       how this record was created
    """
    SOURCE_JOURNAL  = "journal"
    SOURCE_MANUAL   = "manual"
    SOURCE_CHOICES  = [
        (SOURCE_JOURNAL, "From journal entry"),
        (SOURCE_MANUAL,  "Marked manually"),
    ]

    user       = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reading_records"
    )
    book_id    = models.CharField(max_length=5)   # e.g. "GEN"
    chapter    = models.PositiveSmallIntegerField()
    start_verse = models.PositiveSmallIntegerField(null=True, blank=True)
    end_verse   = models.PositiveSmallIntegerField(null=True, blank=True)
    date_read   = models.DateField(default=date.today)
    source      = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default=SOURCE_MANUAL,
    )
    journal_entry = models.ForeignKey(
        JournalEntry,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reading_records"
    )

    class Meta:
        ordering = ["book_id", "chapter", "start_verse"]

    def is_whole_chapter(self):
        return self.start_verse is None and self.end_verse is None

    def __str__(self):
        if self.is_whole_chapter():
            return f"{self.user.username} — {self.book_id} {self.chapter} (whole chapter)"
        return f"{self.user.username} — {self.book_id} {self.chapter}:{self.start_verse}-{self.end_verse}"
