"""
First-deploy data setup, safe to run on every start (it's in the Procfile).

- Reading plans are seeded only while the database has NO plans. Some plan
  seeders delete and replace older plans, so re-running them later would wipe
  users' plan progress.
- The daily verse sample is loaded for the current month only while there are
  NO saved verses, so later months fall through to the live verse feed.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from journal.models import DailyVerse, ReadingPlan

PLAN_SEEDERS = ["seed_plans", "seed_chronological", "seed_mcheyne", "seed_nt_psalms_proverbs"]


class Command(BaseCommand):
    help = "Seed reading plans and a month of daily verses on a fresh database"

    def handle(self, *args, **opts):
        if ReadingPlan.objects.exists():
            self.stdout.write("Reading plans already present — skipping plan seeding.")
        else:
            # All-or-nothing: a half-seeded database would be skipped next time.
            with transaction.atomic():
                for name in PLAN_SEEDERS:
                    self.stdout.write(f"Running {name}…")
                    call_command(name, stdout=self.stdout)

        if DailyVerse.objects.exists():
            self.stdout.write("Daily verses already present — skipping verse seeding.")
        else:
            call_command("seed_daily_verses", stdout=self.stdout)
