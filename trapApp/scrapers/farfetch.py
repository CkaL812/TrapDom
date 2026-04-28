import os
import requests
from dotenv import load_dotenv
from django.utils import timezone
from trapApp.scrapers.base import BaseScraper

load_dotenv()


class _SerpApiBrandScraper(BaseScraper):
    """Базовий клас для брендів через SerpAPI Google Shopping."""

    SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')
    base_url    = ''

    # Список (query, category, subcategory, formality, gender, seasons)
    CATEGORIES: list[tuple] = []

    def search(self, query: str) -> list[dict]:
        if not self.SERPAPI_KEY:
            print(f'[{self.brand_name}] SERPAPI_KEY не заповнено — пропускаємо')
            return []
        params = {
            'engine':  'google_shopping',
            'q':       f'{self.brand_name} {query}',
            'api_key': self.SERPAPI_KEY,
            'num':     20,
        }
        try:
            resp = requests.get('https://serpapi.com/search', params=params, timeout=20)
            resp.raise_for_status()
            return resp.json().get('shopping_results', [])
        except Exception as e:
            print(f'[{self.brand_name}] SerpAPI помилка: {e}')
            return []

    def run(self):
        for query, category, subcategory, formality, gender, seasons in self.CATEGORIES:
            results = self.search(query)
            print(f'[{self.brand_name}] "{query}": {len(results)} результатів')
            for r in results:
                name = r.get('title', '')
                if not name or len(name) < 3:
                    continue
                self.save_item({
                    'name':        name[:255],
                    'source_url':  r.get('link', '')[:255],
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


class TomFordScraper(_SerpApiBrandScraper):
    brand_name = 'Tom Ford'
    CATEGORIES = [
        ('tuxedo suit men',     'layering',  'suit_set', 'black_tie', 'M', ['autumn', 'winter']),
        ('oxford shoes men',    'footwear',  'loafers',  'black_tie', 'M', ['spring', 'autumn', 'winter']),
        ('evening gown women',  'onepiece',  'dress',    'black_tie', 'F', ['autumn', 'winter']),
        ('cocktail dress women','onepiece',  'dress',    'cocktail',  'F', ['spring', 'autumn']),
    ]


class GiorgioArmaniScraper(_SerpApiBrandScraper):
    brand_name = 'Giorgio Armani'
    CATEGORIES = [
        ('tuxedo men',          'layering',  'suit_set', 'black_tie',        'M', ['autumn', 'winter']),
        ('blazer formal men',   'layering',  'blazer',   'business_formal',  'M', ['spring', 'autumn', 'winter']),
        ('evening dress women', 'onepiece',  'dress',    'black_tie',        'F', ['autumn', 'winter']),
        ('cocktail dress women','onepiece',  'dress',    'cocktail',         'F', ['spring', 'autumn']),
    ]


class SandroScraper(_SerpApiBrandScraper):
    brand_name = 'Sandro'
    CATEGORIES = [
        ('midi dress women',       'onepiece', 'dress',    'cocktail',        'F', ['spring', 'summer', 'autumn']),
        ('blazer women',           'layering', 'blazer',   'business_casual', 'F', ['spring', 'autumn']),
        ('tailored trousers women','bottoms',  'trousers', 'business_casual', 'F', ['spring', 'autumn', 'winter']),
        ('shirt men',              'tops',     'shirt',    'smart_casual',    'M', ['spring', 'summer', 'autumn']),
        ('trousers men',           'bottoms',  'trousers', 'smart_casual',    'M', ['spring', 'autumn', 'winter']),
    ]
