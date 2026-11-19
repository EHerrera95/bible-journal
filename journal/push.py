"""Web Push helpers (works for iPhone home-screen apps on iOS 16.4+, Android and desktop)."""
import json
import logging

from django.conf import settings

log = logging.getLogger(__name__)


def push_configured() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def send_push(subscription, title: str, body: str, url: str = "/verse/", tag: str = "daily-verse") -> bool:
    """
    Send one notification. Returns True on success. Subscriptions the push
    service reports as gone (404/410) are deleted.
    """
    from pywebpush import WebPushException, webpush

    payload = json.dumps({"title": title, "body": body, "url": url, "tag": tag})
    try:
        webpush(
            subscription_info=subscription.as_webpush_info(),
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
            ttl=60 * 60 * 12,
        )
        return True
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):
            log.info("Removing expired push subscription %s", subscription.pk)
            subscription.delete()
        else:
            log.warning("Push failed (%s): %s", status, exc)
        return False


def send_verse_to_user(user, verse: dict) -> int:
    """Send a verse to every device the user has subscribed. Returns # delivered."""
    body = verse["text"]
    if len(body) > 180:
        body = body[:177].rsplit(" ", 1)[0] + "…"
    title = f"Verse of the Day · {verse['reference']}"
    return sum(send_push(sub, title, body) for sub in list(user.push_subscriptions.all()))
