# wardrobe/management/commands/seed_events.py
from django.core.management.base import BaseCommand
from trapApp.models import Event
EVENTS = [
    ('День народження (неформальний)', 'casual'),
    ('День народження (вечірка)',      'cocktail'),
    ('Зустріч з друзями',              'casual'),
    ('Бранч',                          'smart_casual'),
    ('Побачення',                      'smart_casual'),
    ('Корпоратив',                     'smart_casual'),
    ('Нетворкінг / Конференція',       'business'),
    ('Презентація',                    'business'),
    ('Публічний виступ',               'business'),
    ('Зустріч з родиною',              'smart_casual'),
    ('Випускний',                      'formal'),
    ('Заручини',                       'cocktail'),
    ('Весільний банкет (гість)',        'formal'),
    ('Розпис',                         'formal'),
    ('Коктейльна вечірка',             'cocktail'),
    ('Похід у театр / Оперу',          'formal'),
    ('Виставка / Галерея',             'smart_casual'),
    ('Гала-вечір',                     'black_tie'),
    ('Благодійний бал',                'black_tie'),
    ('Фотосесія (творча)',             'casual'),
]

class Command(BaseCommand):
    help = 'Seed events into DB'

    def handle(self, *args, **options):
        for name, formality in EVENTS:
            Event.objects.get_or_create(name=name, defaults={'formality': formality})
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(EVENTS)} events.'))
