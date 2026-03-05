import time
import requests
from trapApp.scrapers.base import BaseScraper


class ZaraScraper(BaseScraper):

    brand_name = 'Zara'
    base_url   = 'https://www.zara.com'

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'uk-UA,uk;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.zara.com/ua/uk/',
    }

    # (category_id, wardrobe_category, formality, gender, label)
    CATEGORY_MAP = [

        # ── ЧОЛОВІКИ ────────────────────────────────────────────────────
        (2436949, 'tops',      'smart_casual', 'M', 'MAN Сорочки'),
        (2436585, 'tops',      'casual',       'M', 'MAN Футболки'),
        (2473840, 'bottoms',   'smart_casual', 'M', 'MAN Штани'),
        (2436584, 'bottoms',   'casual',       'M', 'MAN Шорти'),
        (2436311, 'layering',  'business',     'M', 'MAN Блейзери'),       # ← виправлено
        (2606109, 'outerwear', 'smart_casual', 'M', 'MAN Пальта/Тренчі'), # ← виправлено
        (2436336, 'footwear',  'casual',       'M', 'MAN Кросівки'),
        (2436384, 'footwear',  'formal',       'M', 'MAN Офіційне взуття'),
        (2436444, 'accessory', 'casual',       'M', 'MAN Аксесуари'),
        (2436434, 'accessory', 'casual',       'M', 'MAN Ремені'),
        (2436436, 'accessory', 'formal',       'M', 'MAN Краватки'),

        # ── ЖІНКИ ───────────────────────────────────────────────────────
        (2420369, 'tops',      'smart_casual', 'F', 'WOMAN Сорочки/Блузи'),
        (2420417, 'tops',      'casual',       'F', 'WOMAN Футболки'),
        (2419940, 'tops',      'casual',       'F', 'WOMAN Топи'),
        (2420896, 'onepiece',  'cocktail',     'F', 'WOMAN Сукні'),
        (2419185, 'bottoms',   'casual',       'F', 'WOMAN Джинси'),
        (2420795, 'bottoms',   'smart_casual', 'F', 'WOMAN Штани'),
        (2420454, 'bottoms',   'smart_casual', 'F', 'WOMAN Спідниці'),
        (2420942, 'layering',  'business',     'F', 'WOMAN Блейзери'),
        (2419032, 'outerwear', 'smart_casual', 'F', 'WOMAN Тренчі/Пальта'),
        (2417772, 'outerwear', 'casual',       'F', 'WOMAN Куртки'),
        (2419160, 'footwear',  'smart_casual', 'F', 'WOMAN Взуття'),
        (2419075, 'footwear',  'casual',       'F', 'WOMAN Кросівки'),
        (2419172, 'footwear',  'casual',       'F', 'WOMAN Босоніжки'),
        (2418989, 'accessory', 'casual',       'F', 'WOMAN Аксесуари'),
        (2418963, 'accessory', 'casual',       'F', 'WOMAN Прикраси'),
        (2418966, 'accessory', 'casual',       'F', 'WOMAN Ремені'),
    ]

    LIMIT_PER_CATEGORY = 4

    def run(self):
        total_saved = 0
        for category_id, category, formality, gender, label in self.CATEGORY_MAP:
            print(f'\n[Zara] ── {label} ──')
            saved = self._scrape_category(category_id, category, formality, gender)
            total_saved += saved
        print(f'\n[Zara] ✅ Всього збережено: {total_saved} товарів')

    def _scrape_category(self, category_id, category, formality, gender):
        url = f'{self.base_url}/ua/uk/category/{category_id}/products?ajax=true'
        print(f'[Zara] → {url}')

        try:
            r = requests.get(url, headers=self.HEADERS, timeout=20)
        except Exception as e:
            print(f'[Zara] Помилка: {e}')
            return 0

        if r.status_code != 200:
            print(f'[Zara] Статус {r.status_code}: {r.text[:300]}')
            return 0

        try:
            data = r.json()
        except Exception:
            print(f'[Zara] Не JSON: {r.text[:300]}')
            return 0

        products = []
        for group in data.get('productGroups', []):
            for el in group.get('elements', []):
                for item in el.get('commercialComponents', []):
                    products.append(item)

        print(f'[Zara] Знайдено: {len(products)}, беремо: {self.LIMIT_PER_CATEGORY}')

        if not products:
            print(f'[Zara] Ключі відповіді: {list(data.keys())}')
            return 0

        products = products[:self.LIMIT_PER_CATEGORY]

        saved = 0
        for item in products:
            name = item.get('name', '') or item.get('description', '')
            if not name or len(name) < 3:
                continue

            pid  = item.get('id', '')
            seo  = item.get('seo', {})
            slug = seo.get('keyword', '') if isinstance(seo, dict) else ''
            source_url = (
                f'{self.base_url}/ua/uk/{slug}-p{pid}.html' if slug
                else f'{self.base_url}/ua/uk/p{pid}.html'
            )
            source_url = source_url[:500]

            price = None
            for price_key in ['price', 'maxPrice', 'minPrice', 'originalPrice']:
                v = item.get(price_key)
                if v:
                    price = v / 100 if isinstance(v, int) and v > 10000 else v
                    break

            image_url = ''
            try:
                colors = item.get('detail', {}).get('colors', [])
                if colors:
                    xmedia_list = colors[0].get('xmedia', [])
                    if xmedia_list:
                        image_url = xmedia_list[0].get('extraInfo', {}).get('deliveryUrl', '')
            except Exception:
                pass
            image_url = image_url[:500]

            color = ''
            try:
                colors = item.get('detail', {}).get('colors', [])
                if colors:
                    color = colors[0].get('name', '')[:100]
            except Exception:
                pass

            self.save_item({
                'name':       name[:255],
                'source_url': source_url,
                'category':   category,
                'formality':  formality,
                'price':      price,
                'currency':   'UAH',
                'image_url':  image_url,
                'color':      color,
                'material':   '',
                'pattern':    'solid',
                'gender':     gender,
            }, [])
            saved += 1

        print(f'[Zara] categoryId={category_id}: {saved} збережено')
        time.sleep(1)
        return saved