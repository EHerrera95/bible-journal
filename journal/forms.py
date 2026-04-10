from django import forms
from .models import JournalEntry


SOAP_PLACEHOLDERS = {
    "scripture":    "Write out the verse or passage that stood out to you…",
    "observation":  "What do you notice? Who is speaking, and what is happening?",
    "application":  "How does this apply to your life today?",
    "prayer":       "Write a short prayer in response to what you've read…",
}

SOAP_FIELDS = ["scripture", "observation", "application", "prayer"]

SOAP_WIDGETS = {
    field: forms.Textarea(attrs={
        "placeholder": SOAP_PLACEHOLDERS[field],
        "rows": 5,
    })
    for field in SOAP_FIELDS
}


class JournalEntryForm(forms.ModelForm):
    """Plan-based journal entry — date and plan_day set by the view."""

    class Meta:
        model   = JournalEntry
        fields  = SOAP_FIELDS
        widgets = SOAP_WIDGETS


class FreeJournalEntryForm(forms.ModelForm):
    """Free-form entry for today. Date fixed to today in the view."""

    passage_ref = forms.CharField(
        max_length=200,
        required=True,
        label="Passage Reference",
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. John 3:16-21  or  Romans 8",
            "id": "id_passage_ref",
        }),
        help_text="Type a reference, or use the browser below to select one.",
    )

    class Meta:
        model   = JournalEntry
        fields  = ["passage_ref"] + SOAP_FIELDS
        widgets = SOAP_WIDGETS


class BackfillJournalEntryForm(forms.ModelForm):
    """
    Create or edit an entry on any past date.
    Used for:
      - History detail/edit page  (/journal/entry/<date>/)
      - Backfilling past entries  (same URL, new date)
    """

    entry_date = forms.DateField(
        required=True,
        label="Date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    passage_ref = forms.CharField(
        max_length=200,
        required=False,
        label="Passage Reference",
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. John 3:16-21  or  Romans 8",
            "id": "id_passage_ref",
        }),
        help_text="Leave blank if you prefer not to record a passage.",
    )

    class Meta:
        model   = JournalEntry
        fields  = ["entry_date", "passage_ref"] + SOAP_FIELDS
        widgets = SOAP_WIDGETS

    def clean_entry_date(self):
        from datetime import date
        d = self.cleaned_data.get("entry_date")
        if d and d > date.today():
            raise forms.ValidationError("Entry date cannot be in the future.")
        return d


class MarkReadForm(forms.Form):
    book_id     = forms.CharField(max_length=5, widget=forms.HiddenInput())
    chapter     = forms.IntegerField(min_value=1, widget=forms.HiddenInput())
    start_verse = forms.IntegerField(min_value=1, required=False, label="From verse",
                                     widget=forms.NumberInput(attrs={"placeholder": "1"}))
    end_verse   = forms.IntegerField(min_value=1, required=False, label="To verse",
                                     widget=forms.NumberInput(attrs={"placeholder": "leave blank = whole chapter"}))

    def clean(self):
        cleaned = super().clean()
        sv, ev  = cleaned.get("start_verse"), cleaned.get("end_verse")
        if sv and ev and ev < sv:
            raise forms.ValidationError("End verse must be ≥ start verse.")
        return cleaned
