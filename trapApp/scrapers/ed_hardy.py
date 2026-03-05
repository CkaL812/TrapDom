"""
Ed Hardy Scraper — Playwright.
Сайт на Shopify: edhardyusa.com
Вимога: python -m playwright install chromium
"""
import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper


class EdHardyScraper(BaseScraper):
    brand_name = 'Ed Hardy'
    base_url   = 'https://www.edhardyusa.com'

    CATEGORY_MAP = [
        ('/collections/mens-t-shirts',  'tops',      'casual', 'M'),
        ('/collections/mens-hoodies',   'tops',      'casual', 'M'),
        ('/collections/mens-jackets',   'outerwear', 'casual', 'M'),
        ('/collections/womens-tops',    'tops',      'casual', 'F'),
        ('/collections/womens-dresses', 'onepiece',  'casual', 'F'),
        ('/collections/womens-jackets', 'outerwear', 'casual', 'F'),
    ]

    def run(self):
        print('[Ed Hardy] Запуск Playwright...')
        try:
            asyncio.run(self._run_async())
        except Exception as e:
            print(f'[Ed Hardy] КРИТИЧНА ПОМИЛКА: {e}')

    async def _run_async(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/121.0.0.0 Safari/537.36'
                ),
                locale='en-US',
                viewport={'width': 1280, 'height': 900},
            )
            page = await ctx.new_page()
            for path, category, formality, gender in self.CATEGORY_MAP:
                await self._scrape_category(page, path, category, formality, gender)
            await browser.close()
            print('[Ed Hardy] Готово')

    async def _scrape_category(self, page, path, category, formality, gender):
        url = self.base_url + path
        print(f'[Ed Hardy] → {url}')
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=45_000)
            await page.wait_for_timeout(6_000)
        except PWTimeout:
            print(f'[Ed Hardy] Timeout: {url}')
            return
        except Exception as e:
            print(f'[Ed Hardy] Помилка: {e}')
            return

        for _ in range(6):
            await page.keyboard.press('End')
            await page.wait_for_timeout(500)

        html = await page.content()
        saved = self._parse_html(html, category, formality, gender)
        print(f'[Ed Hardy] {path}: {saved} товарів збережено')

    def _parse_html(self, html, category, formality, gender):
        soup = BeautifulSoup(html, 'html.parser')
        saved = 0
        seen: set[str] = set()

        # Shopify-структура
        cards = (
            soup.select('.product-card')
            or soup.select('[class*="ProductCard"]')
            or soup.select('.grid__item')
            or soup.select('li[class*="product"]')
        )
        print(f'[Ed Hardy] Знайдено карток: {len(cards)}')

        for card in cards:
            name_el = (
                card.select_one('[class*="product-card__title"]')
                or card.select_one('[class*="product-title"]')
                or card.select_one('h2') or card.select_one('h3')
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

            price_el = card.select_one('[class*="price"]')
            price = self._parse_price(price_el.get_text() if price_el else '')

            img_el = card.select_one('img')
            image_url = ''
            if img_el:
                image_url = (
                    img_el.get('data-src') or
                    img_el.get('src') or
                    (img_el.get('srcset', '').split()[0] if img_el.get('srcset') else '')
                )
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url

            self.save_item({
                'name':       name,
                'source_url': source_url,
                'category':   category,
                'formality':  formality,
                'price':      price,
                'currency':   'USD',
                'image_url':  image_url,
                'color':      '',
                'material':   '',
                'pattern':    'solid',
                'gender':     gender,
            }, [])
            saved += 1
        return saved

    @staticmethod
    def _parse_price(text):
        if not text:
            return None
        m = re.search(r'[\d]+\.?\d*', text.replace('$', '').replace(',', ''))
        if m:
            try:
                return float(m.group())
            except ValueError:
                pass
        return None