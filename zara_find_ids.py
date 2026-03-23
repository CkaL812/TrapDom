"""
zara_find_ids.py
----------------
Сканує діапазони category_id на Zara UA і знаходить валідні категорії.

Запуск:
    python zara_find_ids.py

Результат зберігається у zara_valid_ids.json і zara_valid_ids.txt
"""

import time
import json
import requests

BASE_URL = 'https://www.zara.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'uk-UA,uk;q=0.9',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://www.zara.com/ua/uk/',
}

# ─── Відомі робочі ID (з логів) ─────────────────────────────────────────────
KNOWN_WORKING = {
    2436585: 'MAN Футболки',
    2436584: 'MAN Шорти',
    2436949: 'MAN Сорочки',
    2436336: 'MAN Кросівки',
    2436385: 'MAN Сандалі/Тапки',
    2436386: 'MAN Шльопанці',
    2473840: 'MAN Штани',
    2436311: 'MAN Блейзери',
    2436384: 'MAN Офіційне взуття',
    2606109: 'MAN Пальта/Тренчі',
    2436388: 'MAN Зимові черевики',
    2436389: 'MAN Зимові чоботи',
    2436444: 'MAN Аксесуари',
    2436434: 'MAN Ремені',
    2436436: 'MAN Краватки',
    2420417: 'WOMAN Футболки',
    2419940: 'WOMAN Топи',
    2420896: 'WOMAN Сукні',
    2420454: 'WOMAN Спідниці',
    2419172: 'WOMAN Босоніжки',
    2419173: 'WOMAN Шльопанці/Тапки',
    2419174: 'WOMAN Сандалі',
    2420456: 'WOMAN Купальники/Пляж',
    2420369: 'WOMAN Сорочки/Блузи',
    2419185: 'WOMAN Джинси',
    2420795: 'WOMAN Штани',
    2420942: 'WOMAN Блейзери',
    2420945: 'WOMAN Сукні (демісезон)',
    2419075: 'WOMAN Кросівки',
    2419175: 'WOMAN Черевики',
    2419176: 'WOMAN Туфлі',
    2419032: 'WOMAN Тренчі/Пальта',
    2417772: 'WOMAN Куртки',
    2419160: 'WOMAN Чоботи',
    2418989: 'WOMAN Аксесуари',
    2418963: 'WOMAN Прикраси',
    2418966: 'WOMAN Ремені',
}

# ─── Діапазони для сканування ────────────────────────────────────────────────
# Генеруємо сусідні ID навколо відомих робочих, щоб знайти нові категорії
def build_scan_ranges():
    ranges = set()

    # Навколо кожного відомого ID ± 50 кроків з різним кроком
    for known_id in KNOWN_WORKING:
        for delta in range(-30, 31):
            candidate = known_id + delta
            if candidate > 0:
                ranges.add(candidate)

    # Додаткові діапазони де можуть бути чоловічі светри, худі, джинси, куртки
    # (між відомими чоловічими ID: 2436311–2436950)
    for i in range(2436290, 2436960, 1):
        ranges.add(i)

    # Жіночі (між 2417700–2421000)
    for i in range(2417700, 2421050, 1):
        ranges.add(i)

    # Окремий блок де знайдено 2606109 (пальта)
    for i in range(2606080, 2606140, 1):
        ranges.add(i)

    return sorted(ranges)


def check_category(category_id, session, delay=0.3):
    url = f'{BASE_URL}/ua/uk/category/{category_id}/products?ajax=true'
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
    except requests.exceptions.Timeout:
        print(f'  [{category_id}] ⏱ timeout, пропускаємо')
        time.sleep(2)
        return None
    except Exception as e:
        print(f'  [{category_id}] ❌ {e}')
        time.sleep(1)
        return None

    if r.status_code == 404:
        return None
    if r.status_code != 200:
        print(f'  [{category_id}] ⚠️  статус {r.status_code}')
        return None

    try:
        data = r.json()
    except Exception:
        return None

    products = []
    for group in data.get('productGroups', []):
        for el in group.get('elements', []):
            for item in el.get('commercialComponents', []):
                products.append(item)

    if not products:
        return None

    # Збираємо назви для розуміння що за категорія
    names = [
        (item.get('name') or item.get('description') or '').strip()
        for item in products[:5]
        if (item.get('name') or item.get('description') or '').strip()
    ]

    time.sleep(delay)
    return {
        'id': category_id,
        'count': len(products),
        'samples': names,
    }


def main():
    scan_ids = build_scan_ranges()

    # Прибираємо вже відомі
    known_ids = set(KNOWN_WORKING.keys())
    to_scan = [i for i in scan_ids if i not in known_ids]

    print(f'🔍 Починаємо сканування {len(to_scan)} кандидатів...')
    print(f'   (+ {len(known_ids)} вже відомих робочих ID)')
    print()

    found = []

    # Стартуємо з вже відомих
    for cat_id, label in KNOWN_WORKING.items():
        found.append({'id': cat_id, 'count': '?', 'samples': [label], 'known': True})

    session = requests.Session()

    for idx, cat_id in enumerate(to_scan, 1):
        result = check_category(cat_id, session)

        if result:
            result['known'] = False
            found.append(result)
            samples_str = ' | '.join(result['samples'][:3])
            print(f'✅ [{cat_id}]  {result["count"]} товарів  →  {samples_str}')
        else:
            # Тиха пропуска — не засмічуємо вивід
            pass

        # Прогрес кожні 100
        if idx % 100 == 0:
            new_found = [r for r in found if not r.get('known')]
            print(f'   ... {idx}/{len(to_scan)} перевірено, нових знайдено: {len(new_found)}')

    # ─── Зберігаємо результати ───────────────────────────────────────────────
    new_ids = [r for r in found if not r.get('known')]

    with open('zara_valid_ids.json', 'w', encoding='utf-8') as f:
        json.dump(found, f, ensure_ascii=False, indent=2)

    with open('zara_valid_ids.txt', 'w', encoding='utf-8') as f:
        f.write('=' * 60 + '\n')
        f.write('НОВІ ЗНАЙДЕНІ ID\n')
        f.write('=' * 60 + '\n\n')
        for r in new_ids:
            f.write(f"ID: {r['id']}   ({r['count']} товарів)\n")
            for s in r['samples']:
                f.write(f"    • {s}\n")
            f.write('\n')

        f.write('\n' + '=' * 60 + '\n')
        f.write('ВСІ ВІДОМІ РОБОЧІ ID\n')
        f.write('=' * 60 + '\n\n')
        for r in found:
            if r.get('known'):
                label = r['samples'][0] if r['samples'] else ''
                f.write(f"ID: {r['id']}   {label}\n")

    print()
    print(f'✅ Готово! Нових ID знайдено: {len(new_ids)}')
    print(f'📄 Результати збережено у:')
    print(f'   → zara_valid_ids.json  (повні дані)')
    print(f'   → zara_valid_ids.txt   (читабельний звіт)')


if __name__ == '__main__':
    main()