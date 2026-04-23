from django.core.management.base import BaseCommand
from trapApp.models import Event

# Назви подій збігаються з JS-списком у outfit_picker.js
# Значення formality — лише з FORMALITY_CHOICES моделі
EVENTS = [
    ('День народження',           'smart_casual'),
    ('Ювілей',                    'cocktail'),
    ('Заручини',                  'cocktail'),
    ('Розпис',                    'semi_formal'),
    ('Весільний банкет (гість)',   'cocktail'),
    ('Коктейльна вечірка',        'cocktail'),
    ('Формальний вечір',          'after_five'),
    ('Корпоратив',                'business_casual'),
    ('Конференція',               'business_casual'),
    ('Нетворкінг',                'business_casual'),
    ('Презентація',               'business_casual'),
    ('Публічний виступ',          'business_formal'),
    ('Фотосесія',                 'smart_casual'),
    ('Випуск з університету',     'semi_formal'),
    ('Театр',                     'smart_casual'),
    ('Опера / філармонія',        'black_tie_creative'),
    ('Гала-вечір',                'black_tie'),
    ('Благодійний бал',           'black_tie'),
    ('Свято в родині',            'smart_casual'),
    ('Бранч / зустріч з друзями', 'smart_casual'),
]


class Command(BaseCommand):
    help = 'Seed events into DB (names match outfit_picker.js)'

    def handle(self, *args, **options):
        created = updated = 0
        for name, formality in EVENTS:
            obj, is_new = Event.objects.get_or_create(
                name=name,
                defaults={'formality': formality},
            )
            if is_new:
                created += 1
            elif obj.formality != formality:
                obj.formality = formality
                obj.save(update_fields=['formality'])
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Done: {created} created, {updated} updated ({len(EVENTS)} total events).'
            )
        )
