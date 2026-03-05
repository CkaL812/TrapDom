"""
Guess Scraper — Playwright.
ФІКС: guess.eu/en-ua/ таймаутить через Cloudflare + JS-рендеринг.
Переписано на Playwright з locale en-GB.
Вимога: python -m playwright install chromium
"""
import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class GuessScraper(BaseScraper):
    brand_name = 'Guess'
    base_url   = 'https://www.guess.eu'

    CATEGORY_MAP = [
        ('/en-gb/c/men/tops/',      'tops',      'casual',       'M'),
        ('/en-gb/c/men/jeans/',     'bottoms',   'casual',       'M'),
        ('/en-gb/c/men/jackets/',   'outerwear', 'smart_casual', 'M'),
        ('/en-gb/c/women/tops/',    'tops',      'casual',       'F'),
        ('/en-gb/c/women/jeans/',   'bottoms',   'casual',       'F'),
        ('/en-gb/c/women/dresses/', 'onepiece',  'cocktail',     'F'),
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
            for path, category, formality, gender in self.CATEGORY_MAP:
                await self._scrape_category(page, path, category, formality, gender)
            await browser.close()
            print('[Guess] Готово')

    async def _scrape_category(self, page, path, category, formality, gender):
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
        saved = self._parse_html(html, category, formality, gender)
        print(f'[Guess] {path}: {saved} товарів збережено')

    def _parse_html(self, html, category, formality, gender):
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
            price_text = price_el.get_text(strip=True) if price_el else ''
            price = None
            if price_text:
                m = re.search(r'[\d]+\.?\d*', price_text.replace(',', '.'))
                if m:
                    try:
                        price = float(m.group())
                    except ValueError:
                        pass

            img_el = card.select_one('img')
            image_url = ''
            if img_el:
                image_url = img_el.get('data-src') or img_el.get('src') or ''
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
            saved += 1
        return saved