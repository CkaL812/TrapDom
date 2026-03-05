"""
Massimo Dutti Scraper — Playwright.
Фіксований wait 12с (сайт повільний).
Вимога: python -m playwright install chromium
"""
import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class MassimoDuttiScraper(BaseScraper):
    brand_name = 'Massimo Dutti'
    base_url   = 'https://www.massimodutti.com'

    CATEGORY_MAP = [
        ('/ua/uk/man-shirts-l737.html',           'tops',      'smart_casual', 'M'),
        ('/ua/uk/man-trousers-l610.html',          'bottoms',   'smart_casual', 'M'),
        ('/ua/uk/man-outerwear-l657.html',         'outerwear', 'smart_casual', 'M'),
        ('/ua/uk/woman-shirts-blouses-l1217.html', 'tops',      'smart_casual', 'F'),
        ('/ua/uk/woman-dresses-l1066.html',        'onepiece',  'cocktail',     'F'),
        ('/ua/uk/woman-trousers-l1335.html',       'bottoms',   'smart_casual', 'F'),
        ('/ua/uk/woman-outerwear-l1184.html',      'outerwear', 'smart_casual', 'F'),
    ]

    def run(self):
        asyncio.run(self._run_async())

    async def _run_async(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/121.0.0.0 Safari/537.36'
                ),
                locale='uk-UA',
                viewport={'width': 1280, 'height': 900},
            )
            page = await ctx.new_page()
            for path, category, formality, gender in self.CATEGORY_MAP:
                await self._scrape_category(page, path, category, formality, gender)
            await browser.close()

    async def _scrape_category(self, page, path, category, formality, gender):
        url = f'{self.base_url}{path}'
        print(f'[Massimo Dutti] → {url}')
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=60_000)
            await page.wait_for_timeout(12_000)
        except PWTimeout:
            print(f'[Massimo Dutti] Timeout: {url}')
            return
        except Exception as e:
            print(f'[Massimo Dutti] Помилка: {e}')
            return

        try:
            for txt in ['Accept all', 'Accept', 'Дозволити все']:
                btn = page.locator(f'button:has-text("{txt}")')
                if await btn.count() > 0:
                    await btn.first.click()
                    await page.wait_for_timeout(1500)
                    break
        except Exception:
            pass

        for _ in range(10):
            await page.keyboard.press('End')
            await page.wait_for_timeout(500)

        html = await page.content()
        saved = self._parse_html(html, category, formality, gender)
        print(f'[Massimo Dutti] {path}: {saved} товарів збережено')

    def _parse_html(self, html, category, formality, gender):
        soup = BeautifulSoup(html, 'html.parser')
        saved = 0
        seen: set[str] = set()

        cards = (
            soup.select('article')
            or soup.select('[class*="ProductCard"]')
            or soup.select('[class*="product-item"]')
            or soup.select('li[class*="product"]')
        )
        print(f'[Massimo Dutti] Знайдено карток: {len(cards)}')

        for card in cards:
            name_el = (
                card.select_one('h2') or card.select_one('h3')
                or card.select_one('[class*="name"]')
            )
            name = name_el.get_text(strip=True) if name_el else ''
            if not name or len(name) < 3:
                continue

            link_el = card.select_one('a[href]')
            href = link_el['href'] if link_el else ''
            source_url = href if href.startswith('http') else self.base_url + href
            if not source_url or source_url in seen:
                continue
            seen.add(source_url)

            price_el = (
                card.select_one('[class*="price"]')
                or card.select_one('[class*="Price"]')
            )
            price = self._parse_price(price_el.get_text() if price_el else '')

            img_el = card.select_one('img')
            image_url = ''
            if img_el:
                image_url = img_el.get('data-src') or img_el.get('src') or ''
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url

            self.save_item({
                'name': name, 'source_url': source_url,
                'category': category, 'formality': formality,
                'price': price, 'currency': 'UAH',
                'image_url': image_url, 'color': '', 'material': '',
                'pattern': 'solid', 'gender': gender,
            }, [])
            saved += 1
        return saved

    @staticmethod
    def _parse_price(text):
        if not text:
            return None
        cleaned = text.replace('\xa0', '').replace('\u202f', '').replace(' ', '')
        m = re.search(r'[\d]+[,.]?\d*', cleaned)
        if m:
            try:
                return float(m.group().replace(',', '.'))
            except ValueError:
                pass
        return None