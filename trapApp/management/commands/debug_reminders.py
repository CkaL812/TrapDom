from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta, time as dt_time


class Command(BaseCommand):
    help = 'Діагностика системи нагадувань'

    def handle(self, *args, **options):
        from trapApp.models import Note

        self.stdout.write('\n=== НАЛАШТУВАННЯ EMAIL ===')
        self.stdout.write(f'  HOST:     {settings.EMAIL_HOST}')
        self.stdout.write(f'  PORT:     {settings.EMAIL_PORT}')
        self.stdout.write(f'  TLS:      {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'  USER:     {settings.EMAIL_HOST_USER}')
        pwd = settings.EMAIL_HOST_PASSWORD
        self.stdout.write(f'  PASSWORD: {"*" * len(pwd) if pwd else "(ПУСТО!)"}')
        self.stdout.write(f'  FROM:     {settings.DEFAULT_FROM_EMAIL}')

        self.stdout.write('\n=== НОТАТКИ В БД ===')
        all_notes = Note.objects.all().select_related('user')
        if not all_notes.exists():
            self.stdout.write(self.style.WARNING('  (нотаток немає взагалі!)'))
        else:
            now = timezone.now()
            for n in all_notes:
                event_end_naive = datetime.combine(
                    n.event_date, n.event_time or dt_time(23, 59)
                )
                event_end = timezone.make_aware(event_end_naive)
                expired = now > event_end + timedelta(hours=6)

                self.stdout.write(
                    f'  #{n.pk} | {n.event_name} | {n.event_date} {n.event_time or ""} '
                    f'| mode={n.mode} | sent={n.notification_sent} '
                    f'| locked={n.outfit_locked} | user={n.user.email}'
                    f'{" | МИНУЛА" if expired else ""}'
                )

        auto_notes = Note.objects.filter(
            notification_sent=False, mode='auto', outfit_locked=False
        )
        self.stdout.write(f'\n  Підходять для відправки (auto, unsent, unlocked): {auto_notes.count()}')

        self.stdout.write('\n=== ТЕСТ SMTP ===')
        try:
            send_mail(
                subject='TrapDom — тест SMTP',
                message='Це тестовий лист від TrapDom. Якщо ти його бачиш — SMTP працює.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'  Тестовий лист надіслано на {settings.EMAIL_HOST_USER}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ПОМИЛКА SMTP: {e}'))
