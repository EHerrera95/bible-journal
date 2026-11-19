# journal/management/commands/backfill_completions.py
#
# Run with:  python manage.py backfill_completions
#
# Finds every plan-type JournalEntry that has a plan_day linked but no
# PlanDayCompletion record, and creates the missing completion records.
# Safe to run multiple times — uses get_or_create throughout.

from django.core.management.base import BaseCommand
from journal.models import JournalEntry, PlanDayCompletion


class Command(BaseCommand):
    help = (
        "Backfill PlanDayCompletion records for existing plan-linked "
        "journal entries that predate the schedule feature."
    )

    def handle(self, *args, **kwargs):
        self.stdout.write("Scanning for plan journal entries missing completion records…")

        # All plan-type entries that have a plan_day
        entries = (
            JournalEntry.objects
            .filter(
                journal_type=JournalEntry.JOURNAL_TYPE_PLAN,
                plan_day__isnull=False,
            )
            .select_related("user", "plan_day")
        )

        created_count  = 0
        existing_count = 0

        for entry in entries:
            obj, created = PlanDayCompletion.objects.get_or_create(
                user=entry.user,
                plan_day=entry.plan_day,
                defaults={
                    "source":        PlanDayCompletion.SOURCE_JOURNAL,
                    "journal_entry": entry,
                },
            )
            if created:
                created_count += 1
            else:
                # If the completion exists but has no journal_entry, link it
                if obj.journal_entry is None:
                    obj.journal_entry = entry
                    obj.source        = PlanDayCompletion.SOURCE_JOURNAL
                    obj.save(update_fields=["journal_entry", "source"])
                existing_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Done.\n"
            f"  Completion records created:  {created_count}\n"
            f"  Already existed (skipped):   {existing_count}\n"
            f"  Total entries scanned:       {entries.count()}\n"
        ))
