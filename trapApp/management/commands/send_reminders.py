from django.core.management.base import BaseCommand
from trapApp.tasks import check_and_send_reminders


class Command(BaseCommand):
    help = 'Перевіряє нотатки і надсилає email-нагадування (те саме що scheduler робить кожні 15 хв)'

    def handle(self, *args, **options):
        self.stdout.write('Перевірка нотаток...')
        check_and_send_reminders()
        self.stdout.write(self.style.SUCCESS('Готово. Перевір логи і пошту.'))
