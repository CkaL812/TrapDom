import time
import requests
from trapApp.scrapers.base import BaseScraper


class ZaraScraper(BaseScraper):

    brand_name = 'Zara'
    base_url   = 'https://www.zara.com'

    # (category_id, wardrobe_category, formality, gender)
    # categoryId береться з DevTools: Network → /category/{ID}/products?ajax=true
    CATEGORY_MAP = [
        (2431994,  'tops',      'smart_casual', 'M'),  # choloviky-sorochky ✓
        (None,     'outerwear', 'smart_casual', 'M'),  # choloviky-verkhnii-odiah
        (None,     'tops',      'smart_casual', 'F'),  # zhinky-sorochky
        (None,     'tops',      'casual',       'F'),  # zhinky-futbolky
        (None,     'onepiece',  'cocktail',     'F'),  # zhinky-sukni
        (None,     'bottoms',   'smart_casual', 'F'),  # zhinky-shtany
        (None,     'bottoms',   'casual',       'F'),  # zhinky-dzhynsy
        (None,     'outerwear', 'smart_casual', 'F'),  # zhinky-verkhnii-odiah
        (None,     'tops',      'casual',       'F'),  # zhinky-topy
    ]

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'uk-UA,uk;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.zara.com/ua/uk/',
    }

    def run(self):
        for category_id, category, formality, gender in self.CATEGORY_MAP:
            if category_id is None:
                print(f'[Zara] Пропускаємо {category}/{gender} — немає categoryId')
                continue
            self._scrape_category(category_id, category, formality, gender)

    def _scrape_category(self, category_id, category, formality, gender):
        url = f'{self.base_url}/ua/uk/category/{category_id}/products?ajax=true'
        print(f'[Zara] → {url}')

        try:
            r = requests.get(url, headers=self.HEADERS, timeout=20)
        except Exception as e:
            print(f'[Zara] Помилка: {e}')
            return

        if r.status_code != 200:
            print(f'[Zara] Статус {r.status_code}: {r.text[:300]}')
            return

        try:
            data = r.json()
        except Exception:
            print(f'[Zara] Не JSON: {r.text[:300]}')
            return

        products = []
        for group in data.get('productGroups', []):
            for el in group.get('elements', []):
                for item in el.get('commercialComponents', []):
                    products.append(item)

        print(f'[Zara] Знайдено товарів: {len(products)}')

        if not products:
            print(f'[Zara] Ключі відповіді: {list(data.keys())}')
            return

        saved = 0
        for item in products:
            name = item.get('name', '') or item.get('description', '')
            if not name or len(name) < 3:
                continue

            # URL товару — обрізаємо до 500 символів (ліміт VARCHAR)
            pid = item.get('id', '')
            seo = item.get('seo', {})
            slug = seo.get('keyword', '') if isinstance(seo, dict) else ''
            if slug:
                source_url = f'{self.base_url}/ua/uk/{slug}-p{pid}.html'
            else:
                source_url = f'{self.base_url}/ua/uk/p{pid}.html'
            source_url = source_url[:500]  # фікс Data too long

            # Ціна
            price = None
            for price_key in ['price', 'maxPrice', 'minPrice', 'originalPrice']:
                v = item.get(price_key)
                if v:
                    price = v / 100 if isinstance(v, int) and v > 10000 else v
                    break

            # Зображення
            # Зображення
# Зображення
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
            self.save_item({
                'name': name[:255],
                'source_url': source_url,
                'category': category,
                'formality': formality,
                'price': price,
                'currency': 'UAH',
                'image_url': image_url,
                'color': '',
                'material': '',
                'pattern': 'solid',
                'gender': gender,
            }, [])
            saved += 1

        print(f'[Zara] categoryId={category_id}: {saved} товарів збережено')
        time.sleep(1)