import requests
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class DieselScraper(BaseScraper):
    """
    Diesel — HTML scraping каталогу.
    ФІКС: en-ua більше не існує, перейшли на en-gb.
    """
    brand_name = 'Diesel'
    base_url   = 'https://www.diesel.com'

    CATEGORY_MAP = [
        ('/en-gb/category/mens-t-shirts',  'tops',      'casual',       'M'),
        ('/en-gb/category/mens-jeans',     'bottoms',   'casual',       'M'),
        ('/en-gb/category/mens-jackets',   'outerwear', 'smart_casual', 'M'),
        ('/en-gb/category/mens-hoodies',   'tops',      'casual',       'M'),
        ('/en-gb/category/mens-shoes',     'footwear',  'casual',       'M'),
    ]

    def scrape_category(self, path, category, formality, gender):
        url = self.base_url + path
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            print(f'[Diesel] Помилка: {e}')
            return

        # Diesel оновив верстку — широкий набір селекторів
        cards = (
            soup.select('[data-product-id]')
            or soup.select('.product-tile')
            or soup.select('article')
            or soup.select('[class*="ProductCard"]')
        )
        print(f'[Diesel] Знайдено карток: {len(cards)}')

        seen: set[str] = set()
        for card in cards:
            name_tag = card.select_one('[class*="name"], [class*="title"], h2, h3')
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)
            if not name or len(name) < 3:
                continue

            link_tag = card.select_one('a[href]')
            href = link_tag['href'] if link_tag else ''
            source_url = href if href.startswith('http') else self.base_url + href
            if not source_url or source_url in seen:
                continue
            seen.add(source_url)

            price_tag = card.select_one('[class*="price"], [class*="Price"]')
            price_text = price_tag.get_text(strip=True) if price_tag else ''
            try:
                price = float(''.join(c for c in price_text if c.isdigit() or c == '.') or '0') or None
            except ValueError:
                price = None

            img_tag = card.select_one('img')
            image_url = ''
            if img_tag:
                image_url = img_tag.get('data-src') or img_tag.get('src') or ''
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url

            self.save_item({
                'name':       name,
                'source_url': source_url,
                'category':   category,
                'formality':  formality,
                'price':      price,
                'currency':   'GBP',
                'image_url':  image_url,
                'color':      '',
                'material':   '',
                'pattern':    'solid',
                'gender':     gender,
            }, [])

    def run(self):
        for path, category, formality, gender in self.CATEGORY_MAP:
            self.scrape_category(path, category, formality, gender)