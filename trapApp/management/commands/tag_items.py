"""
Django management команда для ручного запуску тагера.

Приклади:
    python manage.py tag_items                       # тагує все необроблене
    python manage.py tag_items --all                 # перетегує все (навіть готове)
    python manage.py tag_items --brand Zara          # тільки один бренд
    python manage.py tag_items --limit 10            # обробити тільки 10 товарів
    python manage.py tag_items --retry-low-confidence # переобробити товари з низьким confidence
"""

import logging
from django.core.management.base import BaseCommand
from trapApp.models import ClothingItem


class Command(BaseCommand):
    help = 'Тагує товари через CLIP + правила'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true',
                            help='Перетегувати всі товари, навіть ті, що вже мають tagged_at')
        parser.add_argument('--brand', type=str, default=None,
                            help='Тільки товари одного бренду (напр. --brand Zara)')
        parser.add_argument('--limit', type=int, default=None,
                            help='Обробити максимум N товарів (для тестів)')
        parser.add_argument('--retry-low-confidence', action='store_true',
                            help='Переобробити товари, де CLIP був невпевнений')
        parser.add_argument('--min-conf', type=float, default=0.22,
                            help='Мінімальний поріг впевненості (default: 0.22)')

    def handle(self, *args, **opts):
        # Налаштування логування, щоб бачити прогрес у консолі
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S',
        )

        self.stdout.write(self.style.SUCCESS('═══ TAGGER STARTED ═══'))

        # Будуємо queryset
        qs = ClothingItem.objects.all()

        if opts['brand']:
            qs = qs.filter(brand__name__iexact=opts['brand'])
            self.stdout.write(f'  • Бренд: {opts["brand"]}')

        if opts['retry_low_confidence']:
            # Товари, де subcategory confidence < 0.3
            # (JSON-фільтр для MySQL)
            qs = qs.extra(
                where=["JSON_EXTRACT(tags, '$.confidence.subcategory') < 0.3"]
            )
            self.stdout.write('  • Тільки товари з низьким confidence')

        skip_already = not opts['all']
        if skip_already:
            qs = qs.filter(tagged_at__isnull=True)

        if opts['limit']:
            qs = qs[:opts['limit']]
            self.stdout.write(f'  • Ліміт: {opts["limit"]}')

        self.stdout.write(f'  • Skip already tagged: {skip_already}')
        self.stdout.write(f'  • Min confidence: {opts["min_conf"]}')
        self.stdout.write(f'  • Товарів у черзі: {qs.count()}\n')

        # Запускаємо тагер
        from trapApp.tagger import get_tagger
        tagger = get_tagger()
        tagger.MIN_CONFIDENCE = opts['min_conf']

        stats = tagger.tag_items(qs, skip_already_tagged=False)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('═══ TAGGER FINISHED ═══'))
        self.stdout.write(f'  Всього:     {stats["total"]}')
        self.stdout.write(f'  Затеговано: {stats["tagged"]}')
        self.stdout.write(f'  Пропущено:  {stats["skipped"]}')
        self.stdout.write(f'  Помилок:    {stats["errors"]}')