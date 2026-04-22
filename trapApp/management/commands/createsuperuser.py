import getpass

from django.core.management.base import BaseCommand
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from trapApp.models import CustomUser


class Command(BaseCommand):
    help = 'Створює суперкористувача (CustomUser з is_staff=True, is_superuser=True)'

    def add_arguments(self, parser):
        parser.add_argument('--email',    dest='email',    default=None)
        parser.add_argument('--password', dest='password', default=None)
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_true', dest='no_input',
        )

    def handle(self, *args, **options):
        email    = options.get('email')
        no_input = options.get('no_input')
        password = options.get('password')

        if not no_input:
            self.stdout.write(self.style.MIGRATE_HEADING('\nСтворення суперкористувача\n'))

            while True:
                if not email:
                    email = input('Email: ').strip()
                try:
                    validate_email(email)
                except ValidationError:
                    self.stderr.write('  Некоректний email.')
                    email = None
                    continue
                if CustomUser.objects.filter(email=email.lower()).exists():
                    self.stderr.write(f'  Користувач "{email}" вже існує.')
                    email = None
                    continue
                break

            while True:
                password  = getpass.getpass('Пароль: ')
                password2 = getpass.getpass('Підтвердіть пароль: ')
                if password != password2:
                    self.stderr.write('  Паролі не збігаються.')
                    continue
                if len(password) < 8:
                    self.stderr.write('  Пароль занадто короткий (мінімум 8 символів).')
                    continue
                break
        else:
            if not email or not password:
                self.stderr.write(self.style.ERROR('Потрібно вказати --email та --password'))
                return
            try:
                validate_email(email)
            except ValidationError:
                self.stderr.write(self.style.ERROR(f'Некоректний email: {email}'))
                return
            if CustomUser.objects.filter(email=email.lower()).exists():
                self.stderr.write(self.style.ERROR(f'Користувач "{email}" вже існує.'))
                return

        user = CustomUser.objects.create_superuser(
            username=email.lower(),
            email=email.lower(),
            password=password,
            first_name='Admin',
            last_name='',
        )
        self.stdout.write(self.style.SUCCESS(f'\nСуперкористувача "{user.email}" успішно створено!'))
