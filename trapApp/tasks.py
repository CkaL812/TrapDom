import logging
from datetime import datetime, timedelta, time as dt_time
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)

CATEGORY_ORDER = ['tops', 'layering', 'bottoms', 'onepiece', 'outerwear', 'footwear', 'accessory']


def _compute_notify_at(note):
    """
    Повертає aware-datetime коли треба згенерувати образ і надіслати лист.

    Правило:
      - Є час події і (час - 5 год) >= 08:00 → того ж дня о (час - 5 год)
      - Інакше → напередодні о 20:00
    """
    if note.event_time:
        event_naive = datetime.combine(note.event_date, note.event_time)
        candidate   = event_naive - timedelta(hours=5)
        cutoff      = datetime.combine(note.event_date, dt_time(8, 0))
        if candidate >= cutoff:
            return timezone.make_aware(candidate)

    prev_day = note.event_date - timedelta(days=1)
    return timezone.make_aware(datetime.combine(prev_day, dt_time(20, 0)))


def check_and_send_reminders():
    """Запускається кожні 15 хвилин. Знаходить нотатки, яким час надіслати нагадування."""
    from .models import Note
    from .views import _generate_note_outfit

    now = timezone.now()

    notes = (
        Note.objects
        .filter(notification_sent=False, mode='auto', outfit_locked=False)
        .select_related('user')
    )

    for note in notes:
        notify_at = _compute_notify_at(note)
        if now < notify_at:
            continue

        # Не надсилати, якщо подія вже давно минула (> 6 год після початку)
        event_end_naive = datetime.combine(note.event_date, note.event_time or dt_time(23, 59))
        event_end = timezone.make_aware(event_end_naive)
        if now > event_end + timedelta(hours=6):
            note.notification_sent = True
            note.save(update_fields=['notification_sent'])
            continue

        # Генеруємо образ тільки якщо ще не підібрано
        if not note.outfit_items.exists():
            _generate_note_outfit(note)

        _send_reminder_email(note)

        note.notification_sent = True
        note.save(update_fields=['notification_sent'])


def _send_reminder_email(note):
    user = note.user
    if not user.email:
        return

    items = sorted(
        note.outfit_items.select_related('brand').all(),
        key=lambda x: CATEGORY_ORDER.index(x.category) if x.category in CATEGORY_ORDER else 99,
    )
    items_text = '\n'.join(f'• {item.brand.name} — {item.name}' for item in items) or '(образ ще не зібрано)'
    time_str   = f' о {note.event_time.strftime("%H:%M")}' if note.event_time else ''

    subject = f'TrapDom: образ для «{note.get_event_name_display()}» готовий'
    body = (
        f'Привіт, {user.first_name}!\n\n'
        f'Ваш образ для «{note.get_event_name_display()}»{time_str} готовий:\n\n'
        f'{items_text}\n\n'
        f'Переглянути: http://127.0.0.1:8000/notes/{note.pk}/\n\n'
        f'— TrapDom'
    )

    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        logger.info(f'[REMINDER] Надіслано note #{note.pk} → {user.email}')
    except Exception as exc:
        logger.warning(f'[REMINDER] Помилка note #{note.pk}: {exc}')
