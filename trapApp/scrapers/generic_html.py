from trapApp.scrapers.base import BaseScraper


class GenericHTMLScraper(BaseScraper):
    brand_name = 'Tommy Hilfiger'
    base_url = 'https://ua.tommy.com'

    CATEGORY_URLS = [
        ('/uk/en_uk/mens/shirts/', 'tops', 'smart_casual', 'M'),
        ('/uk/en_uk/mens/chinos/',  'bottoms', 'smart_casual', 'M'),
    ]

    # CSS-селектори для конкретного сайту
    SELECTORS = {
        'product_card': '.product-tile',
        'name':         '.product-tile__name',
        'price':        '.product-tile__price',
        'image':        'img.product-tile__image',
        'link':         'a.product-tile__link',
        'size_btn':     'button.size-button:not(.size-button--unavailable)',
    }

    def scrape_listing(self, path, category, formality, gender):
        url = self.base_url + path
        soup = self.fetch(url)
        if not soup:
            return

        for card in soup.select(self.SELECTORS['product_card']):
            name_el  = card.select_one(self.SELECTORS['name'])
            price_el = card.select_one(self.SELECTORS['price'])
            img_el   = card.select_one(self.SELECTORS['image'])
            link_el  = card.select_one(self.SELECTORS['link'])

            if not name_el:
                continue

            name = name_el.get_text(strip=True)
            source_url = self.base_url + link_el.get('href', '') if link_el else ''
            image_url = img_el.get('src', '') if img_el else ''
            price_text = price_el.get_text(strip=True) if price_el else ''

            price = None
            for char in ['£', '€', '$', 'UAH', '₴', ',']:
                price_text = price_text.replace(char, '').strip()
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
                'name': name,
                'source_url': source_url,
                'category': category,
                'formality': formality,
                'price': price,
                'currency': 'UAH',
                'image_url': image_url,
                'gender': gender,
                'color': '',
                'material': '',
                'pattern': 'solid',
            }, sizes)

    def run(self):
        for path, category, formality, gender in self.CATEGORY_URLS:
            self.scrape_listing(path, category, formality, gender)
