# journal/management/commands/seed_plans.py
#
# Run with:  python manage.py seed_plans
# Re-running is safe — uses get_or_create so nothing is duplicated.

from django.core.management.base import BaseCommand
from journal.models import ReadingPlan, PlanDay


# ── Helper ───────────────────────────────────────────────────────────────────

def make_plan(name, description, days_data):
    """
    days_data: list of (passages_str, key_verse_ref_str)
    """
    plan, _ = ReadingPlan.objects.get_or_create(
        name=name,
        defaults={"description": description},
    )
    for i, (passages, key_verse) in enumerate(days_data, start=1):
        PlanDay.objects.get_or_create(
            plan=plan,
            day_number=i,
            defaults={
                "passages":      passages,
                "key_verse_ref": key_verse,
            },
        )
    return plan


# ═════════════════════════════════════════════════════════════════════════════
# PLAN DATA
# ═════════════════════════════════════════════════════════════════════════════

# ── 1. Gospels in 30 Days ────────────────────────────────────────────────────

GOSPELS_30 = [
    ("Matthew 1–2",        "Matthew 1:21"),
    ("Matthew 3–4",        "Matthew 4:19"),
    ("Matthew 5–6",        "Matthew 5:3"),
    ("Matthew 7–8",        "Matthew 7:7"),
    ("Matthew 9–10",       "Matthew 9:37"),
    ("Matthew 11–12",      "Matthew 11:28"),
    ("Matthew 13–14",      "Matthew 13:44"),
    ("Matthew 15–16",      "Matthew 16:16"),
    ("Matthew 17–18",      "Matthew 18:3"),
    ("Matthew 19–20",      "Matthew 20:28"),
    ("Matthew 21–22",      "Matthew 21:9"),
    ("Matthew 23–24",      "Matthew 24:35"),
    ("Matthew 25–26",      "Matthew 25:40"),
    ("Matthew 27–28",      "Matthew 28:6"),
    ("Mark 1–3",           "Mark 1:15"),
    ("Mark 4–6",           "Mark 4:39"),
    ("Mark 7–9",           "Mark 8:29"),
    ("Mark 10–12",         "Mark 10:45"),
    ("Mark 13–16",         "Mark 16:6"),
    ("Luke 1–2",           "Luke 2:11"),
    ("Luke 3–5",           "Luke 4:18"),
    ("Luke 6–7",           "Luke 6:27"),
    ("Luke 8–9",           "Luke 9:23"),
    ("Luke 10–12",         "Luke 10:27"),
    ("Luke 13–15",         "Luke 15:7"),
    ("Luke 16–18",         "Luke 18:27"),
    ("Luke 19–21",         "Luke 19:10"),
    ("Luke 22–24",         "Luke 24:6"),
    ("John 1–6",           "John 1:14"),
    ("John 7–21",          "John 3:16"),
]

# ── 2. Psalms & Proverbs in 30 Days ─────────────────────────────────────────

PSALMS_PROVERBS_30 = [
    ("Psalm 1–4; Proverbs 1",         "Psalm 1:1"),
    ("Psalm 5–8; Proverbs 2",         "Psalm 8:4"),
    ("Psalm 9–12; Proverbs 3",        "Proverbs 3:5"),
    ("Psalm 13–16; Proverbs 4",       "Psalm 16:8"),
    ("Psalm 17–20; Proverbs 5",       "Psalm 19:1"),
    ("Psalm 21–24; Proverbs 6",       "Psalm 23:1"),
    ("Psalm 25–28; Proverbs 7",       "Psalm 27:1"),
    ("Psalm 29–32; Proverbs 8",       "Psalm 32:8"),
    ("Psalm 33–36; Proverbs 9",       "Psalm 34:8"),
    ("Psalm 37–40; Proverbs 10",      "Psalm 37:4"),
    ("Psalm 41–44; Proverbs 11",      "Proverbs 11:2"),
    ("Psalm 45–48; Proverbs 12",      "Psalm 46:1"),
    ("Psalm 49–52; Proverbs 13",      "Psalm 51:10"),
    ("Psalm 53–56; Proverbs 14",      "Proverbs 14:12"),
    ("Psalm 57–60; Proverbs 15",      "Psalm 57:1"),
    ("Psalm 61–64; Proverbs 16",      "Proverbs 16:3"),
    ("Psalm 65–68; Proverbs 17",      "Psalm 66:1"),
    ("Psalm 69–72; Proverbs 18",      "Proverbs 18:10"),
    ("Psalm 73–76; Proverbs 19",      "Psalm 73:26"),
    ("Psalm 77–80; Proverbs 20",      "Psalm 77:14"),
    ("Psalm 81–84; Proverbs 21",      "Proverbs 21:21"),
    ("Psalm 85–88; Proverbs 22",      "Psalm 86:5"),
    ("Psalm 89–92; Proverbs 23",      "Psalm 91:1"),
    ("Psalm 93–96; Proverbs 24",      "Psalm 96:3"),
    ("Psalm 97–100; Proverbs 25",     "Psalm 100:1"),
    ("Psalm 101–104; Proverbs 26",    "Psalm 103:12"),
    ("Psalm 105–107; Proverbs 27",    "Psalm 107:1"),
    ("Psalm 108–112; Proverbs 28",    "Psalm 112:1"),
    ("Psalm 113–118; Proverbs 29",    "Psalm 118:24"),
    ("Psalm 119–150; Proverbs 30–31", "Psalm 119:105"),
]

# ── 3. New Testament in 1 Year (365 days, ~1 chapter/day + repeats) ──────────
# NT has 260 chapters. We go through once then revisit key books.

def _build_nt_year():
    # NT books in canonical order with chapter counts
    nt_books = [
        ("Matthew",        28), ("Mark",           16), ("Luke",           24),
        ("John",           21), ("Acts",            28), ("Romans",         16),
        ("1 Corinthians",  16), ("2 Corinthians",   13), ("Galatians",       6),
        ("Ephesians",       6), ("Philippians",      4), ("Colossians",       4),
        ("1 Thessalonians", 5), ("2 Thessalonians",  3), ("1 Timothy",        6),
        ("2 Timothy",       4), ("Titus",            3), ("Philemon",         1),
        ("Hebrews",        13), ("James",             5), ("1 Peter",          5),
        ("2 Peter",         3), ("1 John",            5), ("2 John",           1),
        ("3 John",          1), ("Jude",              1), ("Revelation",      22),
    ]
    chapters = []
    for book, count in nt_books:
        for ch in range(1, count + 1):
            chapters.append((book, ch))

    # 260 chapters for first pass; fill remaining 105 days revisiting
    revisit = [
        ("John", 1), ("John", 3), ("John", 14), ("John", 15), ("John", 17),
        ("Romans", 8), ("Romans", 12), ("Ephesians", 1), ("Ephesians", 2),
        ("Philippians", 4), ("Colossians", 1), ("Hebrews", 11), ("Hebrews", 12),
        ("James", 1), ("1 Peter", 1), ("Revelation", 1), ("Revelation", 21),
        ("Revelation", 22),
    ]
    # Pad to 365
    while len(chapters) < 365:
        chapters.extend(revisit)
    chapters = chapters[:365]

    days = []
    for book, ch in chapters:
        days.append((f"{book} {ch}", _nt_key_verse(book, ch)))
    return days


def _nt_key_verse(book, ch):
    lookup = {
        ("Matthew", 1): "Matthew 1:21",   ("Matthew", 5): "Matthew 5:3",
        ("Matthew", 6): "Matthew 6:33",   ("Matthew", 28): "Matthew 28:19",
        ("Mark", 1): "Mark 1:15",         ("Luke", 2): "Luke 2:11",
        ("Luke", 15): "Luke 15:7",        ("John", 1): "John 1:1",
        ("John", 3): "John 3:16",         ("John", 14): "John 14:6",
        ("John", 15): "John 15:5",        ("Acts", 1): "Acts 1:8",
        ("Acts", 2): "Acts 2:38",         ("Romans", 1): "Romans 1:16",
        ("Romans", 3): "Romans 3:23",     ("Romans", 5): "Romans 5:8",
        ("Romans", 8): "Romans 8:28",     ("Romans", 10): "Romans 10:9",
        ("Romans", 12): "Romans 12:2",    ("1 Corinthians", 13): "1 Corinthians 13:4",
        ("Galatians", 2): "Galatians 2:20", ("Ephesians", 2): "Ephesians 2:8",
        ("Philippians", 4): "Philippians 4:13", ("Colossians", 3): "Colossians 3:23",
        ("Hebrews", 11): "Hebrews 11:1",  ("James", 1): "James 1:5",
        ("1 Peter", 5): "1 Peter 5:7",    ("Revelation", 21): "Revelation 21:4",
        ("Revelation", 22): "Revelation 22:20",
    }
    return lookup.get((book, ch), f"{book} {ch}:1")


NT_YEAR = _build_nt_year()


# ── 4. Old & New Testament Together — 1 Year ────────────────────────────────
# 3 OT chapters + 1 NT chapter per day (blended)

def _build_ot_nt_year():
    ot_sequence = [
        # Genesis–Malachi in order, listed as (book, chapters_per_entry) groups
        # We'll just list each chapter individually and batch into groups of 3
        *[(f"Genesis", ch) for ch in range(1, 51)],
        *[(f"Exodus", ch) for ch in range(1, 41)],
        *[(f"Leviticus", ch) for ch in range(1, 28)],
        *[(f"Numbers", ch) for ch in range(1, 37)],
        *[(f"Deuteronomy", ch) for ch in range(1, 35)],
        *[(f"Joshua", ch) for ch in range(1, 25)],
        *[(f"Judges", ch) for ch in range(1, 22)],
        *[(f"Ruth", ch) for ch in range(1, 5)],
        *[(f"1 Samuel", ch) for ch in range(1, 32)],
        *[(f"2 Samuel", ch) for ch in range(1, 25)],
        *[(f"1 Kings", ch) for ch in range(1, 23)],
        *[(f"2 Kings", ch) for ch in range(1, 26)],
        *[(f"1 Chronicles", ch) for ch in range(1, 30)],
        *[(f"2 Chronicles", ch) for ch in range(1, 37)],
        *[(f"Ezra", ch) for ch in range(1, 11)],
        *[(f"Nehemiah", ch) for ch in range(1, 14)],
        *[(f"Esther", ch) for ch in range(1, 10)],
        *[(f"Job", ch) for ch in range(1, 43)],
        *[(f"Psalm", ch) for ch in range(1, 151)],
        *[(f"Proverbs", ch) for ch in range(1, 32)],
        *[(f"Ecclesiastes", ch) for ch in range(1, 13)],
        *[(f"Song of Solomon", ch) for ch in range(1, 9)],
        *[(f"Isaiah", ch) for ch in range(1, 67)],
        *[(f"Jeremiah", ch) for ch in range(1, 53)],
        *[(f"Lamentations", ch) for ch in range(1, 6)],
        *[(f"Ezekiel", ch) for ch in range(1, 49)],
        *[(f"Daniel", ch) for ch in range(1, 13)],
        *[(f"Hosea", ch) for ch in range(1, 15)],
        *[(f"Joel", ch) for ch in range(1, 4)],
        *[(f"Amos", ch) for ch in range(1, 10)],
        *[(f"Obadiah", 1)],
        *[(f"Jonah", ch) for ch in range(1, 5)],
        *[(f"Micah", ch) for ch in range(1, 8)],
        *[(f"Nahum", ch) for ch in range(1, 4)],
        *[(f"Habakkuk", ch) for ch in range(1, 4)],
        *[(f"Zephaniah", ch) for ch in range(1, 4)],
        *[(f"Haggai", ch) for ch in range(1, 3)],
        *[(f"Zechariah", ch) for ch in range(1, 15)],
        *[(f"Malachi", ch) for ch in range(1, 5)],
    ]

    nt_sequence = [
        *[(f"Matthew", ch) for ch in range(1, 29)],
        *[(f"Mark", ch) for ch in range(1, 17)],
        *[(f"Luke", ch) for ch in range(1, 25)],
        *[(f"John", ch) for ch in range(1, 22)],
        *[(f"Acts", ch) for ch in range(1, 29)],
        *[(f"Romans", ch) for ch in range(1, 17)],
        *[(f"1 Corinthians", ch) for ch in range(1, 17)],
        *[(f"2 Corinthians", ch) for ch in range(1, 14)],
        *[(f"Galatians", ch) for ch in range(1, 7)],
        *[(f"Ephesians", ch) for ch in range(1, 7)],
        *[(f"Philippians", ch) for ch in range(1, 5)],
        *[(f"Colossians", ch) for ch in range(1, 5)],
        *[(f"1 Thessalonians", ch) for ch in range(1, 6)],
        *[(f"2 Thessalonians", ch) for ch in range(1, 4)],
        *[(f"1 Timothy", ch) for ch in range(1, 7)],
        *[(f"2 Timothy", ch) for ch in range(1, 5)],
        *[(f"Titus", ch) for ch in range(1, 4)],
        ("Philemon", 1),
        *[(f"Hebrews", ch) for ch in range(1, 14)],
        *[(f"James", ch) for ch in range(1, 6)],
        *[(f"1 Peter", ch) for ch in range(1, 6)],
        *[(f"2 Peter", ch) for ch in range(1, 4)],
        *[(f"1 John", ch) for ch in range(1, 6)],
        ("2 John", 1), ("3 John", 1), ("Jude", 1),
        *[(f"Revelation", ch) for ch in range(1, 23)],
    ]

    # Batch OT into groups of 3 chapters, pair with one NT chapter per day
    days = []
    ot_idx = 0
    nt_idx = 0
    day = 1

    while day <= 365:
        # OT: up to 3 chapters
        ot_parts = []
        for _ in range(3):
            if ot_idx < len(ot_sequence):
                book, ch = ot_sequence[ot_idx]
                ot_parts.append(f"{book} {ch}")
                ot_idx += 1

        # NT: 1 chapter (cycle if exhausted)
        nt_book, nt_ch = nt_sequence[nt_idx % len(nt_sequence)]
        nt_idx += 1

        ot_str = "; ".join(ot_parts) if ot_parts else "Psalm 119"
        passages = f"{ot_str} | NT: {nt_book} {nt_ch}"
        key_verse = _nt_key_verse(nt_book, nt_ch) if (nt_ch, nt_book) else f"{nt_book} {nt_ch}:1"

        days.append((passages, key_verse))
        day += 1

    return days


OT_NT_YEAR = _build_ot_nt_year()


# ── 5. Chronological Bible in 1 Year ────────────────────────────────────────
# Events in historical order (simplified, well-known ordering)

CHRONOLOGICAL_YEAR = [
    # Creation & Patriarchs (Days 1–40)
    ("Genesis 1–2",             "Genesis 1:1"),
    ("Genesis 3–5",             "Genesis 3:15"),
    ("Genesis 6–8",             "Genesis 6:22"),
    ("Genesis 9–11",            "Genesis 9:13"),
    ("Genesis 12–14",           "Genesis 12:1"),
    ("Genesis 15–17",           "Genesis 15:6"),
    ("Genesis 18–20",           "Genesis 18:14"),
    ("Genesis 21–23",           "Genesis 21:1"),
    ("Genesis 24–25",           "Genesis 24:67"),
    ("Genesis 26–28",           "Genesis 28:15"),
    ("Genesis 29–31",           "Genesis 29:20"),
    ("Genesis 32–34",           "Genesis 32:28"),
    ("Genesis 35–37",           "Genesis 37:5"),
    ("Genesis 38–40",           "Genesis 39:9"),
    ("Genesis 41–43",           "Genesis 41:16"),
    ("Genesis 44–46",           "Genesis 45:5"),
    ("Genesis 47–50",           "Genesis 50:20"),
    ("Job 1–5",                 "Job 1:21"),
    ("Job 6–10",                "Job 8:3"),
    ("Job 11–15",               "Job 13:15"),
    ("Job 16–20",               "Job 19:25"),
    ("Job 21–25",               "Job 23:10"),
    ("Job 26–31",               "Job 28:28"),
    ("Job 32–37",               "Job 37:5"),
    ("Job 38–42",               "Job 42:5"),
    ("Exodus 1–4",              "Exodus 3:14"),
    ("Exodus 5–8",              "Exodus 7:5"),
    ("Exodus 9–12",             "Exodus 12:13"),
    ("Exodus 13–16",            "Exodus 14:14"),
    ("Exodus 17–20",            "Exodus 20:3"),
    ("Exodus 21–24",            "Exodus 22:22"),
    ("Exodus 25–28",            "Exodus 25:8"),
    ("Exodus 29–32",            "Exodus 32:26"),
    ("Exodus 33–36",            "Exodus 33:14"),
    ("Exodus 37–40",            "Exodus 40:34"),
    ("Leviticus 1–4",           "Leviticus 1:4"),
    ("Leviticus 5–8",           "Leviticus 6:13"),
    ("Leviticus 9–12",          "Leviticus 11:45"),
    ("Leviticus 13–16",         "Leviticus 16:30"),
    ("Leviticus 17–20",         "Leviticus 19:18"),
    # Wilderness & Law (Days 41–80)
    ("Leviticus 21–24",         "Leviticus 22:32"),
    ("Leviticus 25–27",         "Leviticus 25:10"),
    ("Numbers 1–3",             "Numbers 2:34"),
    ("Numbers 4–6",             "Numbers 6:24"),
    ("Numbers 7–9",             "Numbers 9:15"),
    ("Numbers 10–12",           "Numbers 11:23"),
    ("Numbers 13–15",           "Numbers 14:24"),
    ("Numbers 16–18",           "Numbers 16:5"),
    ("Numbers 19–21",           "Numbers 21:8"),
    ("Numbers 22–24",           "Numbers 23:19"),
    ("Numbers 25–27",           "Numbers 27:17"),
    ("Numbers 28–30",           "Numbers 28:2"),
    ("Numbers 31–33",           "Numbers 32:23"),
    ("Numbers 34–36",           "Numbers 36:13"),
    ("Deuteronomy 1–3",         "Deuteronomy 1:30"),
    ("Deuteronomy 4–6",         "Deuteronomy 6:4"),
    ("Deuteronomy 7–9",         "Deuteronomy 8:3"),
    ("Deuteronomy 10–12",       "Deuteronomy 10:12"),
    ("Deuteronomy 13–16",       "Deuteronomy 15:11"),
    ("Deuteronomy 17–20",       "Deuteronomy 18:15"),
    ("Deuteronomy 21–23",       "Deuteronomy 22:5"),
    ("Deuteronomy 24–27",       "Deuteronomy 25:4"),
    ("Deuteronomy 28–30",       "Deuteronomy 30:19"),
    ("Deuteronomy 31–34",       "Deuteronomy 31:6"),
    # Conquest & Judges (Days 65–100)
    ("Joshua 1–4",              "Joshua 1:9"),
    ("Joshua 5–8",              "Joshua 6:20"),
    ("Joshua 9–12",             "Joshua 10:42"),
    ("Joshua 13–16",            "Joshua 14:12"),
    ("Joshua 17–20",            "Joshua 17:18"),
    ("Joshua 21–24",            "Joshua 24:15"),
    ("Judges 1–3",              "Judges 2:16"),
    ("Judges 4–6",              "Judges 6:12"),
    ("Judges 7–9",              "Judges 7:7"),
    ("Judges 10–12",            "Judges 11:29"),
    ("Judges 13–15",            "Judges 13:5"),
    ("Judges 16–18",            "Judges 16:28"),
    ("Judges 19–21",            "Judges 21:25"),
    ("Ruth 1–4",                "Ruth 1:16"),
    ("1 Samuel 1–3",            "1 Samuel 3:10"),
    ("1 Samuel 4–7",            "1 Samuel 7:12"),
    ("1 Samuel 8–11",           "1 Samuel 8:7"),
    ("1 Samuel 12–14",          "1 Samuel 12:24"),
    ("1 Samuel 15–17",          "1 Samuel 17:45"),
    ("1 Samuel 18–20",          "1 Samuel 18:14"),
    # Kingdom (Days 101–140)
    ("1 Samuel 21–24",          "1 Samuel 23:14"),
    ("1 Samuel 25–28",          "1 Samuel 26:21"),
    ("1 Samuel 29–31",          "1 Samuel 31:13"),
    ("Psalm 18; 2 Samuel 1–2",  "Psalm 18:2"),
    ("2 Samuel 3–5",            "2 Samuel 5:4"),
    ("Psalm 60; 2 Samuel 6–7",  "Psalm 60:12"),
    ("2 Samuel 8–10",           "2 Samuel 9:7"),
    ("Psalm 51; 2 Samuel 11–12","Psalm 51:10"),
    ("2 Samuel 13–15",          "2 Samuel 15:13"),
    ("2 Samuel 16–18",          "2 Samuel 18:33"),
    ("2 Samuel 19–21",          "2 Samuel 22:3"),
    ("2 Samuel 22–24",          "2 Samuel 22:47"),
    ("Psalm 72; 1 Kings 1–2",   "Psalm 72:18"),
    ("1 Kings 3–5",             "1 Kings 3:9"),
    ("Proverbs 1–4",            "Proverbs 3:5"),
    ("Proverbs 5–8",            "Proverbs 8:11"),
    ("Proverbs 9–12",           "Proverbs 11:2"),
    ("Proverbs 13–16",          "Proverbs 16:3"),
    ("Proverbs 17–20",          "Proverbs 18:10"),
    ("Proverbs 21–24",          "Proverbs 21:21"),
    # Psalms & Wisdom (Days 141–170)
    ("Proverbs 25–28",          "Proverbs 27:1"),
    ("Proverbs 29–31",          "Proverbs 31:30"),
    ("Ecclesiastes 1–4",        "Ecclesiastes 3:1"),
    ("Ecclesiastes 5–8",        "Ecclesiastes 5:2"),
    ("Ecclesiastes 9–12",       "Ecclesiastes 12:13"),
    ("Song of Solomon 1–4",     "Song of Solomon 2:4"),
    ("Song of Solomon 5–8",     "Song of Solomon 8:7"),
    ("1 Kings 6–8",             "1 Kings 8:27"),
    ("1 Kings 9–11",            "1 Kings 11:11"),
    ("Psalm 73–77",             "Psalm 73:26"),
    ("Psalm 78–82",             "Psalm 78:4"),
    ("Psalm 83–87",             "Psalm 86:5"),
    ("Psalm 88–92",             "Psalm 91:1"),
    ("Psalm 93–97",             "Psalm 96:3"),
    ("Psalm 98–102",            "Psalm 100:1"),
    ("Psalm 103–107",           "Psalm 103:12"),
    ("Psalm 108–112",           "Psalm 112:1"),
    ("Psalm 113–118",           "Psalm 118:24"),
    ("Psalm 119:1–88",          "Psalm 119:11"),
    ("Psalm 119:89–176",        "Psalm 119:105"),
    # Divided Kingdom (Days 171–220)
    ("Psalm 120–127",           "Psalm 121:1"),
    ("Psalm 128–134",           "Psalm 130:5"),
    ("Psalm 135–141",           "Psalm 139:1"),
    ("Psalm 142–150",           "Psalm 145:3"),
    ("1 Kings 12–14",           "1 Kings 12:24"),
    ("1 Kings 15–17",           "1 Kings 17:1"),
    ("1 Kings 18–20",           "1 Kings 18:21"),
    ("1 Kings 21–22",           "1 Kings 21:29"),
    ("2 Kings 1–3",             "2 Kings 2:11"),
    ("2 Kings 4–6",             "2 Kings 5:13"),
    ("2 Kings 7–9",             "2 Kings 7:9"),
    ("2 Kings 10–12",           "2 Kings 11:17"),
    ("2 Kings 13–15",           "2 Kings 13:23"),
    ("2 Kings 16–18",           "2 Kings 18:5"),
    ("2 Kings 19–21",           "2 Kings 19:31"),
    ("2 Kings 22–25",           "2 Kings 22:2"),
    ("Joel 1–3",                "Joel 2:13"),
    ("Jonah 1–4",               "Jonah 2:9"),
    ("Amos 1–4",                "Amos 3:7"),
    ("Amos 5–9",                "Amos 5:24"),
    # Prophets (Days 221–280)
    ("Hosea 1–4",               "Hosea 2:23"),
    ("Hosea 5–9",               "Hosea 6:6"),
    ("Hosea 10–14",             "Hosea 14:9"),
    ("Micah 1–4",               "Micah 5:2"),
    ("Micah 5–7",               "Micah 6:8"),
    ("Isaiah 1–4",              "Isaiah 1:18"),
    ("Isaiah 5–8",              "Isaiah 6:8"),
    ("Isaiah 9–12",             "Isaiah 9:6"),
    ("Isaiah 13–17",            "Isaiah 14:27"),
    ("Isaiah 18–22",            "Isaiah 22:22"),
    ("Isaiah 23–27",            "Isaiah 26:3"),
    ("Isaiah 28–32",            "Isaiah 30:15"),
    ("Isaiah 33–37",            "Isaiah 33:22"),
    ("Isaiah 38–42",            "Isaiah 40:31"),
    ("Isaiah 43–47",            "Isaiah 43:1"),
    ("Isaiah 48–52",            "Isaiah 53:5"),
    ("Isaiah 53–57",            "Isaiah 55:11"),
    ("Isaiah 58–62",            "Isaiah 61:1"),
    ("Isaiah 63–66",            "Isaiah 64:8"),
    ("2 Chronicles 1–5",        "2 Chronicles 1:10"),
    ("2 Chronicles 6–10",       "2 Chronicles 7:14"),
    ("2 Chronicles 11–15",      "2 Chronicles 15:7"),
    ("2 Chronicles 16–20",      "2 Chronicles 16:9"),
    ("2 Chronicles 21–25",      "2 Chronicles 20:12"),
    ("2 Chronicles 26–30",      "2 Chronicles 29:36"),
    ("2 Chronicles 31–36",      "2 Chronicles 34:27"),
    ("Nahum 1–3",               "Nahum 1:7"),
    ("Zephaniah 1–3",           "Zephaniah 3:17"),
    ("Habakkuk 1–3",            "Habakkuk 2:4"),
    ("Jeremiah 1–4",            "Jeremiah 1:5"),
    # Exile & Return (Days 281–330)
    ("Jeremiah 5–8",            "Jeremiah 6:16"),
    ("Jeremiah 9–12",           "Jeremiah 9:23"),
    ("Jeremiah 13–16",          "Jeremiah 15:16"),
    ("Jeremiah 17–20",          "Jeremiah 17:9"),
    ("Jeremiah 21–24",          "Jeremiah 23:5"),
    ("Jeremiah 25–28",          "Jeremiah 29:11"),
    ("Jeremiah 29–32",          "Jeremiah 31:31"),
    ("Jeremiah 33–36",          "Jeremiah 33:3"),
    ("Jeremiah 37–40",          "Jeremiah 37:17"),
    ("Jeremiah 41–44",          "Jeremiah 42:11"),
    ("Jeremiah 45–48",          "Jeremiah 45:5"),
    ("Jeremiah 49–52",          "Jeremiah 52:31"),
    ("Lamentations 1–3",        "Lamentations 3:22"),
    ("Lamentations 4–5",        "Lamentations 3:23"),
    ("Ezekiel 1–4",             "Ezekiel 3:17"),
    ("Ezekiel 5–8",             "Ezekiel 7:27"),
    ("Ezekiel 9–12",            "Ezekiel 11:19"),
    ("Ezekiel 13–16",           "Ezekiel 16:60"),
    ("Ezekiel 17–20",           "Ezekiel 18:32"),
    ("Ezekiel 21–24",           "Ezekiel 22:30"),
    ("Ezekiel 25–28",           "Ezekiel 28:12"),
    ("Ezekiel 29–32",           "Ezekiel 33:11"),
    ("Ezekiel 33–36",           "Ezekiel 36:26"),
    ("Ezekiel 37–40",           "Ezekiel 37:1"),
    ("Ezekiel 41–44",           "Ezekiel 43:7"),
    ("Ezekiel 45–48",           "Ezekiel 47:12"),
    ("Daniel 1–3",              "Daniel 2:44"),
    ("Daniel 4–6",              "Daniel 6:10"),
    ("Daniel 7–9",              "Daniel 9:24"),
    ("Daniel 10–12",            "Daniel 12:3"),
    # Return & Gospels (Days 331–365)
    ("Ezra 1–4",                "Ezra 3:11"),
    ("Ezra 5–7",                "Ezra 7:10"),
    ("Ezra 8–10",               "Ezra 10:11"),
    ("Haggai 1–2",              "Haggai 2:9"),
    ("Zechariah 1–4",           "Zechariah 4:6"),
    ("Zechariah 5–9",           "Zechariah 8:8"),
    ("Zechariah 10–14",         "Zechariah 12:10"),
    ("Nehemiah 1–4",            "Nehemiah 4:20"),
    ("Nehemiah 5–7",            "Nehemiah 6:3"),
    ("Nehemiah 8–10",           "Nehemiah 8:10"),
    ("Nehemiah 11–13",          "Nehemiah 13:22"),
    ("Esther 1–5",              "Esther 4:14"),
    ("Esther 6–10",             "Esther 8:17"),
    ("Malachi 1–4",             "Malachi 3:10"),
    ("Matthew 1–4",             "Matthew 1:21"),
    ("Matthew 5–7",             "Matthew 5:3"),
    ("Matthew 8–11",            "Matthew 11:28"),
    ("Matthew 12–15",           "Matthew 13:44"),
    ("Matthew 16–19",           "Matthew 16:16"),
    ("Matthew 20–22",           "Matthew 21:9"),
    ("Matthew 23–25",           "Matthew 25:40"),
    ("Matthew 26–28",           "Matthew 28:19"),
    ("Mark 1–4",                "Mark 1:15"),
    ("Mark 5–8",                "Mark 8:29"),
    ("Mark 9–12",               "Mark 10:45"),
    ("Mark 13–16",              "Mark 16:6"),
    ("Luke 1–4",                "Luke 2:11"),
    ("Luke 5–8",                "Luke 6:27"),
    ("Luke 9–12",               "Luke 9:23"),
    ("Luke 13–16",              "Luke 15:7"),
    ("Luke 17–20",              "Luke 19:10"),
    ("Luke 21–24",              "Luke 24:6"),
    ("John 1–4",                "John 1:14"),
    ("John 5–8",                "John 6:35"),
    ("John 9–13",               "John 11:25"),
    ("John 14–17",              "John 14:6"),
    ("John 18–21",              "John 3:16"),
]

# Trim/pad to 365
CHRONOLOGICAL_YEAR = CHRONOLOGICAL_YEAR[:365]
while len(CHRONOLOGICAL_YEAR) < 365:
    CHRONOLOGICAL_YEAR.append(("Acts 1–4", "Acts 1:8"))


# ── Command ───────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed the database with curated reading plans."

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding reading plans…")

        make_plan(
            name="Gospels in 30 Days",
            description=(
                "Read all four Gospels — Matthew, Mark, Luke, and John — "
                "in a single month. A great starting point for anyone wanting "
                "to know Jesus through the eyes of four different witnesses."
            ),
            days_data=GOSPELS_30,
        )
        self.stdout.write("  ✓ Gospels in 30 Days")

        make_plan(
            name="Psalms & Proverbs in 30 Days",
            description=(
                "A month in the wisdom books. Daily readings combine a handful "
                "of Psalms with a chapter of Proverbs — morning praise and "
                "practical wisdom for everyday life."
            ),
            days_data=PSALMS_PROVERBS_30,
        )
        self.stdout.write("  ✓ Psalms & Proverbs in 30 Days")

        make_plan(
            name="New Testament in 1 Year",
            description=(
                "Read the entire New Testament in a year at a leisurely pace — "
                "roughly one chapter per day, with time to revisit beloved "
                "passages. Ideal if the Old Testament feels like too big a "
                "commitment right now."
            ),
            days_data=NT_YEAR,
        )
        self.stdout.write("  ✓ New Testament in 1 Year")

        make_plan(
            name="Old & New Testament Together — 1 Year",
            description=(
                "Read three Old Testament chapters and one New Testament "
                "chapter every day for a year. You'll finish the entire Bible "
                "while keeping the story of Jesus running alongside the Hebrew "
                "Scriptures. The classic Bible-in-a-year experience."
            ),
            days_data=OT_NT_YEAR,
        )
        self.stdout.write("  ✓ Old & New Testament Together — 1 Year")

        make_plan(
            name="Chronological Bible in 1 Year",
            description=(
                "Read Scripture in the order events actually happened — "
                "from Creation through the Patriarchs, Exodus, the Kingdom, "
                "the Prophets, the Exile, and finally the Gospels. History "
                "comes alive when it unfolds in sequence."
            ),
            days_data=CHRONOLOGICAL_YEAR,
        )
        self.stdout.write("  ✓ Chronological Bible in 1 Year")

        self.stdout.write(self.style.SUCCESS("\nAll plans seeded successfully."))
        self.stdout.write(
            "Users can browse and select plans at /plans/\n"
            "Note: 'Book-by-book' plans are generated dynamically per user selection — "
            "no seeding needed for those."
        )
