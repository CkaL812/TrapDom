import logging
from datetime import datetime, timedelta, time as dt_time
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)

CATEGORY_ORDER = ['tops', 'layering', 'bottoms', 'onepiece', 'outerwear', 'footwear', 'accessory']


def _compute_notify_at(note):
    now = timezone.now()
    if note.event_time:
        event_naive = datetime.combine(note.event_date, note.event_time)
        event_aware = timezone.make_aware(event_naive)
        notify_at   = event_aware - timedelta(hours=5)
        if notify_at > now:
            return notify_at
        return now
    prev_day = note.event_date - timedelta(days=1)
    return timezone.make_aware(datetime.combine(prev_day, dt_time(20, 0)))


def check_and_send_reminders():
    from .models import Note
    from .views import _generate_note_outfit
    now = timezone.now()
    notes = (
        Note.objects
        .filter(notification_sent=False, mode='auto')
        .select_related('user')
    )
    for note in notes:
        notify_at = _compute_notify_at(note)
        if now < notify_at:
            continue
        event_end_naive = datetime.combine(note.event_date, note.event_time or dt_time(23, 59))
        event_end = timezone.make_aware(event_end_naive)
        if now > event_end + timedelta(hours=6):
            note.notification_sent = True
            note.save(update_fields=['notification_sent'])
            continue
        if not note.outfit_items.exists():
            _generate_note_outfit(note)
        _send_reminder_email(note)
        note.notification_sent = True
        note.save(update_fields=['notification_sent'])


def _send_reminder_email(note):
    user = note.user
    if not user.email:
        return

    site_url   = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
    note_url   = f'{site_url}/notes/{note.pk}/'
    event_date = note.event_date.strftime('%d.%m.%Y')
    event_time = note.event_time.strftime('%H:%M') if note.event_time else ''
    subject    = f'TrapDom — нагадуємо про «{note.get_event_name_display()}»'

    text_body = (
        f'Привіт, {user.first_name or user.email}!\n\n'
        f'Нагадуємо — незабаром твій захід «{note.get_event_name_display()}» '
        f'({event_date}{" / " + event_time if event_time else ""}).\n\n'
        f'Переглянути образ: {note_url}\n\n'
        f'— TrapDom'
    )

    html_body = render_to_string('trapApp/emails/outfit_ready.html', {
        'user':       user,
        'note':       note,
        'event_name': note.get_event_name_display(),
        'event_date': event_date,
        'event_time': event_time,
        'note_url':   note_url,
        'site_url':   site_url,
    })

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
        logger.info(f'[REMINDER] Надіслано note #{note.pk} → {user.email}')
    except Exception as exc:
        logger.warning(f'[REMINDER] Помилка note #{note.pk}: {exc}')
