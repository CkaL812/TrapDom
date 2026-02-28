import requests
from trapApp.scrapers.base import BaseScraper


class FarfetchBrandScraper(BaseScraper):
    """
    Tom Ford, Giorgio Armani, Sandro не мають локального UA-магазину.
    Найкращий варіант — Farfetch API або SerpAPI Google Shopping.
    Тут показано варіант через SerpAPI (простіший для диплому).
    """
    SERPAPI_KEY = 'YOUR_SERPAPI_KEY'  # Зберігати в .env !
    brand_name = 'Tom Ford'
    formality = 'black_tie'

    CATEGORIES = [
        ('onepiece', 'tuxedo suit'),
        ('onepiece', 'evening gown'),
        ('footwear', 'oxford shoes'),
    ]

    def search(self, query: str) -> list[dict]:
        url = 'https://serpapi.com/search'
        params = {
            'engine': 'google_shopping',
            'q': f'{self.brand_name} {query}',
            'api_key': self.SERPAPI_KEY,
            'num': 20,
        }
        try:
            resp = requests.get(url, params=params, timeout=20)
            return resp.json().get('shopping_results', [])
        except Exception as e:
            print(f'[{self.brand_name}] SerpAPI помилка: {e}')
            return []

    def run(self):
        for category, query in self.CATEGORIES:
            results = self.search(query)
            for r in results:
                self.save_item({
                    'name': r.get('title', ''),
                    'source_url': r.get('link', ''),
                    'category': category,
                    'formality': self.formality,
                    'price': r.get('extracted_price'),
                    'currency': 'USD',
                    'image_url': r.get('thumbnail', ''),
                    'color': '',
                    'material': '',
                    'pattern': 'solid',
                    'gender': 'U',
                }, [])


class GiorgioArmaniScraper(FarfetchBrandScraper):
    brand_name = 'Giorgio Armani'
    formality = 'black_tie'
    CATEGORIES = [
        ('onepiece', 'tuxedo'),
        ('onepiece', 'evening dress'),
        ('layering', 'blazer formal'),
    ]


class SandroScraper(FarfetchBrandScraper):
    brand_name = 'Sandro'
    formality = 'cocktail'
    CATEGORIES = [
        ('onepiece', 'midi dress'),
        ('layering', 'blazer'),
        ('bottoms',  'tailored trousers'),
    ]
