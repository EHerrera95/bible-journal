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
    day_number = models.PositiveIntegerField()          # 1, 2, 3...
    passages = models.CharField(max_length=255)         # e.g. "Genesis 1–3"
    key_verse_ref = models.CharField(max_length=100)    # e.g. "Genesis 1:1"

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
        """
        Determine which day of the plan the user is on.
        Day 1 = plan_start_date
        """
        if not self.reading_plan or not self.plan_start_date:
            return None
        today = today or date.today()
        delta = (today - self.plan_start_date).days
        return max(delta + 1, 1)

    def __str__(self):
        return f"Profile for {self.user.username}"


class JournalEntry(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="journal_entries"
    )
    plan_day = models.ForeignKey(
        PlanDay,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="journal_entries"
    )
    entry_date = models.DateField()  # usually today's date

    # SOAP fields
    scripture = models.TextField()    # S
    observation = models.TextField()  # O
    application = models.TextField()  # A
    prayer = models.TextField()       # P

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "entry_date")
        ordering = ["-entry_date"]

    def __str__(self):
        return f"{self.user.username} - {self.entry_date}"
