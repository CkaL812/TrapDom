"""
COS Scraper — Playwright.
api.cos.com мертвий. Використовується фіксований wait.
Вимога: python -m playwright install chromium
"""
import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class CosScraper(BaseScraper):
    brand_name = 'COS'
    base_url   = 'https://www.cos.com'

    CATEGORY_MAP = [
        ('/en-gb/men/shirts',          'tops',      'smart_casual', 'M'),
        ('/en-gb/men/trousers',         'bottoms',   'smart_casual', 'M'),
        ('/en-gb/men/coats-jackets',    'outerwear', 'smart_casual', 'M'),
        ('/en-gb/men/knitwear',         'tops',      'casual',       'M'),
        ('/en-gb/women/shirts-blouses', 'tops',      'smart_casual', 'F'),
        ('/en-gb/women/trousers',       'bottoms',   'smart_casual', 'F'),
        ('/en-gb/women/dresses',        'onepiece',  'cocktail',     'F'),
        ('/en-gb/women/coats-jackets',  'outerwear', 'smart_casual', 'F'),
    ]

    def run(self):
        print('[COS] Запуск Playwright...')
        try:
            asyncio.run(self._run_async())
        except Exception as e:
            print(f'[COS] КРИТИЧНА ПОМИЛКА: {e}')
            print('[COS] Переконайся що chromium встановлений: python -m playwright install chromium')

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
            print('[COS] Chromium готовий')
            for path, category, formality, gender in self.CATEGORY_MAP:
                await self._scrape_category(page, path, category, formality, gender)
            await browser.close()
            print('[COS] Готово')

    async def _scrape_category(self, page, path, category, formality, gender):
        url = f'{self.base_url}{path}'
        print(f'[COS] → {url}')
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=40_000)
            await page.wait_for_timeout(8_000)
        except PWTimeout:
            print(f'[COS] Timeout: {url}')
            return
        except Exception as e:
            print(f'[COS] Помилка goto: {e}')
            return

        for _ in range(8):
            await page.keyboard.press('End')
            await page.wait_for_timeout(600)

        html = await page.content()
        print(f'[COS] HTML отримано ({len(html)} байт)')
        saved = self._parse_html(html, category, formality, gender)
        print(f'[COS] {category}/{gender}: {saved} товарів збережено')

    def _parse_html(self, html, category, formality, gender):
        soup = BeautifulSoup(html, 'html.parser')
        cards = (
            soup.select('article')
            or soup.select('[data-testid="product"]')
            or soup.select('[class*="ProductCard"]')
            or soup.select('[class*="product-tile"]')
            or soup.select('[class*="product-item"]')
        )
        print(f'[COS] Знайдено карток: {len(cards)}')

        if not cards:
            cards = []
            for a in soup.select('a[href*="/en-gb/"]'):
                h = a.select_one('h2, h3, [class*="name"]')
                if h:
                    cards.append(a)

        saved = 0
        seen: set[str] = set()
        for card in cards:
            name_el = (
                card.select_one('h2') or card.select_one('h3')
                or card.select_one('[class*="name"]')
                or card.select_one('[class*="title"]')
            )
            name = name_el.get_text(strip=True) if name_el else ''
            if not name or len(name) < 3:
                continue

            link_el = card.select_one('a[href]') if card.name != 'a' else card
            href = link_el.get('href', '') if link_el else ''
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
                'price': price, 'currency': 'GBP',
                'image_url': image_url, 'color': '', 'material': '',
                'pattern': 'solid', 'gender': gender,
            }, [])
            saved += 1
        return saved

    @staticmethod
    def _parse_price(text):
        if not text:
            return None
        m = re.search(r'[\d]+\.?\d*', text.replace('£', '').replace(',', ''))
        if m:
            try:
                return float(m.group())
            except ValueError:
                pass
        return None