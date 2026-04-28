"""
Guess Scraper — Playwright.
Вимога: python -m playwright install chromium
"""
import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from bs4 import BeautifulSoup
from django.utils import timezone
from trapApp.scrapers.base import BaseScraper


class GuessScraper(BaseScraper):
    brand_name         = 'Guess'
    base_url           = 'https://www.guess.eu'
    LIMIT_PER_CATEGORY = 20

    # (path, category, subcategory, formality, gender, seasons)
    CATEGORY_MAP = [
        ('/en-gb/c/men/tops/',       'tops',      't_shirt',  'smart_casual', 'M', ['spring', 'summer']),
        ('/en-gb/c/men/shirts/',     'tops',      'shirt',    'smart_casual', 'M', ['spring', 'summer', 'autumn']),
        ('/en-gb/c/men/jeans/',      'bottoms',   'jeans',    'smart_casual', 'M', ['spring', 'summer', 'autumn', 'winter']),
        ('/en-gb/c/men/trousers/',   'bottoms',   'trousers', 'smart_casual', 'M', ['spring', 'autumn', 'winter']),
        ('/en-gb/c/men/jackets/',    'outerwear', 'coat',     'smart_casual', 'M', ['autumn', 'winter']),
        ('/en-gb/c/women/tops/',     'tops',      't_shirt',  'smart_casual', 'F', ['spring', 'summer']),
        ('/en-gb/c/women/jeans/',    'bottoms',   'jeans',    'smart_casual', 'F', ['spring', 'summer', 'autumn', 'winter']),
        ('/en-gb/c/women/dresses/',  'onepiece',  'dress',    'cocktail',     'F', ['spring', 'summer', 'autumn']),
        ('/en-gb/c/women/skirts/',   'bottoms',   'skirt',    'smart_casual', 'F', ['spring', 'summer', 'autumn']),
        ('/en-gb/c/women/jackets/',  'outerwear', 'coat',     'smart_casual', 'F', ['autumn', 'winter']),
    ]

    def run(self):
        print('[Guess] Запуск Playwright...')
        try:
            asyncio.run(self._run_async())
        except Exception as e:
            print(f'[Guess] КРИТИЧНА ПОМИЛКА: {e}')

    async def _run_async(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/121.0.0.0 Safari/537.36'
                ),
                locale='en-GB',
                viewport={'width': 1280, 'height': 900},
            )
            page = await ctx.new_page()
            for path, category, subcategory, formality, gender, seasons in self.CATEGORY_MAP:
                await self._scrape_category(page, path, category, subcategory, formality, gender, seasons)
            await browser.close()
            print('[Guess] Готово')

    async def _scrape_category(self, page, path, category, subcategory, formality, gender, seasons):
        url = self.base_url + path
        print(f'[Guess] → {url}')
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=45_000)
            await page.wait_for_timeout(8_000)
        except PWTimeout:
            print(f'[Guess] Timeout: {url}')
            return
        except Exception as e:
            print(f'[Guess] Помилка: {e}')
            return

        for _ in range(6):
            await page.keyboard.press('End')
            await page.wait_for_timeout(600)

        html = await page.content()
        saved = self._parse_html(html, category, subcategory, formality, gender, seasons)
        print(f'[Guess] {path}: {saved} товарів збережено')

    def _parse_html(self, html, category, subcategory, formality, gender, seasons):
        soup = BeautifulSoup(html, 'html.parser')
        saved = 0
        seen: set[str] = set()

        cards = (
            soup.select('[class*="product-item"]')
            or soup.select('article')
            or soup.select('[class*="ProductCard"]')
        )
        print(f'[Guess] Знайдено карток: {len(cards)}')

        for card in cards:
            if saved >= self.LIMIT_PER_CATEGORY:
                break

            name_el = card.select_one('[class*="name"], [class*="title"], h2, h3')
            name = name_el.get_text(strip=True) if name_el else ''
            if not name or len(name) < 3:
                continue

            link_el = card.select_one('a[href]')
            href = link_el['href'] if link_el else ''
            source_url = href if href.startswith('http') else self.base_url + href
            if not source_url or source_url in seen:
                continue
            seen.add(source_url)

            price_el = card.select_one('[class*="price"], [class*="Price"]')
            price = self._parse_price(price_el.get_text() if price_el else '')

            img_el = card.select_one('img')
            image_url = ''
            if img_el:
                image_url = img_el.get('data-src') or img_el.get('src') or ''
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url

            self.save_item({
                'name':        name[:255],
                'source_url':  source_url[:255],
                'category':    category,
                'subcategory': subcategory,
                'formality':   formality,
                'price':       price,
                'currency':    'GBP',
                'image_url':   image_url[:500],
                'color':       '',
                'material':    '',
                'pattern':     'solid',
                'gender':      gender,
                'seasons':     seasons,
                'tag_source':  'scraper',
                'tagged_at':   timezone.now(),
            }, [])
            saved += 1
        return saved

    @staticmethod
    def _parse_price(text):
        if not text:
            return None
        m = re.search(r'[\d]+\.?\d*', text.replace(',', '.'))
        if m:
            try:
                return float(m.group())
            except ValueError:
                pass
        return None
