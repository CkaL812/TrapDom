import requests
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class DieselScraper(BaseScraper):
    """
    Diesel — HTML scraping каталогу.
    URL: https://www.diesel.com/en-ua/category/clothing
    """
    brand_name = 'Diesel'
    base_url = 'https://www.diesel.com'

    CATEGORY_MAP = [
        ('/en-ua/category/mens-t-shirts',   'tops',      'casual'),
        ('/en-ua/category/mens-jeans',      'bottoms',   'casual'),
        ('/en-ua/category/mens-jackets',    'outerwear', 'smart_casual'),
        ('/en-ua/category/mens-hoodies',    'tops',      'casual'),
        ('/en-ua/category/mens-shoes',      'footwear',  'casual'),
    ]

    def scrape_category(self, path, category, formality):
        url = self.base_url + path
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            print(f'[Diesel] Помилка: {e}')
            return

        for card in soup.select('.product-tile'):
            name_tag = card.select_one('.product-name')
            price_tag = card.select_one('.price .sales .value')
            img_tag = card.select_one('img.tile-image')
            link_tag = card.select_one('a.thumb-link')

            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            price_text = price_tag.get_text(strip=True).replace('\u20b4', '').replace(',', '.').strip() if price_tag else None
            try:
                price = float(price_text) if price_text else None
            except ValueError:
                price = None

            image_url = img_tag.get('src', img_tag.get('data-src', '')) if img_tag else ''
            source_url = self.base_url + link_tag['href'] if link_tag else url

            self.save_item({
                'name': name,
                'source_url': source_url,
                'category': category,
                'formality': formality,
                'price': price,
                'currency': 'UAH',
                'image_url': image_url,
                'color': '',
                'material': '',
                'pattern': 'solid',
                'gender': 'M',
            }, [])

    def run(self):
        for path, category, formality in self.CATEGORY_MAP:
            self.scrape_category(path, category, formality)