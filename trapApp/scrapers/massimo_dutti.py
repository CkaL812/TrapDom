"""
Massimo Dutti Scraper — SerpAPI Google Shopping.
Inditex API (/ua/uk/category/{id}/products?ajax=true) не працює для MD.
"""
import os
import hashlib
import requests
from dotenv import load_dotenv
from django.utils import timezone
from trapApp.scrapers.base import BaseScraper

load_dotenv()


class MassimoDuttiScraper(BaseScraper):
    brand_name  = 'Massimo Dutti'
    base_url    = 'https://www.massimodutti.com'
    SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')

    # (query, category, subcategory, formality, gender, seasons)
    CATEGORIES = [
        ('Massimo Dutti men shirt',           'tops',      'shirt',    'business_casual', 'M', ['spring', 'summer', 'autumn']),
        ('Massimo Dutti men t-shirt',         'tops',      't_shirt',  'smart_casual',    'M', ['spring', 'summer']),
        ('Massimo Dutti men trousers',        'bottoms',   'trousers', 'business_casual', 'M', ['spring', 'autumn', 'winter']),
        ('Massimo Dutti men suit',            'layering',  'suit_set', 'business_formal', 'M', ['spring', 'autumn', 'winter']),
        ('Massimo Dutti men coat jacket',     'outerwear', 'coat',     'smart_casual',    'M', ['autumn', 'winter']),
        ('Massimo Dutti men knitwear sweater','layering',  'sweater',  'smart_casual',    'M', ['autumn', 'winter']),
        ('Massimo Dutti women shirt blouse',  'tops',      'blouse',   'smart_casual',    'F', ['spring', 'summer', 'autumn']),
        ('Massimo Dutti women t-shirt top',   'tops',      't_shirt',  'smart_casual',    'F', ['spring', 'summer']),
        ('Massimo Dutti women dress',         'onepiece',  'dress',    'cocktail',        'F', ['spring', 'summer', 'autumn']),
        ('Massimo Dutti women skirt',         'bottoms',   'skirt',    'smart_casual',    'F', ['spring', 'summer', 'autumn']),
        ('Massimo Dutti women trousers',      'bottoms',   'trousers', 'smart_casual',    'F', ['spring', 'autumn', 'winter']),
        ('Massimo Dutti women coat jacket',   'outerwear', 'coat',     'smart_casual',    'F', ['autumn', 'winter']),
        ('Massimo Dutti women knitwear',      'layering',  'sweater',  'smart_casual',    'F', ['autumn', 'winter']),
    ]

    def search(self, query: str) -> list[dict]:
        if not self.SERPAPI_KEY:
            print('[Massimo Dutti] SERPAPI_KEY не заповнено — пропускаємо')
            return []
        params = {
            'engine':  'google_shopping',
            'q':       query,
            'api_key': self.SERPAPI_KEY,
            'num':     20,
        }
        try:
            resp = requests.get('https://serpapi.com/search', params=params, timeout=20)
            resp.raise_for_status()
            return resp.json().get('shopping_results', [])
        except Exception as e:
            print(f'[Massimo Dutti] SerpAPI помилка: {e}')
            return []

    def run(self):
        for query, category, subcategory, formality, gender, seasons in self.CATEGORIES:
            results = self.search(query)
            print(f'[Massimo Dutti] "{query}": {len(results)} результатів')
            saved = 0
            seen_urls: set = set()
            for r in results:
                if saved >= 20:
                    break
                name = r.get('title', '')
                if not name or len(name) < 3:
                    continue
                link = r.get('link', '').strip()
                if not link:
                    slug = hashlib.md5(name.encode()).hexdigest()[:16]
                    link = f'https://www.massimodutti.com/product/{slug}'
                link = link[:255]
                if link in seen_urls:
                    continue
                seen_urls.add(link)
                self.save_item({
                    'name':        name[:255],
                    'source_url':  link,
                    'category':    category,
                    'subcategory': subcategory,
                    'formality':   formality,
                    'price':       r.get('extracted_price'),
                    'currency':    'USD',
                    'image_url':   r.get('thumbnail', '')[:500],
                    'color':       '',
                    'material':    '',
                    'pattern':     'solid',
                    'gender':      gender,
                    'seasons':     seasons,
                    'tag_source':  'scraper',
                    'tagged_at':   timezone.now(),
                }, [])
                saved += 1
