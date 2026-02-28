import requests
from bs4 import BeautifulSoup
from trapApp.models import Brand, ClothingItem, ClothingSize
import time


class BaseScraper:
    brand_name: str = ''
    base_url: str = ''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8',
    }
    delay: float = 1.5  # секунди між запитами

    def get_brand(self) -> Brand:
        brand, _ = Brand.objects.get_or_create(
            name=self.brand_name,
            defaults={'website': self.base_url, 'formality_range': 'mixed'}
        )
        return brand

    def fetch(self, url: str) -> BeautifulSoup | None:
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            time.sleep(self.delay)
            return BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            print(f'[{self.brand_name}] Помилка при запиті {url}: {e}')
            return None

    def save_item(self, data: dict, sizes: list[str]) -> ClothingItem | None:
        """data — словник полів ClothingItem (без id/brand). sizes — список рядків."""
        brand = self.get_brand()
        item, created = ClothingItem.objects.update_or_create(
            source_url=data['source_url'],
            defaults={**data, 'brand': brand}
        )
        for size_label in sizes:
            ClothingSize.objects.get_or_create(item=item, size_label=size_label)
        action = 'Додано' if created else 'Оновлено'
        print(f'[{self.brand_name}] {action}: {item.name}')
        return item

    def run(self):
        raise NotImplementedError('Реалізуй метод run() у підкласі')

