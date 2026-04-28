"""
Ted Baker Scraper — Shopify JSON API.
Shopify надає /collections/{handle}/products.json без JS-рендерингу.
"""
import requests
from django.utils import timezone
from trapApp.scrapers.base import BaseScraper


class TedBakerScraper(BaseScraper):
    brand_name         = 'Ted Baker'
    base_url           = 'https://www.tedbaker.com'
    LIMIT_PER_CATEGORY = 20

    # (collection_handle, category, subcategory, formality, gender, seasons)
    CATEGORY_MAP = [
        ('mens-shirts',        'tops',      'shirt',    'business_casual', 'M', ['spring', 'summer', 'autumn']),
        ('mens-t-shirts',      'tops',      't_shirt',  'smart_casual',    'M', ['spring', 'summer']),
        ('mens-trousers',      'bottoms',   'trousers', 'smart_casual',    'M', ['spring', 'autumn', 'winter']),
        ('mens-jackets',       'outerwear', 'coat',     'smart_casual',    'M', ['autumn', 'winter']),
        ('mens-suits',         'layering',  'suit_set', 'business_formal', 'M', ['spring', 'autumn', 'winter']),
        ('womens-tops',        'tops',      'blouse',   'smart_casual',    'F', ['spring', 'summer', 'autumn']),
        ('womens-dresses',     'onepiece',  'dress',    'cocktail',        'F', ['spring', 'summer', 'autumn']),
        ('womens-skirts',      'bottoms',   'skirt',    'smart_casual',    'F', ['spring', 'summer', 'autumn']),
        ('womens-trousers',    'bottoms',   'trousers', 'smart_casual',    'F', ['spring', 'autumn', 'winter']),
        ('womens-shoes',       'footwear',  'heels',    'cocktail',        'F', ['spring', 'summer', 'autumn', 'winter']),
        ('womens-jackets',     'outerwear', 'coat',     'smart_casual',    'F', ['autumn', 'winter']),
    ]

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    def run(self):
        for handle, category, subcategory, formality, gender, seasons in self.CATEGORY_MAP:
            self._scrape_collection(handle, category, subcategory, formality, gender, seasons)

    def _scrape_collection(self, handle, category, subcategory, formality, gender, seasons):
        page  = 1
        saved = 0
        seen: set[str] = set()

        while True:
            url = f'{self.base_url}/collections/{handle}/products.json'
            try:
                resp = requests.get(
                    url,
                    params={'limit': 250, 'page': page},
                    headers=self.HEADERS,
                    timeout=20,
                )
                if resp.status_code != 200:
                    print(f'[Ted Baker] Статус {resp.status_code} для {handle}')
                    break
                data = resp.json()
            except Exception as e:
                print(f'[Ted Baker] Помилка {handle}: {e}')
                break

            products = data.get('products', [])
            if not products:
                break

            for product in products:
                if saved >= self.LIMIT_PER_CATEGORY:
                    break

                source_url = f'{self.base_url}/products/{product["handle"]}'
                if source_url in seen:
                    continue
                seen.add(source_url)

                name = product.get('title', '')
                if not name or len(name) < 3:
                    continue

                price = None
                variants = product.get('variants', [])
                if variants:
                    try:
                        price = float(variants[0].get('price', 0)) or None
                    except (ValueError, TypeError):
                        pass

                image_url = ''
                images = product.get('images', [])
                if images:
                    image_url = images[0].get('src', '')[:500]

                self.save_item({
                    'name':        name[:255],
                    'source_url':  source_url[:255],
                    'category':    category,
                    'subcategory': subcategory,
                    'formality':   formality,
                    'price':       price,
                    'currency':    'GBP',
                    'image_url':   image_url,
                    'color':       '',
                    'material':    '',
                    'pattern':     'solid',
                    'gender':      gender,
                    'seasons':     seasons,
                    'tag_source':  'scraper',
                    'tagged_at':   timezone.now(),
                }, [])
                saved += 1

            print(f'[Ted Baker] {handle} page={page}: {len(products)} знайдено, {saved} всього')
            if len(products) < 250:
                break
            page += 1
