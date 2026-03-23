import time
import requests
from trapApp.scrapers.base import BaseScraper


class ZaraScraper(BaseScraper):

    brand_name = 'Zara'
    base_url   = 'https://www.zara.com'

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'uk-UA,uk;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.zara.com/ua/uk/',
    }

    # (category_id, wardrobe_category, formality, gender, seasons, label)
    # Усі ID перевірені автоматичним сканером — повертають реальні товари ✅
    CATEGORY_MAP = [

        # ════════════════════════════════════════════════════════════════
        # ── ЧОЛОВІКИ ────────────────────────────────────────────────────
        # ════════════════════════════════════════════════════════════════

        # ── ЛІТО ────────────────────────────────────────────────────────
        (2436585, 'tops',      'casual',        'M', ['spring', 'summer'],                     'MAN Футболки'),
        (2436584, 'bottoms',   'casual',        'M', ['summer'],                               'MAN Шорти'),
        (2436949, 'tops',      'smart_casual',  'M', ['spring', 'summer'],                     'MAN Сорочки'),
        (2436336, 'footwear',  'casual',        'M', ['spring', 'summer', 'autumn'],           'MAN Кросівки'),
        (2436385, 'footwear',  'casual',        'M', ['summer'],                               'MAN Сандалі/Тапки'),
        (2436386, 'footwear',  'casual',        'M', ['summer'],                               'MAN Шльопанці'),

        # ── ВЕСНА / ОСІНЬ ───────────────────────────────────────────────
        (2473840, 'bottoms',   'smart_casual',  'M', ['spring', 'summer', 'autumn'],           'MAN Штани'),
        (2436311, 'layering',  'business',      'M', ['spring', 'autumn'],                     'MAN Блейзери'),
        (2436384, 'footwear',  'formal',        'M', ['spring', 'autumn', 'winter'],           'MAN Офіційне взуття'),
        (2436388, 'footwear',  'casual',        'M', ['spring', 'autumn'],                     'MAN Черевики'),
        (2436389, 'footwear',  'casual',        'M', ['spring', 'autumn'],                     'MAN Чоботи'),

        # ── ЗИМА ────────────────────────────────────────────────────────
        (2606109, 'outerwear', 'smart_casual',  'M', ['autumn', 'winter'],                     'MAN Пальта/Тренчі'),

        # ── АКСЕСУАРИ (цілий рік) ───────────────────────────────────────
        (2436444, 'accessory', 'casual',        'M', ['spring', 'summer', 'autumn', 'winter'], 'MAN Аксесуари'),
        (2436434, 'accessory', 'casual',        'M', ['spring', 'summer', 'autumn', 'winter'], 'MAN Ремені'),
        (2436436, 'accessory', 'formal',        'M', ['autumn', 'winter'],                     'MAN Краватки'),


        # ════════════════════════════════════════════════════════════════
        # ── ЖІНКИ ───────────────────────────────────────────────────────
        # ════════════════════════════════════════════════════════════════

        # ── ЛІТО ────────────────────────────────────────────────────────
        (2420386, 'tops',      'casual',        'F', ['spring', 'summer'],                     'WOMAN Футболки'),          # 200 товарів ✅
        (2419892, 'tops',      'casual',        'F', ['spring', 'summer'],                     'WOMAN Топи'),              # 402 товари ✅
        (2420896, 'onepiece',  'cocktail',      'F', ['spring', 'summer'],                     'WOMAN Сукні (літо)'),      # 312 товарів ✅
        (2420454, 'bottoms',   'smart_casual',  'F', ['spring', 'summer'],                     'WOMAN Спідниці'),          # 211 товарів ✅
        (2419172, 'footwear',  'casual',        'F', ['summer'],                               'WOMAN Босоніжки'),         # 119 товарів ✅
        (2419053, 'footwear',  'casual',        'F', ['summer'],                               'WOMAN Шльопанці/Тапки'),   # 43 товари  ✅
        (2419090, 'footwear',  'casual',        'F', ['summer'],                               'WOMAN Сандалі'),           # 60 товарів ✅
        (2418955, 'onepiece',  'casual',        'F', ['summer'],                               'WOMAN Купальники/Бікіні'), # 18 товарів ✅
        (2418962, 'onepiece',  'casual',        'F', ['summer'],                               'WOMAN Бікіні верх'),       # 24 товари  ✅
        (2420340, 'tops',      'smart_casual',  'F', ['spring', 'summer'],                     'WOMAN Сорочки/Блузи'),     # 223 товари ✅

        # ── ВЕСНА / ОСІНЬ ───────────────────────────────────────────────
        (2419235, 'bottoms',   'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Джинси'),            # 219 товарів ✅
        (2419270, 'bottoms',   'smart_casual',  'F', ['spring', 'autumn', 'winter'],           'WOMAN Штани'),             # 553 товари  ✅
        (2420942, 'layering',  'business',      'F', ['spring', 'autumn'],                     'WOMAN Блейзери'),          # 112 товарів ✅
        (2419756, 'layering',  'business',      'F', ['spring', 'autumn'],                     'WOMAN Костюми'),           # 47 товарів  ✅
        (2419844, 'layering',  'casual',        'F', ['spring', 'autumn', 'winter'],           'WOMAN Светри/Кардигани'),  # 442 товари  ✅
        (2419849, 'layering',  'casual',        'F', ['spring', 'autumn'],                     'WOMAN Худі/Толстовки'),    # 23 товари   ✅
        (2420325, 'layering',  'casual',        'F', ['spring', 'autumn'],                     'WOMAN Кардигани'),         # 72 товари   ✅
        (2420945, 'onepiece',  'cocktail',      'F', ['spring', 'autumn'],                     'WOMAN Сукні (демісезон)'), # 76 товарів  ✅
        (2419075, 'footwear',  'casual',        'F', ['spring', 'summer', 'autumn'],           'WOMAN Кросівки'),          # 72 товари   ✅
        (2419076, 'footwear',  'casual',        'F', ['spring', 'summer', 'autumn'],           'WOMAN Балетки'),           # 284 товари  ✅
        (2419175, 'footwear',  'smart_casual',  'F', ['spring', 'autumn'],                     'WOMAN Черевики'),          # 107 товарів ✅
        (2419176, 'footwear',  'formal',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Туфлі'),             # 16 товарів  ✅
        (2419023, 'layering',  'smart_casual',  'F', ['spring', 'autumn'],                     'WOMAN Жилети'),            # 28 товарів  ✅
        (2420282, 'onepiece',  'business',      'F', ['spring', 'autumn'],                     'WOMAN Ділові костюми'),    # 61 товар    ✅

        # ── ЗИМА ────────────────────────────────────────────────────────
        (2419032, 'outerwear', 'smart_casual',  'F', ['autumn', 'winter'],                     'WOMAN Тренчі/Пальта'),     # 185 товарів ✅
        (2417773, 'outerwear', 'casual',        'F', ['autumn', 'winter'],                     'WOMAN Куртки'),            # 291 товар   ✅
        (2417766, 'outerwear', 'casual',        'F', ['winter'],                               'WOMAN Хутряні куртки'),    # 8 товарів   ✅
        (2419045, 'outerwear', 'casual',        'F', ['winter'],                               'WOMAN Стьобані куртки'),   # 48 товарів  ✅
        (2419001, 'outerwear', 'casual',        'F', ['winter'],                               'WOMAN Пуховики'),          # 28 товарів  ✅
        (2419016, 'outerwear', 'smart_casual',  'F', ['autumn', 'winter'],                     'WOMAN Пальта вовняні'),    # 100 товарів ✅
        (2419024, 'outerwear', 'smart_casual',  'F', ['autumn', 'winter'],                     'WOMAN Шкіряні пальта'),    # 126 товарів ✅
        (2420321, 'layering',  'casual',        'F', ['autumn', 'winter'],                     'WOMAN Трикотаж/Светри'),   # 416 товарів ✅
        (2419160, 'footwear',  'smart_casual',  'F', ['autumn', 'winter'],                     'WOMAN Чоботи'),            # перевірений ✅
        (2419166, 'footwear',  'casual',        'F', ['autumn', 'winter'],                     'WOMAN Ковбойські чоботи'), # 54 товари   ✅
        (2419061, 'footwear',  'casual',        'F', ['autumn', 'winter'],                     'WOMAN Зимові черевики'),   # 39 товарів  ✅
        (2419057, 'footwear',  'casual',        'F', ['winter'],                               'WOMAN Зимові чоботи хутро'),# 1 товар    ✅

        # ── АКСЕСУАРИ (цілий рік) ───────────────────────────────────────
        (2418989, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Аксесуари'),         # перевірений ✅
        (2418963, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Прикраси'),          # перевірений ✅
        (2418964, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Сережки'),           # 17 товарів  ✅
        (2418966, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Ремені'),            # перевірений ✅
        (2418991, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Шарфи/Хустки'),      # 84 товари   ✅
        (2418968, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Головні убори'),     # 40 товарів  ✅
        (2418971, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Шкарпетки'),         # 20 товарів  ✅
        (2418980, 'accessory', 'casual',        'F', ['spring', 'summer'],                     'WOMAN Окуляри'),           # 2 товари    ✅
        (2418995, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Браслети'),          # 14 товарів  ✅
        (2417726, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Сумки'),             # 160 товарів ✅
        (2417728, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Шопери'),            # 242 товари  ✅
        (2418994, 'accessory', 'casual',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Клатчі'),            # 8 товарів   ✅
    ]

    LIMIT_PER_CATEGORY = 10

    def run(self):
        total_saved = 0
        failed = []

        for category_id, category, formality, gender, seasons, label in self.CATEGORY_MAP:
            print(f'\n[Zara] ── {label} ({", ".join(seasons)}) ──')
            saved = self._scrape_category(category_id, category, formality, gender, seasons)
            total_saved += saved
            if saved == 0:
                failed.append((category_id, label))

        print(f'\n[Zara] ✅ Всього збережено: {total_saved} товарів')

        if failed:
            print(f'\n[Zara] ⚠️  Категорії без товарів ({len(failed)}):')
            for cid, lbl in failed:
                print(f'   • [{cid}] {lbl}')

    def _scrape_category(self, category_id, category, formality, gender, seasons, retries=2):
        url = f'{self.base_url}/ua/uk/category/{category_id}/products?ajax=true'
        print(f'[Zara] → {url}')

        for attempt in range(1, retries + 2):
            try:
                r = requests.get(url, headers=self.HEADERS, timeout=20)
                break
            except requests.exceptions.Timeout:
                print(f'[Zara] ⏱ Timeout (спроба {attempt}/{retries + 1})')
                if attempt <= retries:
                    time.sleep(3 * attempt)
                else:
                    print(f'[Zara] ❌ Пропускаємо після {retries + 1} спроб')
                    return 0
            except Exception as e:
                print(f'[Zara] ❌ Помилка: {e}')
                return 0

        if r.status_code != 200:
            print(f'[Zara] Статус {r.status_code}')
            return 0

        try:
            data = r.json()
        except Exception:
            print(f'[Zara] Не JSON: {r.text[:200]}')
            return 0

        products = []
        for group in data.get('productGroups', []):
            for el in group.get('elements', []):
                for item in el.get('commercialComponents', []):
                    products.append(item)

        count = len(products)
        take  = min(count, self.LIMIT_PER_CATEGORY)
        print(f'[Zara] Знайдено: {count}, беремо: {take}')

        if not products:
            print(f'[Zara] Ключі відповіді: {list(data.keys())}')
            return 0

        products = products[:self.LIMIT_PER_CATEGORY]

        saved = 0
        for item in products:
            name = item.get('name', '') or item.get('description', '')
            if not name or len(name) < 3:
                continue

            pid  = item.get('id', '')
            seo  = item.get('seo', {})
            slug = seo.get('keyword', '') if isinstance(seo, dict) else ''
            source_url = (
                f'{self.base_url}/ua/uk/{slug}-p{pid}.html' if slug
                else f'{self.base_url}/ua/uk/p{pid}.html'
            )
            source_url = source_url[:255]

            price = None
            for price_key in ['price', 'maxPrice', 'minPrice', 'originalPrice']:
                v = item.get(price_key)
                if v:
                    price = v / 100 if isinstance(v, int) and v > 10000 else v
                    break

            image_url = ''
            try:
                colors = item.get('detail', {}).get('colors', [])
                if colors:
                    xmedia_list = colors[0].get('xmedia', [])
                    if xmedia_list:
                        image_url = xmedia_list[0].get('extraInfo', {}).get('deliveryUrl', '')
            except Exception:
                pass
            image_url = image_url[:500]

            color = ''
            try:
                colors = item.get('detail', {}).get('colors', [])
                if colors:
                    color = colors[0].get('name', '')[:100]
            except Exception:
                pass

            self.save_item({
                'name':       name[:255],
                'source_url': source_url,
                'category':   category,
                'formality':  formality,
                'price':      price,
                'currency':   'UAH',
                'image_url':  image_url,
                'color':      color,
                'material':   '',
                'pattern':    'solid',
                'gender':     gender,
                'seasons':    seasons,
            }, [])
            saved += 1

        print(f'[Zara] categoryId={category_id}: {saved} збережено')
        time.sleep(1)
        return saved