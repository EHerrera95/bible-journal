# Running Bible Journal on your phone

The site is now an installable web app (PWA). After you add it to your iPhone home
screen, it opens full-screen like a normal app, stays signed in for 90 days, and can
show **daily verse notifications** (iOS 16.4 or later). You don't need the App Store or
a Mac.

It needs a public **HTTPS** address, because phones can't reach `localhost` on your PC and
iOS only sends push notifications to HTTPS sites. The project is already set up for
Railway (`Procfile`, `RAILWAY_PUBLIC_DOMAIN` in settings), so these steps use Railway.

---

## 1. Deploy the web app (one time)

1. Push this repo to GitHub, then in Railway choose **New Project → Deploy from GitHub repo**.
2. Add a **PostgreSQL** database to the project (**New → Database → PostgreSQL**).
   Railway's disk is wiped on every deploy, so SQLite would lose your entries.
3. On the web service, open **Variables** and add:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (reference variable) |
   | `SECRET_KEY` | any long random string |
   | `DEBUG` | `False` |
   | `VAPID_PUBLIC_KEY` | from step 2 below |
   | `VAPID_PRIVATE_KEY` | from step 2 below |
   | `VAPID_SUBJECT` | `mailto:<your email>` (optional, defaults to your site URL) |
   | `DAILY_VERSE_SOURCE` | `ourmanna` (default), `netbible`, or `sample` |

4. Under **Settings → Networking**, click **Generate Domain**. That URL is your app.
5. Nothing to run by hand for data: on every start the `Procfile` runs
   `setup_initial_data`, which seeds the reading plans and this month's sample
   verses **only on an empty database**, so it's safe across redeploys.
   For an admin login, run `python manage.py createsuperuser` from Railway's
   service shell, or sign up through `/admin/` locally first.

## 2. Create push notification keys (one time)

Run this locally and copy the two lines into Railway's Variables:

```
.venv\Scripts\python.exe manage.py generate_vapid_keys
```

Keep `VAPID_PRIVATE_KEY` secret. If you change the keys, every phone has to turn
notifications on again.

## 3. Schedule the daily send

Nothing to set up. The `Procfile` starts `run_verse_scheduler` next to the web
server, and it runs `send_daily_verse` every 15 minutes. Each run notifies every
user whose chosen time has passed and who hasn't been notified yet today, in
their own time zone, so nobody gets two notifications in one day.

(If you'd rather use a separate Railway cron service, give it the start command
`python manage.py send_daily_verse`, the schedule `*/15 * * * *`, and the same
variables, then remove the scheduler from the `Procfile`.)

## 4. Install it on your iPhone

1. Open your Railway URL in **Safari** and log in.
2. Tap **Share ⬆️ → Add to Home Screen → Add**.
3. Open **Journal** from the home screen. Tap the 🔔 at the top, then
   **Turn on notifications → Allow**.
4. Choose your time (default 7:00 AM) and tap **Save**. Then tap **Send a test verse**.

On Android, Chrome shows an **Install app** prompt, or you can use ⋮ → *Add to Home
screen*. Notifications work the same way.

---

## Where the daily verses come from

`journal/verses.py` picks the verse for each day in this order:

1. **A saved `DailyVerse` row.** This can be the seeded sample month, an earlier fetch,
   or a verse you add by hand in **Admin → Daily verses**. Use the admin to override any
   day, for example a verse that fits a sermon series.
2. **An online verse-of-the-day feed**, fetched once a day by `send_daily_verse`:
   * [OurManna](https://beta.ourmanna.com/api/v1/get?format=json&order=daily) (`ourmanna`)
   * [Bible.org NET Bible VOTD](https://labs.bible.org/api/?passage=votd&type=json) (`netbible`)

   Only the feed's *reference* is used. The text is pulled from
   [bible-api.com](https://bible-api.com) in the public-domain **World English Bible**,
   so nothing copyrighted gets stored.
3. **The bundled 31-day sample** (`journal/data/daily_verses_sample.json`), by day of the
   month. It's a set of well-known verse-of-the-day picks (Lam 3:22-23, Prov 3:5-6,
   Isa 40:31, Jer 29:11 …) in WEB text. Edit that file to change the rotation.

Seeding a month fills every day of that month with the sample, so the online feed takes
over only for days that aren't seeded yet. To use the live feed from now on, skip seeding
the next month.
