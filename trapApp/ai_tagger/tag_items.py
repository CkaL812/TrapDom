import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trapdom.settings')

import django
django.setup()

import requests
import json
from trapApp.models import ClothingItem


OPENROUTER_API_KEY = os.environ['OPENROUTER_API_KEY']
MODEL = 'google/gemini-2.0-flash-001'

PROMPT = """Analyze this clothing item image and return JSON with:
- "color": dominant color in English (e.g. "Navy Blue", "Black")
- "material": likely fabric (e.g. "Wool", "Cotton", "Silk", "Denim")
- "pattern": one of: solid, striped, checked, print, floral, abstract
- "formality": one of: casual, smart_casual, business, cocktail, formal, black_tie
Respond ONLY with valid JSON, no markdown, no explanation."""


def tag_item(item: ClothingItem):
    if not item.image_url:
        print(f'  [skip] {item.name} — немає image_url')
        return

    resp = None
    for attempt in range(1, 4):  # 3 спроби
        try:
            resp = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://trapdom.local',
                    'X-Title': 'TrapDom',
                },
                json={
                    'model': MODEL,
                    'messages': [{
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': PROMPT},
                            {'type': 'image_url', 'image_url': {'url': item.image_url}}
                        ]
                    }],
                    'max_tokens': 200,
                },
                timeout=30,
            )
            resp.raise_for_status()
            break  # успіх

        except requests.HTTPError as e:
            print(f'  [✗] HTTP error для {item.name}: {e} | {resp.text[:300]}')
            return
        except requests.RequestException as e:
            print(f'  [!] Спроба {attempt}/3 для {item.name}: {e}')
            if attempt == 3:
                print(f'  [✗] Пропускаємо {item.name}')
                return
            time.sleep(3 * attempt)  # 3с, 6с між спробами
    else:
        return

    try:
        raw = resp.json()['choices'][0]['message']['content']

        clean = (
            raw.strip()
            .removeprefix('```json')
            .removeprefix('```')
            .removesuffix('```')
            .strip()
        )

        result = json.loads(clean)

        item.color     = result.get('color',     item.color)
        item.material  = result.get('material',  item.material)
        item.pattern   = result.get('pattern',   item.pattern)
        item.formality = result.get('formality', item.formality)
        item.save(update_fields=['color', 'material', 'pattern', 'formality'])

        print(f'  [✓] {item.name} → {result}')

    except (KeyError, json.JSONDecodeError) as e:
        print(f'  [✗] Помилка парсингу для {item.name}: {e} | {resp.text[:200]}')


def run_tagging(limit: int = 500):
    qs = ClothingItem.objects.filter(material='')
    total = min(qs.count(), limit)
    items = list(qs[:limit])

    print(f'[→] Тегуємо {total} речей...')

    for i, item in enumerate(items, 1):
        print(f'[{i}/{total}] {item.name}')
        tag_item(item)

    print(f'\n[✅] Готово!')


if __name__ == '__main__':
    run_tagging()