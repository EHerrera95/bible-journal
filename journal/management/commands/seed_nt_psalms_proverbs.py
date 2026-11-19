# journal/management/commands/seed_nt_psalms_proverbs.py
#
# Run with:  python manage.py seed_nt_psalms_proverbs
#
# This command:
#   1. Deletes "New Testament in 1 Year"
#   2. Deletes "Psalms & Proverbs in 30 Days"
#   3. Creates "New Testament, Psalms & Proverbs in 1 Year" (365 days)
#
# Structure:
#   Days   1–260  → NT one chapter per day (Matthew → Revelation)
#   Days 261–334  → Psalms (~two per day, Psalm 119 split into 4 sections)
#   Days 335–365  → Proverbs one chapter per day

from django.core.management.base import BaseCommand
from journal.models import ReadingPlan, PlanDay

OLD_PLANS = [
    "New Testament in 1 Year",
    "Psalms & Proverbs in 30 Days",
]

NEW_PLAN_NAME = "New Testament, Psalms & Proverbs in 1 Year"

KEY_VERSES = {
    "Matthew 1": "Matthew 1:21",
    "Matthew 5": "Matthew 5:3",
    "Matthew 6": "Matthew 6:33",
    "Matthew 11": "Matthew 11:28",
    "Matthew 16": "Matthew 16:16",
    "Matthew 28": "Matthew 28:19",
    "Mark 1": "Mark 1:15",
    "Mark 10": "Mark 10:45",
    "Mark 16": "Mark 16:6",
    "Luke 2": "Luke 2:11",
    "Luke 4": "Luke 4:18",
    "Luke 15": "Luke 15:7",
    "Luke 19": "Luke 19:10",
    "Luke 24": "Luke 24:6",
    "John 1": "John 1:1",
    "John 3": "John 3:16",
    "John 6": "John 6:35",
    "John 11": "John 11:25",
    "John 14": "John 14:6",
    "John 15": "John 15:5",
    "John 17": "John 17:21",
    "John 21": "John 21:17",
    "Acts 1": "Acts 1:8",
    "Acts 2": "Acts 2:38",
    "Romans 1": "Romans 1:16",
    "Romans 3": "Romans 3:23",
    "Romans 5": "Romans 5:8",
    "Romans 8": "Romans 8:28",
    "Romans 10": "Romans 10:9",
    "Romans 12": "Romans 12:2",
    "1 Corinthians 13": "1 Corinthians 13:4",
    "Galatians 2": "Galatians 2:20",
    "Ephesians 2": "Ephesians 2:8",
    "Philippians 4": "Philippians 4:13",
    "Colossians 3": "Colossians 3:23",
    "Hebrews 11": "Hebrews 11:1",
    "Hebrews 12": "Hebrews 12:1",
    "James 1": "James 1:5",
    "1 Peter 5": "1 Peter 5:7",
    "1 John 4": "1 John 4:19",
    "Revelation 1": "Revelation 1:8",
    "Revelation 21": "Revelation 21:4",
    "Revelation 22": "Revelation 22:20",
    "Psalm 1, 2": "Psalm 1:1",
    "Psalm 23, 24": "Psalm 23:1",
    "Psalm 51, 52": "Psalm 51:10",
    "Psalm 91, 92": "Psalm 91:1",
    "Psalm 103, 104": "Psalm 103:12",
    "Psalm 119:1-40": "Psalm 119:11",
    "Psalm 119:121-176": "Psalm 119:105",
    "Psalm 138, 139": "Psalm 139:14",
    "Psalm 148, 149, 150": "Psalm 148:1",
    "Proverbs 3": "Proverbs 3:5",
    "Proverbs 16": "Proverbs 16:3",
    "Proverbs 31": "Proverbs 31:30",
}

DAYS = [
    # ── NEW TESTAMENT (Days 1–260) ─────────────────────────────────────────
    # Matthew (1–28)
    (1,   "Matthew 1"),
    (2,   "Matthew 2"),
    (3,   "Matthew 3"),
    (4,   "Matthew 4"),
    (5,   "Matthew 5"),
    (6,   "Matthew 6"),
    (7,   "Matthew 7"),
    (8,   "Matthew 8"),
    (9,   "Matthew 9"),
    (10,  "Matthew 10"),
    (11,  "Matthew 11"),
    (12,  "Matthew 12"),
    (13,  "Matthew 13"),
    (14,  "Matthew 14"),
    (15,  "Matthew 15"),
    (16,  "Matthew 16"),
    (17,  "Matthew 17"),
    (18,  "Matthew 18"),
    (19,  "Matthew 19"),
    (20,  "Matthew 20"),
    (21,  "Matthew 21"),
    (22,  "Matthew 22"),
    (23,  "Matthew 23"),
    (24,  "Matthew 24"),
    (25,  "Matthew 25"),
    (26,  "Matthew 26"),
    (27,  "Matthew 27"),
    (28,  "Matthew 28"),
    # Mark (1–16)
    (29,  "Mark 1"),
    (30,  "Mark 2"),
    (31,  "Mark 3"),
    (32,  "Mark 4"),
    (33,  "Mark 5"),
    (34,  "Mark 6"),
    (35,  "Mark 7"),
    (36,  "Mark 8"),
    (37,  "Mark 9"),
    (38,  "Mark 10"),
    (39,  "Mark 11"),
    (40,  "Mark 12"),
    (41,  "Mark 13"),
    (42,  "Mark 14"),
    (43,  "Mark 15"),
    (44,  "Mark 16"),
    # Luke (1–24)
    (45,  "Luke 1"),
    (46,  "Luke 2"),
    (47,  "Luke 3"),
    (48,  "Luke 4"),
    (49,  "Luke 5"),
    (50,  "Luke 6"),
    (51,  "Luke 7"),
    (52,  "Luke 8"),
    (53,  "Luke 9"),
    (54,  "Luke 10"),
    (55,  "Luke 11"),
    (56,  "Luke 12"),
    (57,  "Luke 13"),
    (58,  "Luke 14"),
    (59,  "Luke 15"),
    (60,  "Luke 16"),
    (61,  "Luke 17"),
    (62,  "Luke 18"),
    (63,  "Luke 19"),
    (64,  "Luke 20"),
    (65,  "Luke 21"),
    (66,  "Luke 22"),
    (67,  "Luke 23"),
    (68,  "Luke 24"),
    # John (1–21)
    (69,  "John 1"),
    (70,  "John 2"),
    (71,  "John 3"),
    (72,  "John 4"),
    (73,  "John 5"),
    (74,  "John 6"),
    (75,  "John 7"),
    (76,  "John 8"),
    (77,  "John 9"),
    (78,  "John 10"),
    (79,  "John 11"),
    (80,  "John 12"),
    (81,  "John 13"),
    (82,  "John 14"),
    (83,  "John 15"),
    (84,  "John 16"),
    (85,  "John 17"),
    (86,  "John 18"),
    (87,  "John 19"),
    (88,  "John 20"),
    (89,  "John 21"),
    # Acts (1–28)
    (90,  "Acts 1"),
    (91,  "Acts 2"),
    (92,  "Acts 3"),
    (93,  "Acts 4"),
    (94,  "Acts 5"),
    (95,  "Acts 6"),
    (96,  "Acts 7"),
    (97,  "Acts 8"),
    (98,  "Acts 9"),
    (99,  "Acts 10"),
    (100, "Acts 11"),
    (101, "Acts 12"),
    (102, "Acts 13"),
    (103, "Acts 14"),
    (104, "Acts 15"),
    (105, "Acts 16"),
    (106, "Acts 17"),
    (107, "Acts 18"),
    (108, "Acts 19"),
    (109, "Acts 20"),
    (110, "Acts 21"),
    (111, "Acts 22"),
    (112, "Acts 23"),
    (113, "Acts 24"),
    (114, "Acts 25"),
    (115, "Acts 26"),
    (116, "Acts 27"),
    (117, "Acts 28"),
    # Romans (1–16)
    (118, "Romans 1"),
    (119, "Romans 2"),
    (120, "Romans 3"),
    (121, "Romans 4"),
    (122, "Romans 5"),
    (123, "Romans 6"),
    (124, "Romans 7"),
    (125, "Romans 8"),
    (126, "Romans 9"),
    (127, "Romans 10"),
    (128, "Romans 11"),
    (129, "Romans 12"),
    (130, "Romans 13"),
    (131, "Romans 14"),
    (132, "Romans 15"),
    (133, "Romans 16"),
    # 1 Corinthians (1–16)
    (134, "1 Corinthians 1"),
    (135, "1 Corinthians 2"),
    (136, "1 Corinthians 3"),
    (137, "1 Corinthians 4"),
    (138, "1 Corinthians 5"),
    (139, "1 Corinthians 6"),
    (140, "1 Corinthians 7"),
    (141, "1 Corinthians 8"),
    (142, "1 Corinthians 9"),
    (143, "1 Corinthians 10"),
    (144, "1 Corinthians 11"),
    (145, "1 Corinthians 12"),
    (146, "1 Corinthians 13"),
    (147, "1 Corinthians 14"),
    (148, "1 Corinthians 15"),
    (149, "1 Corinthians 16"),
    # 2 Corinthians (1–13)
    (150, "2 Corinthians 1"),
    (151, "2 Corinthians 2"),
    (152, "2 Corinthians 3"),
    (153, "2 Corinthians 4"),
    (154, "2 Corinthians 5"),
    (155, "2 Corinthians 6"),
    (156, "2 Corinthians 7"),
    (157, "2 Corinthians 8"),
    (158, "2 Corinthians 9"),
    (159, "2 Corinthians 10"),
    (160, "2 Corinthians 11"),
    (161, "2 Corinthians 12"),
    (162, "2 Corinthians 13"),
    # Galatians (1–6)
    (163, "Galatians 1"),
    (164, "Galatians 2"),
    (165, "Galatians 3"),
    (166, "Galatians 4"),
    (167, "Galatians 5"),
    (168, "Galatians 6"),
    # Ephesians (1–6)
    (169, "Ephesians 1"),
    (170, "Ephesians 2"),
    (171, "Ephesians 3"),
    (172, "Ephesians 4"),
    (173, "Ephesians 5"),
    (174, "Ephesians 6"),
    # Philippians (1–4)
    (175, "Philippians 1"),
    (176, "Philippians 2"),
    (177, "Philippians 3"),
    (178, "Philippians 4"),
    # Colossians (1–4)
    (179, "Colossians 1"),
    (180, "Colossians 2"),
    (181, "Colossians 3"),
    (182, "Colossians 4"),
    # 1 Thessalonians (1–5)
    (183, "1 Thessalonians 1"),
    (184, "1 Thessalonians 2"),
    (185, "1 Thessalonians 3"),
    (186, "1 Thessalonians 4"),
    (187, "1 Thessalonians 5"),
    # 2 Thessalonians (1–3)
    (188, "2 Thessalonians 1"),
    (189, "2 Thessalonians 2"),
    (190, "2 Thessalonians 3"),
    # 1 Timothy (1–6)
    (191, "1 Timothy 1"),
    (192, "1 Timothy 2"),
    (193, "1 Timothy 3"),
    (194, "1 Timothy 4"),
    (195, "1 Timothy 5"),
    (196, "1 Timothy 6"),
    # 2 Timothy (1–4)
    (197, "2 Timothy 1"),
    (198, "2 Timothy 2"),
    (199, "2 Timothy 3"),
    (200, "2 Timothy 4"),
    # Titus (1–3)
    (201, "Titus 1"),
    (202, "Titus 2"),
    (203, "Titus 3"),
    # Philemon
    (204, "Philemon"),
    # Hebrews (1–13)
    (205, "Hebrews 1"),
    (206, "Hebrews 2"),
    (207, "Hebrews 3"),
    (208, "Hebrews 4"),
    (209, "Hebrews 5"),
    (210, "Hebrews 6"),
    (211, "Hebrews 7"),
    (212, "Hebrews 8"),
    (213, "Hebrews 9"),
    (214, "Hebrews 10"),
    (215, "Hebrews 11"),
    (216, "Hebrews 12"),
    (217, "Hebrews 13"),
    # James (1–5)
    (218, "James 1"),
    (219, "James 2"),
    (220, "James 3"),
    (221, "James 4"),
    (222, "James 5"),
    # 1 Peter (1–5)
    (223, "1 Peter 1"),
    (224, "1 Peter 2"),
    (225, "1 Peter 3"),
    (226, "1 Peter 4"),
    (227, "1 Peter 5"),
    # 2 Peter (1–3)
    (228, "2 Peter 1"),
    (229, "2 Peter 2"),
    (230, "2 Peter 3"),
    # 1 John (1–5)
    (231, "1 John 1"),
    (232, "1 John 2"),
    (233, "1 John 3"),
    (234, "1 John 4"),
    (235, "1 John 5"),
    # 2 John, 3 John, Jude
    (236, "2 John"),
    (237, "3 John"),
    (238, "Jude"),
    # Revelation (1–22)
    (239, "Revelation 1"),
    (240, "Revelation 2"),
    (241, "Revelation 3"),
    (242, "Revelation 4"),
    (243, "Revelation 5"),
    (244, "Revelation 6"),
    (245, "Revelation 7"),
    (246, "Revelation 8"),
    (247, "Revelation 9"),
    (248, "Revelation 10"),
    (249, "Revelation 11"),
    (250, "Revelation 12"),
    (251, "Revelation 13"),
    (252, "Revelation 14"),
    (253, "Revelation 15"),
    (254, "Revelation 16"),
    (255, "Revelation 17"),
    (256, "Revelation 18"),
    (257, "Revelation 19"),
    (258, "Revelation 20"),
    (259, "Revelation 21"),
    (260, "Revelation 22"),

    # ── PSALMS (Days 261–334) ──────────────────────────────────────────────
    (261, "Psalm 1, 2"),
    (262, "Psalm 3, 4"),
    (263, "Psalm 5, 6"),
    (264, "Psalm 7, 8"),
    (265, "Psalm 9, 10"),
    (266, "Psalm 11, 12"),
    (267, "Psalm 13, 14"),
    (268, "Psalm 15, 16"),
    (269, "Psalm 17, 18"),
    (270, "Psalm 19, 20"),
    (271, "Psalm 21, 22"),
    (272, "Psalm 23, 24"),
    (273, "Psalm 25, 26"),
    (274, "Psalm 27, 28"),
    (275, "Psalm 29, 30"),
    (276, "Psalm 31, 32"),
    (277, "Psalm 33, 34"),
    (278, "Psalm 35, 36"),
    (279, "Psalm 37, 38"),
    (280, "Psalm 39, 40"),
    (281, "Psalm 41, 42"),
    (282, "Psalm 43, 44"),
    (283, "Psalm 45, 46"),
    (284, "Psalm 47, 48"),
    (285, "Psalm 49, 50"),
    (286, "Psalm 51, 52"),
    (287, "Psalm 53, 54"),
    (288, "Psalm 55, 56"),
    (289, "Psalm 57, 58"),
    (290, "Psalm 59, 60"),
    (291, "Psalm 61, 62"),
    (292, "Psalm 63, 64"),
    (293, "Psalm 65, 66"),
    (294, "Psalm 67, 68"),
    (295, "Psalm 69, 70"),
    (296, "Psalm 71, 72"),
    (297, "Psalm 73, 74"),
    (298, "Psalm 75, 76"),
    (299, "Psalm 77, 78"),
    (300, "Psalm 79, 80"),
    (301, "Psalm 81, 82"),
    (302, "Psalm 83, 84"),
    (303, "Psalm 85, 86"),
    (304, "Psalm 87, 88"),
    (305, "Psalm 89, 90"),
    (306, "Psalm 91, 92"),
    (307, "Psalm 93, 94"),
    (308, "Psalm 95, 96"),
    (309, "Psalm 97, 98"),
    (310, "Psalm 99, 100"),
    (311, "Psalm 101, 102"),
    (312, "Psalm 103, 104"),
    (313, "Psalm 105, 106"),
    (314, "Psalm 107, 108"),
    (315, "Psalm 109, 110"),
    (316, "Psalm 111, 112"),
    (317, "Psalm 113, 114"),
    (318, "Psalm 115, 116"),
    (319, "Psalm 117, 118"),
    (320, "Psalm 119:1-40"),
    (321, "Psalm 119:41-80"),
    (322, "Psalm 119:81-120"),
    (323, "Psalm 119:121-176"),
    (324, "Psalm 120, 121, 122"),
    (325, "Psalm 123, 124, 125"),
    (326, "Psalm 126, 127, 128"),
    (327, "Psalm 129, 130, 131"),
    (328, "Psalm 132, 133, 134"),
    (329, "Psalm 135, 136, 137"),
    (330, "Psalm 138, 139"),
    (331, "Psalm 140, 141"),
    (332, "Psalm 142, 143, 144"),
    (333, "Psalm 145, 146, 147"),
    (334, "Psalm 148, 149, 150"),

    # ── PROVERBS (Days 335–365) ────────────────────────────────────────────
    (335, "Proverbs 1"),
    (336, "Proverbs 2"),
    (337, "Proverbs 3"),
    (338, "Proverbs 4"),
    (339, "Proverbs 5"),
    (340, "Proverbs 6"),
    (341, "Proverbs 7"),
    (342, "Proverbs 8"),
    (343, "Proverbs 9"),
    (344, "Proverbs 10"),
    (345, "Proverbs 11"),
    (346, "Proverbs 12"),
    (347, "Proverbs 13"),
    (348, "Proverbs 14"),
    (349, "Proverbs 15"),
    (350, "Proverbs 16"),
    (351, "Proverbs 17"),
    (352, "Proverbs 18"),
    (353, "Proverbs 19"),
    (354, "Proverbs 20"),
    (355, "Proverbs 21"),
    (356, "Proverbs 22"),
    (357, "Proverbs 23"),
    (358, "Proverbs 24"),
    (359, "Proverbs 25"),
    (360, "Proverbs 26"),
    (361, "Proverbs 27"),
    (362, "Proverbs 28"),
    (363, "Proverbs 29"),
    (364, "Proverbs 30"),
    (365, "Proverbs 31"),
]


def key_verse_for(passage):
    if passage in KEY_VERSES:
        return KEY_VERSES[passage]
    # Sensible fallback: first reference + :1
    import re
    first = passage.split(";")[0].split(",")[0].strip()
    m = re.match(r"^(.+?\s+[\d:]+)", first)
    base = m.group(1) if m else first
    # Strip verse sub-range to get a clean ref
    base = re.sub(r":\d+-\d+$", "", base).strip()
    return f"{base}:1"


class Command(BaseCommand):
    help = (
        "Replace 'New Testament in 1 Year' and 'Psalms & Proverbs in 30 Days' "
        "with the combined 'New Testament, Psalms & Proverbs in 1 Year' plan (365 days)."
    )

    def handle(self, *args, **kwargs):
        # ── Step 1: Delete old plans ─────────────────────────────────────────
        for name in OLD_PLANS:
            try:
                old = ReadingPlan.objects.get(name=name)
                days = old.days.count()
                old.delete()
                self.stdout.write(f"  ✓ Deleted '{name}' ({days} days).")
            except ReadingPlan.DoesNotExist:
                self.stdout.write(f"  — '{name}' not found, skipping.")

        # ── Step 2: Create new plan ──────────────────────────────────────────
        self.stdout.write(f"\n  Creating '{NEW_PLAN_NAME}'…")

        plan, created = ReadingPlan.objects.get_or_create(
            name=NEW_PLAN_NAME,
            defaults={
                "description": (
                    "Read the entire New Testament at one chapter a day "
                    "(Days 1–260), then the Book of Psalms at roughly two "
                    "psalms a day (Days 261–334), and finish with Proverbs "
                    "at one chapter a day (Days 335–365). A full year of "
                    "focused, manageable Scripture — start any day."
                )
            },
        )

        if not created:
            self.stdout.write("  Plan already exists — updating days only.")

        created_days = 0
        for day_num, passage in DAYS:
            kv = key_verse_for(passage)
            _, c = PlanDay.objects.get_or_create(
                plan=plan,
                day_number=day_num,
                defaults={"passages": passage, "key_verse_ref": kv},
            )
            if c:
                created_days += 1

        total = PlanDay.objects.filter(plan=plan).count()
        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Done.\n"
            f"  Plan:          '{plan.name}'\n"
            f"  Days created:  {created_days}\n"
            f"  Total days:    {total}\n"
            f"\n  Structure:\n"
            f"    Days   1–260  New Testament (one chapter/day)\n"
            f"    Days 261–334  Psalms (~two psalms/day)\n"
            f"    Days 335–365  Proverbs (one chapter/day)\n"
            f"\n  Available at /plans/"
        ))
