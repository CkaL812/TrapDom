from trapApp.scrapers.base import BaseScraper


class GenericHTMLScraper(BaseScraper):
    """
    Tommy Hilfiger — HTML scraping каталогу.
    ФІКС: ua.tommy.com не існує → tommy.com/en-gb/
    """
    brand_name = 'Tommy Hilfiger'
    base_url   = 'https://www.tommy.com'

    CATEGORY_URLS = [
        ('/en-gb/men/shirts/',        'tops',      'smart_casual', 'M'),
        ('/en-gb/men/chinos/',        'bottoms',   'smart_casual', 'M'),
        ('/en-gb/men/jackets/',       'outerwear', 'smart_casual', 'M'),
        ('/en-gb/men/t-shirts/',      'tops',      'casual',       'M'),
        ('/en-gb/women/tops/',        'tops',      'smart_casual', 'F'),
        ('/en-gb/women/dresses/',     'onepiece',  'smart_casual', 'F'),
        ('/en-gb/women/trousers/',    'bottoms',   'smart_casual', 'F'),
    ]

    SELECTORS = {
        'product_card': '.product-tile, [class*="ProductCard"], .grid__item',
        'name':         '[class*="product-name"], [class*="product-title"], h2, h3',
        'price':        '[class*="price"], [class*="Price"]',
        'image':        'img',
        'link':         'a[href]',
        'size_btn':     'button.size-button:not(.size-button--unavailable)',
    }

    def scrape_listing(self, path, category, formality, gender):
        url = self.base_url + path
        soup = self.fetch(url)
        if not soup:
            return

        cards = soup.select(self.SELECTORS['product_card'])
        print(f'[Tommy Hilfiger] Знайдено карток: {len(cards)}')

        seen: set[str] = set()
        for card in cards:
            name_el  = card.select_one(self.SELECTORS['name'])
            price_el = card.select_one(self.SELECTORS['price'])
            img_el   = card.select_one(self.SELECTORS['image'])
            link_el  = card.select_one(self.SELECTORS['link'])

            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) < 3:
                continue

            href = link_el.get('href', '') if link_el else ''
            source_url = href if href.startswith('http') else self.base_url + href
            if not source_url or source_url in seen:
                continue
            seen.add(source_url)

            image_url = ''
            if img_el:
                image_url = img_el.get('data-src') or img_el.get('src') or ''
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url

            price_text = price_el.get_text(strip=True) if price_el else ''
            for char in ['£', '€', '$', 'GBP', 'UAH', '₴', ',']:
                price_text = price_text.replace(char, '').strip()
            price = None
            try:
                price = float(price_text.split()[0])
            except Exception:
                pass

            sizes = []
            if source_url:
                detail_soup = self.fetch(source_url)
                if detail_soup:
                    sizes = [
                        el.get_text(strip=True)
                        for el in detail_soup.select(self.SELECTORS['size_btn'])
                    ]

            self.save_item({
                'name':       name,
                'source_url': source_url,
                'category':   category,
                'formality':  formality,
                'price':      price,
                'currency':   'GBP',
                'image_url':  image_url,
                'gender':     gender,
                'color':      '',
                'material':   '',
                'pattern':    'solid',
            }, sizes)

    def run(self):
        for path, category, formality, gender in self.CATEGORY_URLS:
            self.scrape_listing(path, category, formality, gender)