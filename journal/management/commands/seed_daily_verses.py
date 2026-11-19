"""
Load the bundled 31-day verse sample into DailyVerse for a month.

    python manage.py seed_daily_verses                 # current month
    python manage.py seed_daily_verses --month 2026-12
    python manage.py seed_daily_verses --overwrite     # replace days already saved
"""
import calendar
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from journal.models import DailyVerse
from journal.verses import sample_for


class Command(BaseCommand):
    help = "Seed one month of daily verses from journal/data/daily_verses_sample.json"

    def add_arguments(self, parser):
        parser.add_argument("--month", help="YYYY-MM (default: current month)")
        parser.add_argument("--overwrite", action="store_true", help="Replace verses already saved")

    def handle(self, *args, **opts):
        if opts["month"]:
            try:
                year, month = (int(x) for x in opts["month"].split("-"))
            except ValueError:
                raise CommandError("--month must look like 2026-12")
        else:
            t = date.today()
            year, month = t.year, t.month

        created = skipped = 0
        for d in range(1, calendar.monthrange(year, month)[1] + 1):
            day = date(year, month, d)
            if DailyVerse.objects.filter(date=day).exists() and not opts["overwrite"]:
                skipped += 1
                continue
            DailyVerse.objects.update_or_create(date=day, defaults=sample_for(day))
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"{calendar.month_name[month]} {year}: {created} verses saved, {skipped} already present."
        ))
