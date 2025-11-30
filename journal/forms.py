from django import forms
from .models import JournalEntry


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ["scripture", "observation", "application", "prayer"]
        widgets = {
            "scripture": forms.Textarea(attrs={"rows": 3}),
            "observation": forms.Textarea(attrs={"rows": 4}),
            "application": forms.Textarea(attrs={"rows": 4}),
            "prayer": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "scripture": "Scripture (S)",
            "observation": "Observation (O)",
            "application": "Application (A)",
            "prayer": "Prayer (P)",
        }
