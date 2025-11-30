from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404


from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Profile, PlanDay, JournalEntry
from .forms import JournalEntryForm



@login_required(login_url="/admin/login/")
def today_view(request):
    # Ensure the user has a Profile row
    profile, _ = Profile.objects.get_or_create(user=request.user)

    has_plan = bool(profile.reading_plan and profile.plan_start_date)

    plan_day = None
    day_number = None

    if has_plan:
        # Which day of the plan are we on?
        day_number = profile.current_day_number()

        # Get that specific PlanDay, if it exists
        plan_day = (
            PlanDay.objects
            .filter(plan=profile.reading_plan, day_number=day_number)
            .first()
        )

    context = {
        "today": date.today(),
        "has_plan": has_plan,
        "plan_day": plan_day,
        "day_number": day_number,
    }
    return render(request, "journal/today.html", context)


@login_required(login_url="/admin/login/")
def journal_today_view(request):
    """
    Create or edit today's SOAP entry for the logged-in user.
    """
    # Ensure profile exists
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if not profile.reading_plan or not profile.plan_start_date:
        # No plan setup yet - send back to today page
        return redirect("today")

    # Determine which day of the plan we're on
    today = date.today()
    day_number = profile.current_day_number(today)

    # Get the PlanDay for today
    plan_day = (
        PlanDay.objects
        .filter(plan=profile.reading_plan, day_number=day_number)
        .first()
    )

    if not plan_day:
        # If no reading defined, just send back to today page
        return redirect("today")

    # Try to get existing entry for today
    journal_entry = (
        JournalEntry.objects
        .filter(user=request.user, entry_date=today)
        .first()
    )

    if request.method == "POST":
        form = JournalEntryForm(request.POST, instance=journal_entry)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.entry_date = today
            entry.plan_day = plan_day
            entry.save()
            # After saving, go back to today dashboard
            return redirect("today")
    else:
        form = JournalEntryForm(instance=journal_entry)

    context = {
        "form": form,
        "today": today,
        "plan_day": plan_day,
        "day_number": day_number,
        "is_edit": journal_entry is not None,
    }
    return render(request, "journal/journal_today.html", context)