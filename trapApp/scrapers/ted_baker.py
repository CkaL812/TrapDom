import requests
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class TedBakerScraper(BaseScraper):
    """
    Ted Baker — HTML scraping каталогу.
    URL: https://www.tedbaker.com/uk/
    """
    brand_name = 'Ted Baker'
    base_url = 'https://www.tedbaker.com'

    CATEGORY_MAP = [
        ('/uk/Mens/Tops/c/MENSTOPS',          'tops',      'smart_casual', 'M'),
        ('/uk/Mens/Shirts/c/MENSSHIRTS',       'tops',      'formal',       'M'),
        ('/uk/Mens/Trousers/c/MENSSHOES',      'bottoms',   'smart_casual', 'M'),
        ('/uk/Mens/Jackets/c/MENSJACKETS',     'outerwear', 'smart_casual', 'M'),
        ('/uk/Womens/Tops/c/WOMTOPS',          'tops',      'smart_casual', 'F'),
        ('/uk/Womens/Dresses/c/WOMDRESSES',    'onepiece',  'cocktail',     'F'),
        ('/uk/Womens/Shoes/c/WOMFOOTWEAR',     'footwear',  'smart_casual', 'F'),
    ]

    def scrape_category(self, path, category, formality, gender):
        url = self.base_url + path
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            print(f'[Ted Baker] Помилка: {e}')
            return

        for card in soup.select('.product-tile, [data-component="ProductCard"]'):
            name_tag = card.select_one('[class*="product-name"], [class*="ProductName"]')
            price_tag = card.select_one('[class*="price"], [class*="Price"]')
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
                'currency': 'GBP',
                'image_url': image_url,
                'color': '',
                'material': '',
                'pattern': 'solid',
                'gender': gender,
            }, [])

    def run(self):
        for path, category, formality, gender in self.CATEGORY_MAP:
            self.scrape_category(path, category, formality, gender)