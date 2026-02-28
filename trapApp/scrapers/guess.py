import requests
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class GuessScraper(BaseScraper):
    """
    Guess — HTML scraping каталогу.
    URL: https://www.guess.eu/en-ua/
    """
    brand_name = 'Guess'
    base_url = 'https://www.guess.eu'

    CATEGORY_MAP = [
        ('/en-ua/c/men/tops/',       'tops',      'casual'),
        ('/en-ua/c/men/jeans/',      'bottoms',   'casual'),
        ('/en-ua/c/men/jackets/',    'outerwear', 'smart_casual'),
        ('/en-ua/c/women/tops/',     'tops',      'casual'),
        ('/en-ua/c/women/jeans/',    'bottoms',   'casual'),
        ('/en-ua/c/women/dresses/',  'onepiece',  'cocktail'),
        ('/en-ua/c/accessories/',    'accessories','casual'),
    ]

    GENDER_MAP = {
        'men':   'M',
        'women': 'F',
    }

    def scrape_category(self, path, category, formality):
        url = self.base_url + path
        gender = 'M'
        for key, val in self.GENDER_MAP.items():
            if key in path:
                gender = val
                break
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            print(f'[Guess] Помилка: {e}')
            return

        for card in soup.select('.product-item'):
            name_tag = card.select_one('.product-item-name')
            price_tag = card.select_one('.price')
            img_tag = card.select_one('img.product-image-photo')
            link_tag = card.select_one('a.product-item-link')

            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            price_text = price_tag.get_text(strip=True).replace('\u20b4','').replace('\u20ac','').replace(',','.').strip() if price_tag else None
            try:
                price = float(price_text) if price_text else None
            except ValueError:
                price = None

            image_url = img_tag.get('src', '') if img_tag else ''
            source_url = link_tag['href'] if link_tag else url

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
                'gender': gender,
            }, [])

    def run(self):
        for path, category, formality in self.CATEGORY_MAP:
            self.scrape_category(path, category, formality)