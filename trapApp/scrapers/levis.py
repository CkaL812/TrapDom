import os
import requests
from dotenv import load_dotenv
from django.utils import timezone
from trapApp.scrapers.base import BaseScraper

load_dotenv()


class LevisScraper(BaseScraper):
    """
    Levi's — Algolia Search API.
    Ключі знайти в DevTools → Network → фільтр 'algolia'.
    """
    brand_name = "Levi's"
    base_url   = 'https://www.levi.com/UA/uk_UA'

    ALGOLIA_APP_ID  = os.environ.get('LEVI_ALGOLIA_APP_ID', '')
    ALGOLIA_API_KEY = os.environ.get('LEVI_ALGOLIA_API_KEY', '')
    ALGOLIA_INDEX   = 'levi_UA_products'

    # (facet, category, subcategory, formality, gender, seasons)
    CATEGORY_FACETS = [
        ('mens-tops',      'tops',      't_shirt',  'smart_casual', 'M', ['spring', 'summer']),
        ('mens-shirts',    'tops',      'shirt',    'smart_casual', 'M', ['spring', 'summer', 'autumn']),
        ('mens-bottoms',   'bottoms',   'jeans',    'smart_casual', 'M', ['spring', 'summer', 'autumn', 'winter']),
        ('mens-outerwear', 'outerwear', 'coat',     'smart_casual', 'M', ['autumn', 'winter']),
        ('womens-tops',    'tops',      't_shirt',  'smart_casual', 'F', ['spring', 'summer']),
        ('womens-bottoms', 'bottoms',   'jeans',    'smart_casual', 'F', ['spring', 'summer', 'autumn', 'winter']),
        ('womens-dresses', 'onepiece',  'dress',    'smart_casual', 'F', ['spring', 'summer', 'autumn']),
    ]

    def search_products(self, facet: str) -> list[dict]:
        url = (
            f'https://{self.ALGOLIA_APP_ID}-dsn.algolia.net'
            f'/1/indexes/{self.ALGOLIA_INDEX}/query'
        )
        headers = {
            **self.headers,
            'X-Algolia-Application-Id': self.ALGOLIA_APP_ID,
            'X-Algolia-API-Key':        self.ALGOLIA_API_KEY,
        }
        payload = {'params': f'facetFilters=category:{facet}&hitsPerPage=200'}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json().get('hits', [])
        except Exception as e:
            print(f"[Levi's] Помилка: {e}")
            return []

    def run(self):
        if not self.ALGOLIA_APP_ID:
            print("[Levi's] LEVI_ALGOLIA_APP_ID не заповнено в .env — скрапер пропущено")
            return

        for facet, category, subcategory, formality, gender, seasons in self.CATEGORY_FACETS:
            hits = self.search_products(facet)[:20]
            print(f"[Levi's] facet={facet} → знайдено: {len(hits)}")
            for hit in hits:
                name = hit.get('name', '')
                if not name:
                    continue
                sizes = [s['label'] for s in hit.get('sizes', []) if s.get('available')]
                self.save_item({
                    'name':        name[:255],
                    'source_url':  f"{self.base_url}/{hit.get('url', '')}",
                    'category':    category,
                    'subcategory': subcategory,
                    'formality':   formality,
                    'price':       hit.get('price'),
                    'currency':    'UAH',
                    'image_url':   hit.get('image', '')[:500],
                    'color':       hit.get('color', '')[:100],
                    'material':    '',
                    'pattern':     'solid',
                    'gender':      gender,
                    'seasons':     seasons,
                    'tag_source':  'scraper',
                    'tagged_at':   timezone.now(),
                }, sizes)
