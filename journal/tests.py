import json
from datetime import date, time
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings

from .models import DailyVerse, Profile, PushSubscription
from .verses import sample_for, verse_for

PLAIN_STATIC = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
SUB = {"endpoint": "https://push.example/abc", "keys": {"p256dh": "p" * 20, "auth": "a" * 10}}


class VerseTests(TestCase):
    def test_sample_covers_every_day_of_month(self):
        for d in range(1, 32):
            v = sample_for(date(2026, 12, d))
            self.assertTrue(v["reference"] and v["text"])

    def test_seed_month(self):
        call_command("seed_daily_verses", month="2027-02", stdout=mock.MagicMock())
        self.assertEqual(DailyVerse.objects.filter(date__year=2027, date__month=2).count(), 28)

    def test_saved_verse_wins_over_sample(self):
        DailyVerse.objects.create(date=date(2026, 12, 25), reference="Luke 2:11", text="x", source="manual")
        self.assertEqual(verse_for(date(2026, 12, 25))["reference"], "Luke 2:11")

    @override_settings(DAILY_VERSE_SOURCE="ourmanna")
    def test_feed_failure_falls_back_to_sample(self):
        with mock.patch("journal.verses.fetch_online", side_effect=OSError("offline")):
            v = verse_for(date.today(), allow_fetch=True)
        self.assertEqual(v["source"], "sample")
        self.assertTrue(DailyVerse.objects.filter(date=date.today()).exists())


@override_settings(VAPID_PUBLIC_KEY="pub", VAPID_PRIVATE_KEY="priv", STORAGES=PLAIN_STATIC)
class PushTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("reader", password="pw-for-tests-only")
        self.client.force_login(self.user)

    def test_pwa_files(self):
        self.assertEqual(self.client.get("/manifest.webmanifest").json()["display"], "standalone")
        sw = self.client.get("/sw.js")
        self.assertEqual(sw["Content-Type"], "application/javascript")
        self.assertIn("showNotification", sw.content.decode())

    def test_pages_render(self):
        for url in ("/today/", "/verse/", "/settings/notifications/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_subscribe_and_unsubscribe(self):
        r = self.client.post("/push/subscribe/", json.dumps({**SUB, "timezone": "America/New_York"}),
                             content_type="application/json")
        self.assertEqual(r.json()["devices"], 1)
        p = Profile.objects.get(user=self.user)
        self.assertTrue(p.verse_notifications)
        self.assertEqual(p.timezone, "America/New_York")
        self.client.post("/push/unsubscribe/", json.dumps({"endpoint": SUB["endpoint"]}),
                         content_type="application/json")
        self.assertFalse(PushSubscription.objects.exists())

    def test_send_daily_verse_once_per_day(self):
        PushSubscription.objects.create(user=self.user, endpoint=SUB["endpoint"],
                                        p256dh="p", auth="a")
        Profile.objects.update_or_create(user=self.user, defaults={
            "verse_notifications": True, "notify_time": time(0, 0), "timezone": "UTC"})
        with mock.patch("pywebpush.webpush") as wp, \
             mock.patch("journal.verses.fetch_online", side_effect=OSError("offline")):
            call_command("send_daily_verse", stdout=mock.MagicMock())
            call_command("send_daily_verse", stdout=mock.MagicMock())
        self.assertEqual(wp.call_count, 1)
        payload = json.loads(wp.call_args.kwargs["data"])
        self.assertIn("Verse of the Day", payload["title"])
