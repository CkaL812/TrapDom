import json
import re
import time
import requests
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class HugoBossScraper(BaseScraper):
    brand_name = 'Hugo Boss'
    base_url   = 'https://www.hugoboss.com'
    PAGE_SIZE  = 4

    CATEGORY_MAP = [
        ('/uk/men-shirts/',      'tops',      'smart_casual', 'M'),
        ('/uk/men-polo-shirts/', 'tops',      'smart_casual', 'M'),
        ('/uk/men-trousers/',    'bottoms',   'smart_casual', 'M'),
        ('/uk/men-suits/',       'layering',  'formal',       'M'),
        ('/uk/men-jackets/',     'outerwear', 'smart_casual', 'M'),
        ('/uk/men-jeans/',       'bottoms',   'casual',       'M'),
        ('/uk/women-dresses/',   'onepiece',  'cocktail',     'F'),
        ('/uk/women-blouses/',   'tops',      'smart_casual', 'F'),
        ('/uk/women-trousers/',  'bottoms',   'smart_casual', 'F'),
    ]

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Referer': 'https://www.hugoboss.com/uk/',
        'X-Requested-With': 'XMLHttpRequest',
    }

    def run(self):
        for path, category, formality, gender in self.CATEGORY_MAP:
            self._scrape_category(path, category, formality, gender)

    CATEGORY_LIMIT = 20

    def _scrape_category(self, path, category, formality, gender):
        start = 0
        seen: set[str] = set()

        while True:
            url = f'{self.base_url}{path}?format=ajax&start={start}&sz={self.PAGE_SIZE}'
            print(f'[Hugo Boss] {url}')

            try:
                r = requests.get(url, headers=self.HEADERS, timeout=20)
            except Exception as e:
                print(f'[Hugo Boss] Помилка: {e}')
                break

            if r.status_code != 200:
                print(f'[Hugo Boss] Статус {r.status_code}')
                break

            products = self._parse(r.text)
            if not products:
                print(f'[Hugo Boss] {path}: 0 товарів — стоп')
                break

            new = 0
            for name, source_url, price, image_url in products:
                if source_url in seen:
                    continue
                seen.add(source_url)
                new += 1
                print(f'[Hugo Boss] img: {image_url[:80] if image_url else "EMPTY"}')
                self.save_item({
                    'name':       name[:255],
                    'source_url': source_url[:500],
                    'category':   category,
                    'formality':  formality,
                    'price':      price,
                    'currency':   'GBP',
                    'image_url':  image_url[:500] if image_url else '',
                    'color':      '',
                    'material':   '',
                    'pattern':    'solid',
                    'gender':     gender,
                }, [])

            print(f'[Hugo Boss] start={start}: {new} нових')

            if len(seen) >= self.CATEGORY_LIMIT:
                print(f'[Hugo Boss] {path}: ліміт {self.CATEGORY_LIMIT} — стоп')
                break
            if new < self.PAGE_SIZE:
                break
            start += self.PAGE_SIZE
            time.sleep(1)

    def _parse(self, html: str):
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        seen_urls: set[str] = set()

        for card in soup.select('article.product-tile-plp'):
            a = card.select_one('a.js-product-tile__search-link, a[href*="hugoboss.com"], a[href^="/uk/"]')
            if not a:
                continue
            href = a.get('href', '')
            if not href:
                continue
            source_url = href if href.startswith('http') else self.base_url + href

            if source_url in seen_urls:
                continue

            if not any(x in source_url for x in ['.html', '/p/', 'product']):
                if re.search(r'-\d{5,}', source_url) is None:
                    continue

            product_data = json.loads(card.get('data-as-product', '{}'))
            name = product_data.get('item_name', '').strip()
            if not name or len(name) < 5:
                continue
            price = product_data.get('price') or None

            # Image from data attribute (always present, clean URL)
            image_url = card.get('data-originalimage', '')
            if not image_url:
                img = card.select_one('img[src*="hugoboss"]') or card.select_one('img')
                if img:
                    image_url = img.get('src', '') or img.get('data-src', '')
            if image_url.startswith('//'):
                image_url = 'https:' + image_url

            seen_urls.add(source_url)
            results.append((name, source_url, price, image_url))

        return results
