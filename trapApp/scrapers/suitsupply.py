import requests
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class SuitsupplyScraper(BaseScraper):
    """
    Suitsupply — HTML scraping каталогу.
    URL: https://eu.suitsupply.com/en_UA/
    """
    brand_name = 'Suitsupply'
    base_url = 'https://eu.suitsupply.com'

    CATEGORY_MAP = [
        ('/en_UA/suits/',       'outerwear', 'formal'),
        ('/en_UA/trousers/',    'bottoms',   'formal'),
        ('/en_UA/shirts/',      'tops',      'formal'),
        ('/en_UA/jackets/',     'outerwear', 'smart_casual'),
        ('/en_UA/ties/',        'accessories','formal'),
        ('/en_UA/shoes/',       'footwear',  'formal'),
        ('/en_UA/coats/',       'outerwear', 'formal'),
    ]

    def scrape_category(self, path, category, formality):
        url = self.base_url + path
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            print(f'[Suitsupply] Помилка: {e}')
            return

        for card in soup.select('.product-tile, [class*="ProductCard"]'):
            name_tag = card.select_one('[class*="name"], [class*="title"]')
            price_tag = card.select_one('[class*="price"]')
            img_tag = card.select_one('img')
            link_tag = card.select_one('a')

            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            price_text = price_tag.get_text(strip=True) if price_tag else ''
            try:
                price = float(''.join(c for c in price_text if c.isdigit() or c == '.'))
            except (ValueError, TypeError):
                price = None

            image_url = img_tag.get('src', img_tag.get('data-src', '')) if img_tag else ''
            href = link_tag.get('href', '') if link_tag else ''
            source_url = href if href.startswith('http') else self.base_url + href

            self.save_item({
                'name': name,
                'source_url': source_url,
                'category': category,
                'formality': formality,
                'price': price,
                'currency': 'EUR',
                'image_url': image_url,
                'color': '',
                'material': '',
                'pattern': 'solid',
                'gender': 'M',
            }, [])

    def run(self):
        for path, category, formality in self.CATEGORY_MAP:
            self.scrape_category(path, category, formality)