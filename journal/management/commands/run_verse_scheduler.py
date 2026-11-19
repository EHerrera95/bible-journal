"""
Run send_daily_verse every few minutes, forever. Started alongside the web
server in the Procfile so no separate cron service is needed.

    python manage.py run_verse_scheduler --every 15
"""
import time
import traceback

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import close_old_connections


class Command(BaseCommand):
    help = "Loop: send due daily-verse notifications every N minutes"

    def add_arguments(self, parser):
        parser.add_argument("--every", type=int, default=15, help="minutes between runs")

    def handle(self, *args, **opts):
        interval = max(opts["every"], 1) * 60
        self.stdout.write(f"Verse scheduler started (every {opts['every']} min).")
        while True:
            try:
                close_old_connections()
                call_command("send_daily_verse", stdout=self.stdout, stderr=self.stderr)
            except Exception:  # never let one bad run stop the loop
                self.stderr.write(traceback.format_exc())
            finally:
                close_old_connections()
            self.stdout.flush()
            time.sleep(interval)
