import os
import django

# Якщо запускаєш як звичайний скрипт (не через manage.py shell):
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
# django.setup()

from django.db.models import Count
from trapApp.models import ClothingItem  # <- заміни your_app на назву свого додатку

print("=" * 60)
print("РОЗПОДІЛ ПО КАТЕГОРІЯХ + СТАТЬ")
print("=" * 60)

items = (
    ClothingItem.objects
    .values('category', 'gender')
    .annotate(count=Count('id'))
    .order_by('category', 'gender')
)

current_category = None
for row in items:
    cat_display = dict(ClothingItem.CATEGORY_CHOICES).get(row['category'], row['category'])
    gender_display = {'M': 'Чоловіче', 'F': 'Жіноче', 'U': 'Унісекс'}.get(row['gender'], row['gender'])

    if row['category'] != current_category:
        print(f"\n📁 {cat_display} ({row['category']})")
        current_category = row['category']

    print(f"   {gender_display}: {row['count']} шт.")


print("\n" + "=" * 60)
print("РОЗПОДІЛ ПО FORMALITY")
print("=" * 60)

formality = (
    ClothingItem.objects
    .values('formality', 'category')
    .annotate(count=Count('id'))
    .order_by('formality', 'category')
)

current_formality = None
for row in formality:
    cat_display = dict(ClothingItem.CATEGORY_CHOICES).get(row['category'], row['category'])
    form_display = dict(ClothingItem.FORMALITY_CHOICES).get(row['formality'], row['formality'])

    if row['formality'] != current_formality:
        print(f"\n🎩 {form_display}")
        current_formality = row['formality']

    print(f"   {cat_display}: {row['count']} шт.")


print("\n" + "=" * 60)
print("РОЗПОДІЛ ПО СЕЗОНАХ")
print("=" * 60)

from trapApp.models import Season  # <- теж заміни

seasons = Season.objects.annotate(count=Count('items')).order_by('name')
for s in seasons:
    print(f"  {s}: {s.count} шт.")


print("\n" + "=" * 60)
print("ТОП-20 НАЗВ ТОВАРІВ (для розуміння номенклатури)")
print("=" * 60)

sample = ClothingItem.objects.values_list('name', 'category', 'gender').order_by('category')[:50]
for name, cat, gender in sample:
    cat_display = dict(ClothingItem.CATEGORY_CHOICES).get(cat, cat)
    gender_display = {'M': 'Чол', 'F': 'Жін', 'U': 'Уні'}.get(gender, gender)
    print(f"  [{cat_display} / {gender_display}] {name}")


print("\n" + "=" * 60)
print("ЗАГАЛЬНА СТАТИСТИКА")
print("=" * 60)

total = ClothingItem.objects.count()
male = ClothingItem.objects.filter(gender='M').count()
female = ClothingItem.objects.filter(gender='F').count()
unisex = ClothingItem.objects.filter(gender='U').count()

print(f"  Всього товарів: {total}")
print(f"  Чоловічих: {male}")
print(f"  Жіночих: {female}")
print(f"  Унісекс: {unisex}")