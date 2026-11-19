"""
Send the daily verse notification to everyone whose chosen time has arrived.

Run it on a schedule (e.g. a Railway cron service every 15 minutes):

    python manage.py send_daily_verse

Each user gets at most one per local day, at or after their notify_time.
    --force          ignore the time / already-sent checks
    --user NAME      only this username
    --dry-run        show who would be notified
"""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.management.base import BaseCommand
from django.utils import timezone

from journal.models import Profile
from journal.push import push_configured, send_verse_to_user
from journal.verses import verse_for


class Command(BaseCommand):
    help = "Push today's verse to subscribed users whose notification time has arrived"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--user")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        if not push_configured() and not opts["dry_run"]:
            self.stderr.write("VAPID keys are not set — run generate_vapid_keys first.")
            return

        # Make sure today's verse is stored (fetches from the online feed once a day).
        verse_for(timezone.localdate(), allow_fetch=True)

        profiles = (Profile.objects
                    .filter(verse_notifications=True, user__push_subscriptions__isnull=False)
                    .select_related("user").distinct())
        if opts["user"]:
            profiles = profiles.filter(user__username=opts["user"])

        now_utc = timezone.now()
        sent_users = 0
        for profile in profiles:
            try:
                tz = ZoneInfo(profile.timezone)
            except (ZoneInfoNotFoundError, ValueError):
                tz = ZoneInfo("UTC")
            local_now = now_utc.astimezone(tz)
            local_day = local_now.date()

            due = (local_now.time() >= profile.notify_time
                   and profile.last_verse_push_date != local_day)
            if not (due or opts["force"]):
                continue

            verse = verse_for(local_day, allow_fetch=True)
            if opts["dry_run"]:
                self.stdout.write(f"would notify {profile.user.username}: {verse['reference']}")
                continue

            delivered = send_verse_to_user(profile.user, verse)
            if delivered:
                profile.last_verse_push_date = local_day
                profile.save(update_fields=["last_verse_push_date"])
                sent_users += 1
            self.stdout.write(f"{profile.user.username}: {delivered} device(s) — {verse['reference']}")

        self.stdout.write(self.style.SUCCESS(f"Done at {datetime.now():%H:%M}. Notified {sent_users} user(s)."))
