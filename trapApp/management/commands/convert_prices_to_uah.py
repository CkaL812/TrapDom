import requests
from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand
from trapApp.models import ClothingItem


def fetch_nbu_rates():
    """Повертає dict {код_валюти: курс_до_гривні} з API НБУ."""
    url = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return {row['cc']: Decimal(str(row['rate'])) for row in resp.json()}


class Command(BaseCommand):
    help = 'Конвертує всі ціни товарів у гривні за курсом НБУ'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показати що буде змінено без запису в БД',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('Отримую курси НБУ...')
        try:
            rates = fetch_nbu_rates()
        except Exception as e:
            self.stderr.write(f'Помилка отримання курсів: {e}')
            return

        for code, rate in rates.items():
            if code in ('USD', 'GBP', 'EUR'):
                self.stdout.write(f'  {code} -> {rate} UAH')

        items = ClothingItem.objects.exclude(currency='UAH')
        total = items.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Всі ціни вже у гривнях.'))
            return

        self.stdout.write(f'\nЗнайдено {total} товарів не в UAH:')

        converted = 0
        skipped = 0

        for item in items.iterator():
            currency = item.currency.upper()
            rate = rates.get(currency)

            if rate is None:
                self.stdout.write(
                    self.style.WARNING(f'  #{item.pk} {item.name[:40]} — невідома валюта {currency}, пропускаю')
                )
                skipped += 1
                continue

            old_price      = item.price
            old_sale_price = item.sale_price

            new_price = None
            new_sale  = None

            if item.price is not None:
                new_price = (item.price * rate).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            if item.sale_price is not None:
                new_sale = (item.sale_price * rate).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

            safe_name = item.name[:35].encode('cp1251', errors='replace').decode('cp1251')
            self.stdout.write(
                f'  #{item.pk} [{currency}] {safe_name:35s}  '
                f'{old_price} -> {new_price} UAH'
                + (f'  (sale {old_sale_price} -> {new_sale})' if new_sale else '')
            )

            if not dry_run:
                item.price      = new_price
                item.sale_price = new_sale
                item.currency   = 'UAH'
                item.save(update_fields=['price', 'sale_price', 'currency'])

            converted += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\n[DRY RUN] Було б конвертовано: {converted}, пропущено: {skipped}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nГотово. Конвертовано: {converted}, пропущено: {skipped}'
            ))
