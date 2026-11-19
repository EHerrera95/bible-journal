from datetime import date, timedelta, time as dtime
import json
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.templatetags.static import static
from django.utils import timezone as dj_tz
from django.views.decorators.cache import cache_control

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Profile, PlanDay, JournalEntry, ReadingRecord, ReadingPlan, PlanDayCompletion
from .forms import (
    JournalEntryForm, FreeJournalEntryForm,
    BackfillJournalEntryForm, MarkReadForm,
)
from .bible_data import BIBLE_BOOKS, BOOKS_BY_ID, OT_BOOKS, NT_BOOKS, verse_count
from .models import DailyVerse, PushSubscription
from .push import push_configured, send_verse_to_user
from .verses import verse_for


# ── Home ─────────────────────────────────────────────────────────────────────

def home_view(request):
    if request.user.is_authenticated:
        return redirect("today")
    return render(request, "journal/home.html")


# ── Today Dashboard ───────────────────────────────────────────────────────────

@login_required
def today_view(request):
    today     = date.today()
    yesterday = today - timedelta(days=1)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    has_plan   = bool(profile.reading_plan and profile.plan_start_date)

    plan_day   = None
    day_number = None
    preview_days = []  # 3-day strip for the today dashboard

    if has_plan:
        day_number = profile.current_day_number()
        plan_day   = (
            PlanDay.objects
            .filter(plan=profile.reading_plan, day_number=day_number)
            .first()
        )

        # Build yesterday / today / tomorrow preview strip
        completed_set = set(
            PlanDayCompletion.objects
            .filter(user=request.user, plan_day__plan=profile.reading_plan)
            .values_list("plan_day_id", flat=True)
        )
        for offset in (-1, 0, 1):
            dn  = day_number + offset
            if dn < 1:
                continue
            pd  = PlanDay.objects.filter(plan=profile.reading_plan, day_number=dn).first()
            if pd:
                # In calendar mode derive the date; in sequential mode show None
                if profile.is_sequential:
                    pd_date = None
                else:
                    pd_date = profile.plan_start_date + timedelta(days=dn - 1)
                preview_days.append({
                    "plan_day":   pd,
                    "day_number": dn,
                    "date":       pd_date,
                    "is_today":   offset == 0,
                    "is_past":    offset < 0,
                    "completed":  pd.id in completed_set,
                })

    today_entry = (
        JournalEntry.objects
        .filter(user=request.user, entry_date=today)
        .first()
    )
    yesterday_entry = (
        JournalEntry.objects
        .filter(user=request.user, entry_date=yesterday)
        .first()
    )

    context = {
        "today":           today,
        "has_plan":        has_plan,
        "plan_day":        plan_day,
        "day_number":      day_number,
        "today_entry":     today_entry,
        "yesterday_entry": yesterday_entry,
        "preview_days":    preview_days,
        "is_sequential":   profile.is_sequential if has_plan else False,
        "profile":         profile,
        "daily_verse":     verse_for(_user_local_date(profile)),
    }
    return render(request, "journal/today.html", context)


# ── Plan Selection ────────────────────────────────────────────────────────────

@login_required
def plans_view(request):
    from django.db.models import Count, Min
    profile, _ = Profile.objects.get_or_create(user=request.user)

    plans = ReadingPlan.objects.annotate(day_count=Count("days")).order_by("name")

    # Completion counts per plan
    completion_counts = dict(
        PlanDayCompletion.objects
        .filter(user=request.user)
        .values("plan_day__plan_id")
        .annotate(count=Count("id"))
        .values_list("plan_day__plan_id", "count")
    )

    # Earliest completion date per plan — used to reconstruct the original
    # start date when the user resumes a plan they previously left
    earliest_completion = dict(
        PlanDayCompletion.objects
        .filter(user=request.user)
        .values("plan_day__plan_id")
        .annotate(earliest=Min("completed_at"))
        .values_list("plan_day__plan_id", "earliest")
    )

    # Lowest completed day_number per plan — needed to back-calculate start date
    # start_date = earliest_completion_date - (lowest_completed_day_number - 1) days
    lowest_completed_day = {}
    for item in (
        PlanDayCompletion.objects
        .filter(user=request.user)
        .values("plan_day__plan_id")
        .annotate(min_day=Min("plan_day__day_number"))
    ):
        lowest_completed_day[item["plan_day__plan_id"]] = item["min_day"]

    from datetime import timedelta as _td
    today = date.today()

    plan_data = []
    for plan in plans:
        total     = plan.day_count
        completed = completion_counts.get(plan.id, 0)
        pct       = int(100 * completed / total) if total else 0
        is_active = profile.reading_plan_id == plan.id

        # Reconstruct original start date from earliest completion record
        # so Resume Plan pre-fills the right date instead of today
        original_start = None
        if completed > 0 and plan.id in earliest_completion:
            earliest_dt = earliest_completion[plan.id]
            min_day     = lowest_completed_day.get(plan.id, 1)
            # earliest completion was on day `min_day`, so start = that date - (min_day-1) days
            earliest_date = earliest_dt.date() if hasattr(earliest_dt, "date") else earliest_dt
            original_start = earliest_date - _td(days=min_day - 1)

        # For the active plan use the stored start date (user may have adjusted it)
        if is_active:
            original_start = profile.plan_start_date or original_start or today

        plan_data.append({
            "plan":           plan,
            "total":          total,
            "completed":      completed,
            "pct":            pct,
            "is_active":      is_active,
            "is_done":        pct == 100,
            "started":        completed > 0,
            "original_start": original_start,  # pre-fill date for Resume Plan
        })

    plan_data.sort(key=lambda p: (
        0 if p["is_active"] else
        1 if p["started"] and not p["is_done"] else
        2 if not p["started"] else
        3
    ))

    context = {
        "plan_data":    plan_data,
        "current_plan": profile.reading_plan,
        "current_mode": profile.plan_mode,
        "bible_books":  BIBLE_BOOKS,
        "profile":      profile,
        "today":        today,
    }
    return render(request, "journal/plans.html", context)


@login_required
@require_POST
def select_plan_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    plan_id    = request.POST.get("plan_id")
    book_id    = request.POST.get("book_id")
    start_date = request.POST.get("start_date") or str(date.today())
    plan_mode  = request.POST.get("plan_mode", Profile.PLAN_MODE_CALENDAR)

    # Validate mode value
    valid_modes = [Profile.PLAN_MODE_CALENDAR, Profile.PLAN_MODE_SEQUENTIAL]
    if plan_mode not in valid_modes:
        plan_mode = Profile.PLAN_MODE_CALENDAR

    try:
        start = date.fromisoformat(start_date)
    except ValueError:
        start = date.today()

    if book_id and not plan_id:
        book = BOOKS_BY_ID.get(book_id.upper())
        if not book:
            return redirect("plans")
        plan = _get_or_create_book_plan(book)
    elif plan_id:
        try:
            plan = ReadingPlan.objects.get(pk=plan_id)
        except ReadingPlan.DoesNotExist:
            return redirect("plans")
    else:
        return redirect("plans")

    profile.reading_plan    = plan
    profile.plan_start_date = start
    profile.plan_mode       = plan_mode
    profile.save()
    return redirect("today")


def _get_or_create_book_plan(book):
    plan_name = f"{book['name']} — Book by Book"
    plan, _   = ReadingPlan.objects.get_or_create(
        name=plan_name,
        defaults={"description": (
            f"Read the book of {book['name']} one chapter at a time. "
            f"{len(book['verses'])} days of focused study."
        )},
    )
    for ch_idx in range(1, len(book["verses"]) + 1):
        PlanDay.objects.get_or_create(
            plan=plan,
            day_number=ch_idx,
            defaults={
                "passages":      f"{book['name']} {ch_idx}",
                "key_verse_ref": f"{book['name']} {ch_idx}:1",
            },
        )
    return plan


# ── Plan-based Journal Entry ──────────────────────────────────────────────────

@login_required
def journal_today_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if not profile.reading_plan or not profile.plan_start_date:
        return redirect("today")

    today      = date.today()
    day_number = profile.current_day_number(today)
    plan_day   = (
        PlanDay.objects
        .filter(plan=profile.reading_plan, day_number=day_number)
        .first()
    )

    if not plan_day:
        return redirect("today")

    journal_entry = (
        JournalEntry.objects
        .filter(user=request.user, entry_date=today)
        .first()
    )

    if request.method == "POST":
        form = JournalEntryForm(request.POST, instance=journal_entry)
        if form.is_valid():
            entry              = form.save(commit=False)
            entry.user         = request.user
            entry.entry_date   = today
            entry.plan_day     = plan_day
            entry.journal_type = JournalEntry.JOURNAL_TYPE_PLAN
            entry.save()
            _ensure_completion(request.user, plan_day, entry)
            return redirect("today")
    else:
        form = JournalEntryForm(instance=journal_entry)

    context = {
        "form":       form,
        "today":      today,
        "plan_day":   plan_day,
        "day_number": day_number,
        "is_edit":    journal_entry is not None,
    }
    return render(request, "journal/journal_today.html", context)


# ── Free-form Journal Entry (today only) ─────────────────────────────────────

@login_required
def journal_free_view(request):
    today         = date.today()
    journal_entry = (
        JournalEntry.objects
        .filter(user=request.user, entry_date=today)
        .first()
    )

    prefill_ref = ""
    book_id     = request.GET.get("book", "")
    chapter     = request.GET.get("chapter", "")
    if book_id and chapter:
        book = BOOKS_BY_ID.get(book_id.upper())
        if book:
            prefill_ref = f"{book['name']} {chapter}"

    # From the Verse of the Day page: /journal/free/?ref=John 3:16
    prefill_scripture = ""
    if request.GET.get("ref"):
        prefill_ref = request.GET["ref"][:200]
        profile, _ = Profile.objects.get_or_create(user=request.user)
        votd = verse_for(_user_local_date(profile))
        if votd["reference"] == prefill_ref:
            prefill_scripture = f'{votd["text"]} ({votd["reference"]}, {votd["translation"]})'

    if request.method == "POST":
        form = FreeJournalEntryForm(request.POST, instance=journal_entry)
        if form.is_valid():
            entry              = form.save(commit=False)
            entry.user         = request.user
            entry.entry_date   = today
            entry.journal_type = JournalEntry.JOURNAL_TYPE_FREE
            entry.plan_day     = None
            entry.save()
            _auto_record_from_ref(request.user, entry.passage_ref, entry)
            return redirect("today")
    else:
        initial = {"passage_ref": prefill_ref} if prefill_ref else {}
        if prefill_scripture:
            initial["scripture"] = prefill_scripture
        form    = FreeJournalEntryForm(
            instance=journal_entry,
            initial=initial if not journal_entry else {},
        )

    books_json = [
        {"id": b["id"], "name": b["name"], "testament": b["testament"],
         "chapters": len(b["verses"])}
        for b in BIBLE_BOOKS
    ]

    context = {
        "form":         form,
        "today":        today,
        "is_edit":      journal_entry is not None,
        "books_json":   books_json,
        "prefill_book": book_id.upper() if book_id else "",
        "prefill_chap": chapter,
    }
    return render(request, "journal/journal_free.html", context)


# ── History — paginated list ──────────────────────────────────────────────────

@login_required
def journal_history_view(request):
    qs = (
        JournalEntry.objects
        .filter(user=request.user)
        .select_related("plan_day", "plan_day__plan")
        .order_by("-entry_date")
    )

    paginator = Paginator(qs, 20)
    page_num  = request.GET.get("page", 1)
    page_obj  = paginator.get_page(page_num)

    context = {
        "page_obj":   page_obj,
        "total":      paginator.count,
    }
    return render(request, "journal/journal_history.html", context)


# ── Entry Detail / Edit ───────────────────────────────────────────────────────

@login_required
def journal_entry_view(request, entry_date_str):
    """
    View, edit, or create a journal entry for a specific date.
    URL: /journal/entry/2025-03-15/

    - GET with existing entry  → pre-filled edit form
    - GET with no entry        → blank form (backfill)
    - POST                     → save and redirect to history
    - POST with action=delete  → delete and redirect to history
    """
    # Parse the date from the URL
    try:
        entry_date = date.fromisoformat(entry_date_str)
    except ValueError:
        return redirect("journal_history")

    if entry_date > date.today():
        return redirect("journal_history")

    # Fetch existing entry for this user + date (may be None)
    journal_entry = (
        JournalEntry.objects
        .filter(user=request.user, entry_date=entry_date)
        .select_related("plan_day", "plan_day__plan")
        .first()
    )

    # ── DELETE ────────────────────────────────────────────────────────────────
    if request.method == "POST" and request.POST.get("action") == "delete":
        if journal_entry:
            journal_entry.delete()
        return redirect("journal_history")

    # ── SAVE (POST) ───────────────────────────────────────────────────────────
    if request.method == "POST":
        form = BackfillJournalEntryForm(request.POST, instance=journal_entry)
        if form.is_valid():
            new_date = form.cleaned_data["entry_date"]

            if (
                journal_entry
                and new_date != journal_entry.entry_date
                and JournalEntry.objects.filter(
                    user=request.user, entry_date=new_date
                ).exclude(pk=journal_entry.pk).exists()
            ):
                form.add_error(
                    "entry_date",
                    "You already have an entry for that date. "
                    "Edit it directly from the history list."
                )
            else:
                entry = form.save(commit=False)
                entry.user = request.user

                # Plan day association — from hidden field or existing entry
                plan_day_id = request.POST.get("plan_day_id")
                linked_plan_day = None
                if plan_day_id:
                    try:
                        linked_plan_day = PlanDay.objects.get(pk=plan_day_id)
                    except PlanDay.DoesNotExist:
                        pass
                elif journal_entry and journal_entry.plan_day:
                    linked_plan_day = journal_entry.plan_day

                entry.plan_day = linked_plan_day
                entry.journal_type = (
                    JournalEntry.JOURNAL_TYPE_PLAN
                    if linked_plan_day
                    else JournalEntry.JOURNAL_TYPE_FREE
                )
                entry.save()

                # Keep completion records in sync
                if linked_plan_day:
                    _ensure_completion(request.user, linked_plan_day, entry)

                if entry.passage_ref:
                    _auto_record_from_ref(request.user, entry.passage_ref, entry)
                return redirect("journal_history")

    # ── GET ───────────────────────────────────────────────────────────────────
    else:
        initial = {"entry_date": entry_date}
        if journal_entry:
            form = BackfillJournalEntryForm(instance=journal_entry)
        else:
            form = BackfillJournalEntryForm(initial=initial)

    # Book browser data
    books_json = [
        {"id": b["id"], "name": b["name"], "testament": b["testament"],
         "chapters": len(b["verses"])}
        for b in BIBLE_BOOKS
    ]

    # Plan day selector — load user's active plan days for association
    profile, _ = Profile.objects.get_or_create(user=request.user)
    plan_days_for_selector = []
    if profile.reading_plan:
        plan_days_for_selector = list(
            PlanDay.objects
            .filter(plan=profile.reading_plan)
            .order_by("day_number")
            .values("id", "day_number", "passages")
        )

    # Which plan day is currently linked?
    current_plan_day_id = None
    if journal_entry and journal_entry.plan_day_id:
        current_plan_day_id = journal_entry.plan_day_id
    elif request.GET.get("plan_day"):
        current_plan_day_id = request.GET.get("plan_day")

    context = {
        "form":                   form,
        "entry_date":             entry_date,
        "journal_entry":          journal_entry,
        "is_edit":                journal_entry is not None,
        "books_json":             books_json,
        "plan_days_for_selector": plan_days_for_selector,
        "current_plan_day_id":    current_plan_day_id,
        "active_plan":            profile.reading_plan,
    }
    return render(request, "journal/journal_entry.html", context)


# ── Backfill shortcut: redirect to entry page for a new date ─────────────────

@login_required
def journal_backfill_view(request):
    """
    Redirects to /journal/entry/<date>/ for backfilling.
    Accepts ?date=YYYY-MM-DD or defaults to yesterday.
    """
    raw  = request.GET.get("date", "")
    try:
        target = date.fromisoformat(raw)
    except ValueError:
        target = date.today() - timedelta(days=1)

    if target > date.today():
        target = date.today()

    return redirect("journal_entry", entry_date_str=str(target))


# ── Shared helpers ────────────────────────────────────────────────────────────

def _ensure_completion(user, plan_day, journal_entry=None):
    """
    Create a PlanDayCompletion for (user, plan_day) if one doesn't exist.
    Called whenever a plan-linked journal entry is saved, keeping
    PlanDayCompletion in sync with journal entries automatically.
    """
    if plan_day is None:
        return
    obj, _ = PlanDayCompletion.objects.get_or_create(
        user=user,
        plan_day=plan_day,
        defaults={
            "source":        PlanDayCompletion.SOURCE_JOURNAL,
            "journal_entry": journal_entry,
        },
    )
    # If completion already exists but has no journal_entry linked, update it
    if obj.journal_entry is None and journal_entry is not None:
        obj.journal_entry = journal_entry
        obj.source        = PlanDayCompletion.SOURCE_JOURNAL
        obj.save(update_fields=["journal_entry", "source"])

def _auto_record_from_ref(user, ref, entry):
    if not ref:
        return
    ref = ref.strip()
    for book in BIBLE_BOOKS:
        if ref.lower().startswith(book["name"].lower()):
            remainder = ref[len(book["name"]):].strip()
            m         = re.match(r"(\d+)", remainder)
            if m:
                chapter = int(m.group(1))
                if 1 <= chapter <= len(book["verses"]):
                    ReadingRecord.objects.get_or_create(
                        user=user,
                        book_id=book["id"],
                        chapter=chapter,
                        start_verse=None,
                        end_verse=None,
                        defaults={
                            "source":        ReadingRecord.SOURCE_JOURNAL,
                            "journal_entry": entry,
                        },
                    )
            return


# ── Bible Progress ────────────────────────────────────────────────────────────

@login_required
def progress_view(request):
    records  = (
        ReadingRecord.objects
        .filter(user=request.user)
        .values_list("book_id", "chapter")
    )
    read_set = set(records)

    def build_book_data(book):
        num_chapters = len(book["verses"])
        chapters     = [
            {"number": ch, "read": (book["id"], ch) in read_set}
            for ch in range(1, num_chapters + 1)
        ]
        read_count = sum(1 for c in chapters if c["read"])
        return {
            "id":         book["id"],
            "name":       book["name"],
            "chapters":   chapters,
            "total":      num_chapters,
            "read_count": read_count,
            "complete":   read_count == num_chapters,
            "pct":        int(100 * read_count / num_chapters) if num_chapters else 0,
        }

    ot_data = [build_book_data(b) for b in OT_BOOKS]
    nt_data = [build_book_data(b) for b in NT_BOOKS]
    total   = sum(d["total"] for d in ot_data + nt_data)
    read    = sum(d["read_count"] for d in ot_data + nt_data)

    context = {
        "ot_books":       ot_data,
        "nt_books":       nt_data,
        "total_chapters": total,
        "read_chapters":  read,
        "overall_pct":    int(100 * read / total) if total else 0,
    }
    return render(request, "journal/progress.html", context)


# ── Mark / Unmark Chapter ─────────────────────────────────────────────────────

@login_required
@require_POST
def mark_read_view(request):
    form   = MarkReadForm(request.POST)
    action = request.POST.get("action", "mark")

    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    book_id     = form.cleaned_data["book_id"].upper()
    chapter     = form.cleaned_data["chapter"]
    start_verse = form.cleaned_data.get("start_verse") or None
    end_verse   = form.cleaned_data.get("end_verse") or None

    book = BOOKS_BY_ID.get(book_id)
    if not book or chapter < 1 or chapter > len(book["verses"]):
        return JsonResponse({"ok": False, "errors": "Invalid book or chapter."}, status=400)

    if action == "unmark":
        ReadingRecord.objects.filter(
            user=request.user, book_id=book_id, chapter=chapter,
            start_verse=start_verse, end_verse=end_verse,
        ).delete()
        return JsonResponse({"ok": True, "action": "unmarked", "book_id": book_id, "chapter": chapter})

    ReadingRecord.objects.get_or_create(
        user=request.user, book_id=book_id, chapter=chapter,
        start_verse=start_verse, end_verse=end_verse,
        defaults={"source": ReadingRecord.SOURCE_MANUAL},
    )
    return JsonResponse({"ok": True, "action": "marked", "book_id": book_id, "chapter": chapter})


# ── AJAX: verse count ─────────────────────────────────────────────────────────

@login_required
def verse_count_view(request):
    book_id = request.GET.get("book", "").upper()
    try:
        chapter = int(request.GET.get("chapter", ""))
    except (ValueError, TypeError):
        return JsonResponse({"error": "bad chapter"}, status=400)
    count = verse_count(book_id, chapter)
    if count == 0:
        return JsonResponse({"error": "not found"}, status=404)
    return JsonResponse({"verses": count})


# ── Plan Schedule ─────────────────────────────────────────────────────────────

@login_required
def schedule_view(request):
    """
    Full paginated plan schedule — every day in the user's current reading
    plan, showing completion status and actions for past/missed days.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if not profile.reading_plan or not profile.plan_start_date:
        return redirect("plans")

    today      = date.today()
    day_number = profile.current_day_number()

    # All PlanDays for this plan
    all_days = list(
        PlanDay.objects
        .filter(plan=profile.reading_plan)
        .order_by("day_number")
    )

    # Completed plan days for this user
    completed_map = {
        c.plan_day_id: c
        for c in PlanDayCompletion.objects.filter(
            user=request.user,
            plan_day__plan=profile.reading_plan,
        ).select_related("journal_entry")
    }

    # Journal entries keyed by plan_day_id (for plan-type entries)
    journaled_plan_days = set(
        JournalEntry.objects
        .filter(
            user=request.user,
            journal_type=JournalEntry.JOURNAL_TYPE_PLAN,
            plan_day__plan=profile.reading_plan,
        )
        .values_list("plan_day_id", flat=True)
    )

    total_days     = len(all_days)
    completed_days = len(completed_map)
    is_sequential  = profile.is_sequential

    # Build annotated rows
    rows = []
    for pd in all_days:
        dn         = pd.day_number
        completion = completed_map.get(pd.id)
        has_journal = pd.id in journaled_plan_days

        # Date calculation — meaningful in calendar mode, approximate in sequential
        if is_sequential:
            # In sequential mode, date is the start date + day offset (informational only)
            pd_date = profile.plan_start_date + timedelta(days=dn - 1)
        else:
            pd_date = profile.plan_start_date + timedelta(days=dn - 1)

        # Status logic differs by mode
        if is_sequential:
            # Sequential: past = completed, current = next to do, future = not yet reached
            is_current = dn == day_number
            is_done    = completion is not None
            is_future  = dn > day_number and not is_done

            if is_done:
                status = "journaled" if has_journal else "read"
            elif is_current:
                status = "today"
            else:
                # dn < day_number but not completed shouldn't happen in sequential
                # (day_number IS the first incomplete), but guard for edge cases
                status = "missed" if dn < day_number else "upcoming"
        else:
            # Calendar mode: past/today/future based on day number vs today's day
            is_today  = dn == day_number
            is_past   = dn < day_number
            is_future = dn > day_number

            if is_past or is_today:
                status = "today" if is_today else (
                    "journaled" if has_journal else
                    "read"      if completion else
                    "missed"
                )
            else:
                status = "upcoming"

        rows.append({
            "plan_day":    pd,
            "day_number":  dn,
            "date":        pd_date,
            "is_today":    dn == day_number,
            "is_past":     dn < day_number,
            "is_future":   dn > day_number,
            "status":      status,
            "completion":  completion,
            "has_journal": has_journal,
            "journal_url": f"/journal/entry/{pd_date.isoformat()}/",
        })

    paginator = Paginator(rows, 30)
    page_num  = request.GET.get("page", 1)

    # Default to the page containing today's day
    if request.GET.get("page") is None:
        page_num = max(1, (day_number - 1) // 30 + 1)

    page_obj = paginator.get_page(page_num)

    context = {
        "page_obj":       page_obj,
        "profile":        profile,
        "plan":           profile.reading_plan,
        "total_days":     total_days,
        "completed_days": completed_days,
        "pct_complete":   int(100 * completed_days / total_days) if total_days else 0,
        "today_day":      day_number,
        "today":          today,
        "is_sequential":  is_sequential,
    }
    return render(request, "journal/schedule.html", context)


# ── Mark Plan Day Read (AJAX) ─────────────────────────────────────────────────

@login_required
@require_POST
def mark_plan_day_view(request):
    """
    Toggle a plan day's completion status.
    POST: plan_day_id=<id>, action=mark|unmark
    Returns JSON so the schedule page can update in place.
    """
    plan_day_id = request.POST.get("plan_day_id")
    action      = request.POST.get("action", "mark")

    try:
        plan_day = PlanDay.objects.select_related("plan").get(pk=plan_day_id)
    except (PlanDay.DoesNotExist, ValueError):
        return JsonResponse({"ok": False, "error": "Plan day not found."}, status=404)

    # Security: only allow for the user's active plan
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if plan_day.plan != profile.reading_plan:
        return JsonResponse({"ok": False, "error": "Not your active plan."}, status=403)

    if action == "unmark":
        PlanDayCompletion.objects.filter(
            user=request.user, plan_day=plan_day
        ).delete()
        return JsonResponse({"ok": True, "action": "unmarked", "plan_day_id": plan_day_id})

    obj, created = PlanDayCompletion.objects.get_or_create(
        user=request.user,
        plan_day=plan_day,
        defaults={"source": PlanDayCompletion.SOURCE_MANUAL},
    )
    return JsonResponse({
        "ok":          True,
        "action":      "marked",
        "created":     created,
        "plan_day_id": plan_day_id,
    })


# ── Mobile app (PWA): manifest + service worker ──────────────────────────────



def manifest_view(request):
    data = {
        "name": "Bible Journal",
        "short_name": "Journal",
        "description": "SOAP Bible journal with reading plans and a daily verse.",
        "start_url": "/today/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#faf7f2",
        "theme_color": "#1c1712",
        "icons": [
            {"src": static("journal/icons/icon-192.png"), "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": static("journal/icons/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    return HttpResponse(json.dumps(data), content_type="application/manifest+json")


@cache_control(no_cache=True)
def service_worker_view(request):
    # Served from the site root so its scope covers every page.
    return render(request, "journal/sw.js", content_type="application/javascript")


def _user_local_date(profile):
    try:
        return dj_tz.now().astimezone(ZoneInfo(profile.timezone)).date()
    except (ZoneInfoNotFoundError, ValueError):
        return date.today()


# ── Daily verse ──────────────────────────────────────────────────────────────

@login_required
def verse_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    day = _user_local_date(profile)
    verse = verse_for(day)
    recent = DailyVerse.objects.filter(date__lt=day).order_by("-date")[:14]
    return render(request, "journal/verse.html", {
        "verse": verse, "day": day, "recent": recent,
    })


# ── Notification settings + push subscription endpoints ──────────────────────

@login_required
def notifications_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    saved = False
    if request.method == "POST":
        try:
            hh, mm = (int(x) for x in request.POST.get("notify_time", "07:00").split(":")[:2])
            profile.notify_time = dtime(hh, mm)
        except ValueError:
            pass
        tz = request.POST.get("timezone", "")
        if tz in available_timezones():
            profile.timezone = tz
        profile.verse_notifications = request.POST.get("verse_notifications") == "on"
        profile.save()
        saved = True

    return render(request, "journal/notifications.html", {
        "profile": profile,
        "saved": saved,
        "push_ready": push_configured(),
        "vapid_public_key": settings.VAPID_PUBLIC_KEY,
        "device_count": request.user.push_subscriptions.count(),
        "timezones": sorted(t for t in available_timezones() if "/" in t and not t.startswith("Etc/")),
    })


@login_required
@require_POST
def push_subscribe_view(request):
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
        keys = data["keys"]
    except (ValueError, KeyError, TypeError):
        return HttpResponseBadRequest("bad subscription")

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "user": request.user,
            "p256dh": keys["p256dh"],
            "auth": keys["auth"],
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:300],
        },
    )
    profile, _ = Profile.objects.get_or_create(user=request.user)
    tz = data.get("timezone")
    if tz and tz in available_timezones():
        profile.timezone = tz
    profile.verse_notifications = True
    profile.save()
    return JsonResponse({"ok": True, "devices": request.user.push_subscriptions.count()})


@login_required
@require_POST
def push_unsubscribe_view(request):
    try:
        endpoint = json.loads(request.body).get("endpoint")
    except ValueError:
        endpoint = None
    qs = request.user.push_subscriptions.all()
    if endpoint:
        qs = qs.filter(endpoint=endpoint)
    qs.delete()
    return JsonResponse({"ok": True, "devices": request.user.push_subscriptions.count()})


@login_required
@require_POST
def push_test_view(request):
    if not push_configured():
        return JsonResponse({"ok": False, "error": "Push keys are not configured on the server."}, status=400)
    profile, _ = Profile.objects.get_or_create(user=request.user)
    delivered = send_verse_to_user(request.user, verse_for(_user_local_date(profile)))
    return JsonResponse({"ok": delivered > 0, "delivered": delivered})
