import os
import requests
from dotenv import load_dotenv
from trapApp.scrapers.base import BaseScraper

load_dotenv()


class LevisScraper(BaseScraper):
    """
    Levi's — Algolia Search API.
    ФІКС: ключі з .env замість хардкоду.
    Реальні ключі знайти в DevTools → Network → фільтр 'algolia'.
    """
    brand_name = "Levi's"
    base_url   = 'https://www.levi.com/UA/uk_UA'

    ALGOLIA_APP_ID  = os.environ.get('LEVI_ALGOLIA_APP_ID', '')
    ALGOLIA_API_KEY = os.environ.get('LEVI_ALGOLIA_API_KEY', '')
    ALGOLIA_INDEX   = 'levi_UA_products'  # уточнити через DevTools

    CATEGORY_FACETS = [
        ('tops',     'casual',       'mens-tops'),
        ('bottoms',  'casual',       'mens-bottoms'),
        ('tops',     'casual',       'womens-tops'),
        ('bottoms',  'casual',       'womens-bottoms'),
        ('outerwear','smart_casual', 'mens-outerwear'),
    ]

    def search_products(self, category_facet: str) -> list[dict]:
        url = (
            f'https://{self.ALGOLIA_APP_ID}-dsn.algolia.net'
            f'/1/indexes/{self.ALGOLIA_INDEX}/query'
        )
        headers = {
            **self.headers,
            'X-Algolia-Application-Id': self.ALGOLIA_APP_ID,
            'X-Algolia-API-Key':        self.ALGOLIA_API_KEY,
        }
        payload = {'params': f'facetFilters=category:{category_facet}&hitsPerPage=200'}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json().get('hits', [])
        except Exception as e:
            print(f"[Levi's] Помилка: {e}")
            return []

    def run(self):
        if not self.ALGOLIA_APP_ID:
            print("[Levi's] ⚠️  LEVI_ALGOLIA_APP_ID не заповнено в .env — скрапер пропущено")
            return

        for category, formality, facet in self.CATEGORY_FACETS:
            hits = self.search_products(facet)
            print(f"[Levi's] facet={facet} → знайдено: {len(hits)}")
            for hit in hits:
                name = hit.get('name', '')
                if not name:
                    continue
                sizes = [s['label'] for s in hit.get('sizes', []) if s.get('available')]
                self.save_item({
                    'name':       name,
                    'source_url': f"{self.base_url}/{hit.get('url', '')}",
                    'category':   category,
                    'formality':  formality,
                    'price':      hit.get('price'),
                    'currency':   'UAH',
                    'image_url':  hit.get('image', ''),
                    'color':      hit.get('color', ''),
                    'material':   '',
                    'pattern':    'solid',
                    'gender':     'U',
                }, sizes)