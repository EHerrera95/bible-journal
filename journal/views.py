from django.shortcuts import render
from datetime import date

def today_view(request):
    # For now this is just a placeholder display.
    # Later, we'll pull real plan data and entries.
    context = {
        "today": date.today(),
        "passages": "Genesis 1–3",      # temporary dummy data
        "key_verse_ref": "Genesis 1:1", # temporary dummy data
    }
    return render(request, "journal/today.html", context)
