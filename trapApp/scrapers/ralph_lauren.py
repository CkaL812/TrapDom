"""
Ralph Lauren Scraper — Playwright + stealth.
Cloudflare px-captcha блокує звичайний headless.
pip install playwright-stealth
Вимога: python -m playwright install chromium
"""
import asyncio
import re
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from bs4 import BeautifulSoup
from trapApp.scrapers.base import BaseScraper

try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False
    print('[Ralph Lauren] ⚠️  playwright-stealth не встановлений (pip install playwright-stealth)')


class RalphLaurenScraper(BaseScraper):
    brand_name = 'Ralph Lauren'
    base_url   = 'https://www.ralphlauren.com'

    CATEGORY_MAP = [
        ('/men/clothing/polos',         'tops',      'smart_casual', 'M'),
        ('/men/clothing/shirts',        'tops',      'formal',       'M'),
        ('/men/clothing/pants',         'bottoms',   'smart_casual', 'M'),
        ('/men/clothing/jackets-coats', 'outerwear', 'smart_casual', 'M'),
        ('/women/clothing/tops',        'tops',      'smart_casual', 'F'),
        ('/women/clothing/dresses',     'onepiece',  'cocktail',     'F'),
        ('/women/clothing/pants-jeans', 'bottoms',   'casual',       'F'),
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
                locale='en-US',
                viewport={'width': 1440, 'height': 900},
                extra_http_headers={'Accept-Language': 'en-US,en;q=0.9'},
            )
            page = await ctx.new_page()
            if HAS_STEALTH:
                await stealth_async(page)
                print('[Ralph Lauren] Stealth mode активний')

            try:
                await page.goto(self.base_url, wait_until='domcontentloaded', timeout=30_000)
                await page.wait_for_timeout(3000)
            except Exception:
                pass

            for path, category, formality, gender in self.CATEGORY_MAP:
                await self._scrape_category(page, path, category, formality, gender)
            await browser.close()

    async def _scrape_category(self, page, path, category, formality, gender):
        url = f'{self.base_url}{path}'
        print(f'[Ralph Lauren] → {url}')
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=60_000)
            await page.wait_for_timeout(10_000)
        except PWTimeout:
            print(f'[Ralph Lauren] Timeout: {url}')
            return
        except Exception as e:
            print(f'[Ralph Lauren] Помилка: {e}')
            return

        for _ in range(10):
            await page.keyboard.press('End')
            await page.wait_for_timeout(500)

        html = await page.content()
        if 'px-captcha' in html or 'Access to this page has been denied' in html:
            print(f'[Ralph Lauren] ❌ Cloudflare заблокував: {url}')
            return

        saved = self._parse_html(html, category, formality, gender)
        print(f'[Ralph Lauren] {path}: {saved} товарів збережено')

    def _parse_html(self, html, category, formality, gender):
        soup = BeautifulSoup(html, 'html.parser')
        saved = 0
        seen: set[str] = set()

        cards = (
            soup.select('[class*="product-grid"] li')
            or soup.select('[class*="ProductTile"]')
            or soup.select('[class*="product-tile"]')
            or soup.select('article')
        )
        print(f'[Ralph Lauren] Знайдено карток: {len(cards)}')

        for card in cards:
            name_el = (
                card.select_one('[class*="product-name"]')
                or card.select_one('[class*="ProductName"]')
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
                'price': price, 'currency': 'USD',
                'image_url': image_url, 'color': '',
                'material': '', 'pattern': 'solid', 'gender': gender,
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