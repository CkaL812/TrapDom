"""
Кастомна команда createsuperuser.
Замість стандартного CustomUser записує адміна в окрему таблицю Admin
(тільки email + пароль).
"""
import getpass

from django.core.management.base import BaseCommand
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from trapApp.models import Admin


class Command(BaseCommand):
    help = 'Створює адміністратора у таблиці Admin (email + пароль)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            dest='email',
            default=None,
            help='Email адміністратора',
        )
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_true',
            dest='no_input',
            help='Не запитувати підтвердження (потрібний --email та --password)',
        )
        parser.add_argument(
            '--password',
            dest='password',
            default=None,
            help='Пароль (тільки для --noinput)',
        )

    def handle(self, *args, **options):
        email    = options.get('email')
        no_input = options.get('no_input')
        password = options.get('password')

        # ── Інтерактивний режим ──────────────────────────────────────────────
        if not no_input:
            self.stdout.write(self.style.MIGRATE_HEADING(
                '\nСтворення адміністратора (окрема таблиця Admin)\n'
            ))

            # Email
            while True:
                if not email:
                    email = input('Email: ').strip()
                try:
                    validate_email(email)
                except ValidationError:
                    self.stderr.write('  Некоректний email. Спробуйте знову.')
                    email = None
                    continue
                if Admin.objects.filter(email=email.lower()).exists():
                    self.stderr.write(
                        f'  Адмін з email "{email}" вже існує. Спробуйте інший.'
                    )
                    email = None
                    continue
                break

            # Пароль
            while True:
                password  = getpass.getpass('Пароль: ')
                password2 = getpass.getpass('Підтвердіть пароль: ')
                if password != password2:
                    self.stderr.write('  Паролі не збігаються. Спробуйте знову.')
                    continue
                if len(password) < 8:
                    self.stderr.write('  Пароль занадто короткий (мінімум 8 символів).')
                    continue
                break

        # ── Нон-інтерактивний режим ──────────────────────────────────────────
        else:
            if not email or not password:
                self.stderr.write(
                    self.style.ERROR(
                        'У режимі --noinput потрібно вказати --email та --password'
                    )
                )
                return

            try:
                validate_email(email)
            except ValidationError:
                self.stderr.write(self.style.ERROR(f'Некоректний email: {email}'))
                return

            if Admin.objects.filter(email=email.lower()).exists():
                self.stderr.write(
                    self.style.ERROR(f'Адмін з email "{email}" вже існує.')
                )
                return

        # ── Збереження ───────────────────────────────────────────────────────
        Admin.objects.create_admin(email=email, password=password)
        self.stdout.write(
            self.style.SUCCESS(f'\nАдміністратора "{email}" успішно створено!')
        )
