import requests
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class TedBakerScraper(BaseScraper):
    """
    Ted Baker — HTML scraping каталогу.
    ФІКС: Сайт переїхав з SAP Hybris на Shopify.
    Старі URL /uk/Mens/Tops/c/MENSTOPS → нові /collections/mens-tops
    """
    brand_name = 'Ted Baker'
    base_url   = 'https://www.tedbaker.com'

    CATEGORY_MAP = [
        ('/collections/mens-shirts',    'tops',      'formal',       'M'),
        ('/collections/mens-t-shirts',  'tops',      'casual',       'M'),
        ('/collections/mens-trousers',  'bottoms',   'smart_casual', 'M'),
        ('/collections/mens-jackets',   'outerwear', 'smart_casual', 'M'),
        ('/collections/womens-tops',    'tops',      'smart_casual', 'F'),
        ('/collections/womens-dresses', 'onepiece',  'cocktail',     'F'),
        ('/collections/womens-trousers','bottoms',   'smart_casual', 'F'),
        ('/collections/womens-shoes',   'footwear',  'smart_casual', 'F'),
    ]

    def scrape_category(self, path, category, formality, gender):
        url = self.base_url + path
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            print(f'[Ted Baker] Помилка: {e}')
            return

        # Shopify-структура карток
        cards = (
            soup.select('.product-card')
            or soup.select('[class*="ProductCard"]')
            or soup.select('.grid__item')
            or soup.select('[class*="product-item"]')
        )
        print(f'[Ted Baker] Знайдено карток: {len(cards)}')

        seen: set[str] = set()
        for card in cards:
            name_tag = (
                card.select_one('.product-card__title')
                or card.select_one('[class*="product-title"]')
                or card.select_one('h2') or card.select_one('h3')
            )
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

            price_tag = card.select_one('.price, .product-card__price, [class*="price"]')
            price_text = price_tag.get_text(strip=True) if price_tag else ''
            try:
                price = float(''.join(c for c in price_text if c.isdigit() or c == '.') or '0') or None
            except (ValueError, TypeError):
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