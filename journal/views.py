from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Profile, PlanDay


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
