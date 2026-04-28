"""
COS Scraper — SerpAPI Google Shopping.
Playwright повертає 303 redirect (сайт блокує headless браузери).
"""
import os
import hashlib
import requests
from dotenv import load_dotenv
from django.utils import timezone
from trapApp.scrapers.base import BaseScraper

load_dotenv()


class CosScraper(BaseScraper):
    brand_name  = 'COS'
    base_url    = 'https://www.cos.com'
    SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')

    # (query, category, subcategory, formality, gender, seasons)
    CATEGORIES = [
        ('men shirt',           'tops',      'shirt',    'smart_casual',    'M', ['spring', 'summer', 'autumn']),
        ('men t-shirt',         'tops',      't_shirt',  'smart_casual',    'M', ['spring', 'summer']),
        ('men trousers',        'bottoms',   'trousers', 'smart_casual',    'M', ['spring', 'autumn', 'winter']),
        ('men coat jacket',     'outerwear', 'coat',     'smart_casual',    'M', ['autumn', 'winter']),
        ('men knitwear sweater','layering',  'sweater',  'smart_casual',    'M', ['autumn', 'winter']),
        ('men blazer suit',     'layering',  'blazer',   'business_casual', 'M', ['spring', 'autumn']),
        ('women shirt blouse',  'tops',      'blouse',   'smart_casual',    'F', ['spring', 'summer', 'autumn']),
        ('women t-shirt top',   'tops',      't_shirt',  'smart_casual',    'F', ['spring', 'summer']),
        ('women trousers',      'bottoms',   'trousers', 'smart_casual',    'F', ['spring', 'autumn', 'winter']),
        ('women skirt',         'bottoms',   'skirt',    'smart_casual',    'F', ['spring', 'summer', 'autumn']),
        ('women dress',         'onepiece',  'dress',    'cocktail',        'F', ['spring', 'summer', 'autumn']),
        ('women coat jacket',   'outerwear', 'coat',     'smart_casual',    'F', ['autumn', 'winter']),
        ('women knitwear',      'layering',  'sweater',  'smart_casual',    'F', ['autumn', 'winter']),
    ]

    def search(self, query: str) -> list[dict]:
        if not self.SERPAPI_KEY:
            print('[COS] SERPAPI_KEY не заповнено — пропускаємо')
            return []
        params = {
            'engine':  'google_shopping',
            'q':       f'COS {query}',
            'api_key': self.SERPAPI_KEY,
            'num':     20,
        }
        try:
            resp = requests.get('https://serpapi.com/search', params=params, timeout=20)
            resp.raise_for_status()
            return resp.json().get('shopping_results', [])
        except Exception as e:
            print(f'[COS] SerpAPI помилка: {e}')
            return []

    def run(self):
        for query, category, subcategory, formality, gender, seasons in self.CATEGORIES:
            results = self.search(query)
            print(f'[COS] "{query}": {len(results)} результатів')
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
                    link = f'https://www.cos.com/product/{slug}'
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
                    'currency':    'GBP',
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
