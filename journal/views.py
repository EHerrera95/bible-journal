from datetime import date, timedelta
import re

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Profile, PlanDay, JournalEntry, ReadingRecord, ReadingPlan
from .forms import (
    JournalEntryForm, FreeJournalEntryForm,
    BackfillJournalEntryForm, MarkReadForm,
)
from .bible_data import BIBLE_BOOKS, BOOKS_BY_ID, OT_BOOKS, NT_BOOKS, verse_count


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

    if has_plan:
        day_number = profile.current_day_number()
        plan_day   = (
            PlanDay.objects
            .filter(plan=profile.reading_plan, day_number=day_number)
            .first()
        )

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
    }
    return render(request, "journal/today.html", context)


# ── Plan Selection ────────────────────────────────────────────────────────────

@login_required
def plans_view(request):
    from django.db.models import Count
    plans      = ReadingPlan.objects.annotate(day_count=Count("days")).order_by("name")
    profile, _ = Profile.objects.get_or_create(user=request.user)
    context    = {
        "plans":        plans,
        "current_plan": profile.reading_plan,
        "bible_books":  BIBLE_BOOKS,
    }
    return render(request, "journal/plans.html", context)


@login_required
@require_POST
def select_plan_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    plan_id    = request.POST.get("plan_id")
    book_id    = request.POST.get("book_id")
    start_date = request.POST.get("start_date") or str(date.today())

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

            # Check for a date conflict if the user changed the date on an
            # existing entry (can't have two entries on the same day)
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
                entry              = form.save(commit=False)
                entry.user         = request.user
                entry.journal_type = JournalEntry.JOURNAL_TYPE_FREE
                entry.plan_day     = journal_entry.plan_day if journal_entry else None
                entry.save()
                # Auto-create a reading record if we can parse the passage
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

    # Book browser data (same as free-form view)
    books_json = [
        {"id": b["id"], "name": b["name"], "testament": b["testament"],
         "chapters": len(b["verses"])}
        for b in BIBLE_BOOKS
    ]

    context = {
        "form":          form,
        "entry_date":    entry_date,
        "journal_entry": journal_entry,
        "is_edit":       journal_entry is not None,
        "books_json":    books_json,
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
