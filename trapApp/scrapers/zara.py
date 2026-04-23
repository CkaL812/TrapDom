import time
import requests
from django.utils import timezone
from trapApp.scrapers.base import BaseScraper


class ZaraScraper(BaseScraper):
    """
    Zara-скрепер з 3 сезонними капсулами (літо / весна-осінь / зима)
    та конкретним списком типів одягу для кожної капсули.

    Ціль: 200 товарів = 100 MAN + 100 WOMAN.
    Розподіл по сезонах на стать: 30 літо / 45 весна-осінь / 25 зима.

    Якщо в якомусь типі одягу немає категорії (напр. чол. кардигани),
    недобір переливається в інші типи ТОГО Ж СЕЗОНУ тієї ж статі
    (механізм "добору").
    """

    brand_name = 'Zara'
    base_url   = 'https://www.zara.com'

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'uk-UA,uk;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.zara.com/ua/uk/',
    }

    # ────────────────────────────────────────────────────────────────
    #  МЕТА-ІНФО ПРО КАТЕГОРІЇ
    #  cat_id -> (category, subcategory, formality, gender, seasons, label)
    # ────────────────────────────────────────────────────────────────
    CATEGORY_META = {
        # ══════════ MAN ══════════
        2436585: ('tops',      't_shirt',         'smart_casual',    'M', ['spring', 'summer'],                     'MAN Футболки'),
        2436584: ('bottoms',   'shorts',          'smart_casual',    'M', ['summer'],                               'MAN Шорти'),
        2436949: ('tops',      'shirt',           'smart_casual',    'M', ['spring', 'summer'],                     'MAN Сорочки'),
        2436336: ('footwear',  'sneakers',        'smart_casual',    'M', ['spring', 'summer', 'autumn'],           'MAN Кросівки'),
        2436385: ('footwear',  'sandals',         'smart_casual',    'M', ['summer'],                               'MAN Сандалі/Тапки'),
        2436386: ('footwear',  'flip_flops',      'smart_casual',    'M', ['summer'],                               'MAN Шльопанці'),
        2473840: ('bottoms',   'trousers',        'smart_casual',    'M', ['spring', 'summer', 'autumn', 'winter'], 'MAN Штани'),
        2436311: ('layering',  'blazer',          'business_casual', 'M', ['spring', 'autumn'],                     'MAN Блейзери'),
        2436384: ('footwear',  'loafers',         'business_formal', 'M', ['spring', 'autumn', 'winter'],           'MAN Офіційне взуття/Лофери'),
        2436388: ('footwear',  'boots',           'smart_casual',    'M', ['spring', 'autumn'],                     'MAN Черевики'),
        2436389: ('footwear',  'boots',           'smart_casual',    'M', ['spring', 'autumn', 'winter'],           'MAN Чоботи'),
        2606109: ('outerwear', 'coat',            'smart_casual',    'M', ['autumn', 'winter'],                     'MAN Пальта/Тренчі'),
        2436444: ('accessory', 'other_accessory', 'smart_casual',    'M', ['spring', 'summer', 'autumn', 'winter'], 'MAN Аксесуари'),
        2436434: ('accessory', 'belt',            'smart_casual',    'M', ['spring', 'summer', 'autumn', 'winter'], 'MAN Ремені'),
        2436436: ('accessory', 'tie',             'business_formal', 'M', ['autumn', 'winter'],                     'MAN Краватки'),

        # ══════════ WOMAN ══════════
        2420386: ('tops',      't_shirt',         'smart_casual',    'F', ['spring', 'summer'],                     'WOMAN Футболки'),
        2419892: ('tops',      'tank_top',        'smart_casual',    'F', ['spring', 'summer'],                     'WOMAN Топи'),
        2420896: ('onepiece',  'sundress',        'cocktail',        'F', ['spring', 'summer'],                     'WOMAN Сукні (літо)'),
        2420454: ('bottoms',   'skirt',           'smart_casual',    'F', ['spring', 'summer'],                     'WOMAN Спідниці'),
        2419172: ('footwear',  'sandals',         'smart_casual',    'F', ['summer'],                               'WOMAN Босоніжки'),
        2419053: ('footwear',  'flip_flops',      'smart_casual',    'F', ['summer'],                               'WOMAN Шльопанці/Тапки'),
        2419090: ('footwear',  'sandals',         'smart_casual',    'F', ['summer'],                               'WOMAN Сандалі'),
        2418955: ('onepiece',  'swimsuit',        'smart_casual',    'F', ['summer'],                               'WOMAN Купальники/Бікіні'),
        2418962: ('onepiece',  'bikini',          'smart_casual',    'F', ['summer'],                               'WOMAN Бікіні верх'),
        2420340: ('tops',      'blouse',          'smart_casual',    'F', ['spring', 'summer'],                     'WOMAN Сорочки/Блузи'),
        2419235: ('bottoms',   'jeans',           'smart_casual',    'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Джинси'),
        2419270: ('bottoms',   'trousers',        'smart_casual',    'F', ['spring', 'autumn', 'winter'],           'WOMAN Штани'),
        2420942: ('layering',  'blazer',          'business_casual', 'F', ['spring', 'autumn'],                     'WOMAN Блейзери'),
        2419756: ('layering',  'suit_set',        'business_formal', 'F', ['spring', 'autumn'],                     'WOMAN Костюми'),
        2419844: ('layering',  'sweater',         'smart_casual',    'F', ['spring', 'autumn', 'winter'],           'WOMAN Светри/Кардигани'),
        2419849: ('layering',  'hoodie',          'smart_casual',    'F', ['spring', 'autumn', 'winter'],           'WOMAN Худі/Толстовки'),
        2420325: ('layering',  'cardigan',        'smart_casual',    'F', ['spring', 'autumn'],                     'WOMAN Кардигани'),
        2420945: ('onepiece',  'dress',           'cocktail',        'F', ['spring', 'autumn'],                     'WOMAN Сукні (демісезон)'),
        2419075: ('footwear',  'sneakers',        'smart_casual',    'F', ['spring', 'summer', 'autumn'],           'WOMAN Кросівки'),
        2419076: ('footwear',  'flats',           'smart_casual',    'F', ['spring', 'summer', 'autumn'],           'WOMAN Балетки'),
        2419175: ('footwear',  'boots',           'smart_casual',    'F', ['spring', 'autumn'],                     'WOMAN Черевики'),
        2419176: ('footwear',  'heels',           'cocktail',        'F', ['spring', 'summer', 'autumn', 'winter'], 'WOMAN Туфлі'),
        2420282: ('onepiece',  'jumpsuit',        'business_formal', 'F', ['spring', 'autumn'],                     'WOMAN Ділові костюми'),
        2419032: ('outerwear', 'trench',          'smart_casual',    'F', ['autumn', 'winter'],                     'WOMAN Тренчі/Пальта'),
        2417773: ('outerwear', 'leather_jacket',  'smart_casual',    'F', ['autumn', 'winter'],                     'WOMAN Куртки'),
        2419045: ('outerwear', 'quilted_jacket',  'smart_casual',    'F', ['winter'],                               'WOMAN Стьобані куртки'),
        2419001: ('outerwear', 'puffer',          'smart_casual',    'F', ['winter'],                               'WOMAN Пуховики'),
        2419016: ('outerwear', 'wool_coat',       'smart_casual',    'F', ['autumn', 'winter'],                     'WOMAN Пальта вовняні'),
        2419024: ('outerwear', 'leather_jacket',  'smart_casual',    'F', ['autumn', 'winter'],                     'WOMAN Шкіряні пальта'),
        2420321: ('layering',  'sweater',         'smart_casual',    'F', ['autumn', 'winter'],                     'WOMAN Трикотаж/Светри'),
        2419160: ('footwear',  'boots',           'smart_casual',    'F', ['autumn', 'winter'],                     'WOMAN Чоботи'),
        2419166: ('footwear',  'cowboy_boots',    'smart_casual',    'F', ['autumn', 'winter'],                     'WOMAN Ковбойські чоботи'),
        2419061: ('footwear',  'winter_boots',    'smart_casual',    'F', ['autumn', 'winter'],                     'WOMAN Зимові черевики'),
        2419057: ('footwear',  'winter_boots',    'smart_casual',    'F', ['winter'],                               'WOMAN Зимові чоботи хутро'),
    }

    # ────────────────────────────────────────────────────────────────
    #  ПЛАН: (gender, capsule) -> [(type_label, target, [cat_ids]), ...]
    # ────────────────────────────────────────────────────────────────
    PLAN = {
        # ═══════════════ MAN ═══════════════
        ('M', 'summer'): [
            ('Футболки',          8, [2436585]),
            ('Шорти',             6, [2436584]),
            ('Лляні штани',       5, [2473840]),
            ('Сандалі/Шльопанці', 6, [2436385, 2436386]),
            ('Легкі сорочки',     5, [2436949]),
        ],  # 30

        ('M', 'spring_autumn'): [
            ('Тренчі/Пальта',     6, [2606109]),
            ('Блейзери',          8, [2436311]),
            ('Штани',             6, [2473840]),
            ('Лофери',            6, [2436384]),
            ('Черевики/Чоботи',   8, [2436388, 2436389]),
            ('Кросівки',          6, [2436336]),
            ('Аксесуари/Ремені',  5, [2436444, 2436434]),
        ],  # 45

        ('M', 'winter'): [
            ('Пальта/Тренчі',     10, [2606109]),
            ('Офіційне взуття',   5,  [2436384]),
            ('Штани',             4,  [2473840]),
            ('Аксесуари',         6,  [2436436, 2436434, 2436444]),
        ],  # 25

        # ═══════════════ WOMAN ═══════════════
        ('F', 'summer'): [
            ('Футболки/Топи',     6, [2420386, 2419892]),
            ('Сорочки/Блузи',     4, [2420340]),
            ('Сукні (сарафани)',  5, [2420896]),
            ('Лляні штани',       3, [2419270]),
            ('Спідниці',          3, [2420454]),
            ('Сандалі/Босоніжки', 6, [2419090, 2419172, 2419053]),
            ('Купальники',        3, [2418955, 2418962]),
        ],  # 30

        ('F', 'spring_autumn'): [
            ('Тренчі/Пальта',          6, [2419032]),
            ('Шкіряні пальта/куртки',  5, [2419024, 2417773]),
            ('Блейзери/Костюми',       7, [2420942, 2419756, 2420282]),
            ('Кардигани',              6, [2420325, 2419844]),
            ('Балетки/Туфлі',          5, [2419076, 2419176]),
            ('Черевики/Чоботи',        6, [2419175, 2419160]),
            ('Штани/Джинси',           5, [2419270, 2419235]),
            ('Сукні (демісезон)',      5, [2420945]),
        ],  # 45

        ('F', 'winter'): [
            ('Пуховики/Стьобані',         6, [2419001, 2419045]),
            ('Пальта вовняні/шкіряні',    6, [2419016, 2419024]),
            ('Худі/Толстовки',            3, [2419849]),
            ('Трикотаж/Светри',           5, [2420321, 2419844]),
            ('Зимове взуття',             5, [2419061, 2419057, 2419160, 2419166]),
        ],  # 25
    }

    MAX_PER_CATEGORY_DEFAULT = 5
    # Для вузьких категорій, де мало виборів — дозволяємо більше
    MAX_PER_CATEGORY_OVERRIDES = {
        2606109: 10,  # MAN Пальта/Тренчі — єдиний зимовий верхній одяг у чоловіків
    }

    GENDER_TARGET = 100

    CAPSULE_TO_SEASONS = {
        'summer':        ['summer'],
        'spring_autumn': ['spring', 'autumn'],
        'winter':        ['winter'],
    }

    # ────────────────────────────────────────────────────────────────
    #  ГОЛОВНИЙ ЦИКЛ
    # ────────────────────────────────────────────────────────────────
    def run(self):
        fetch_cache = {}    # cat_id -> list[product_dicts]
        saved_ids   = set() # id вже збережених товарів (для анти-дубля при доборі)
        report      = []
        saved_by_gender = {'M': 0, 'F': 0}

        capsule_order = ['summer', 'spring_autumn', 'winter']

        for gender in ['M', 'F']:
            print(f'\n{"═"*60}\n  🚹🚺 СТАТЬ: {gender}  (ціль: {self.GENDER_TARGET})\n{"═"*60}')

            for capsule in capsule_order:
                plan_items = self.PLAN.get((gender, capsule), [])
                if not plan_items:
                    continue

                capsule_plan_total = sum(t[1] for t in plan_items)
                print(f'\n  ── {capsule.upper()} (план: {capsule_plan_total}) ──')

                capsule_debt   = 0
                capsule_saved  = 0
                capsule_report = []

                for type_label, target, cat_ids in plan_items:
                    got = self._fill_type(
                        type_label, target, cat_ids, capsule, gender,
                        fetch_cache, saved_ids,
                    )
                    capsule_saved += got
                    capsule_report.append((type_label, target, got))
                    if got < target:
                        capsule_debt += (target - got)

                # Добір недостачі з інших типів цієї ж капсули
                if capsule_debt > 0:
                    print(f'\n     🔄 Добір: потрібно ще {capsule_debt} товарів з інших типів капсули')
                    extra = self._fill_debt(
                        capsule_debt, plan_items, capsule, gender,
                        fetch_cache, saved_ids,
                    )
                    capsule_saved += extra
                    capsule_report.append(('↳ ДОБІР', capsule_debt, extra))

                saved_by_gender[gender] += capsule_saved
                report.append((gender, capsule, capsule_plan_total, capsule_saved, capsule_report))

        self._print_report(report, saved_by_gender)

    # ────────────────────────────────────────────────────────────────
    #  ЗАПОВНЕННЯ ОДНОГО ТИПУ ОДЯГУ
    # ────────────────────────────────────────────────────────────────
    def _fill_type(self, type_label, target, cat_ids, capsule, gender,
                   fetch_cache, saved_ids):
        seasons_for_save = self.CAPSULE_TO_SEASONS[capsule]
        print(f'     ▸ [{capsule}/{type_label}] ціль={target}, категорій={len(cat_ids)}')

        pools = []
        for cid in cat_ids:
            if cid not in self.CATEGORY_META:
                continue
            meta = self.CATEGORY_META[cid]
            if meta[3] != gender:
                continue

            if cid not in fetch_cache:
                fetch_cache[cid] = self._fetch_category(cid, meta[5])
            products = fetch_cache[cid]
            if not products:
                continue

            max_take = self.MAX_PER_CATEGORY_OVERRIDES.get(
                cid, self.MAX_PER_CATEGORY_DEFAULT
            )
            pools.append({
                'cat_id':   cid,
                'meta':     meta,
                'products': list(products),   # копія, щоб .pop не чіпав кеш
                'taken':    0,
                'max':      max_take,
            })

        if not pools:
            print(f'       ⚠ немає доступних категорій')
            return 0

        saved_here = 0
        idx = 0
        while saved_here < target:
            active = [p for p in pools if p['taken'] < p['max'] and p['products']]
            if not active:
                break

            pool = pools[idx % len(pools)]
            idx += 1
            if pool['taken'] >= pool['max'] or not pool['products']:
                continue

            product = pool['products'].pop(0)
            pid = product.get('id')
            if pid and pid in saved_ids:
                continue   # уже збережений цей самий товар (може бути в іншій категорії)

            if self._save_product(product, pool['meta'], seasons_for_save):
                if pid:
                    saved_ids.add(pid)
                pool['taken'] += 1
                saved_here += 1

        mark = '✓' if saved_here >= target else ('⚠' if saved_here > 0 else '✗')
        print(f'       {mark} зібрано {saved_here}/{target}')
        return saved_here

    # ────────────────────────────────────────────────────────────────
    #  ДОБІР НЕДОСТАЧІ В МЕЖАХ КАПСУЛИ
    # ────────────────────────────────────────────────────────────────
    def _fill_debt(self, debt, plan_items, capsule, gender, fetch_cache, saved_ids):
        seasons_for_save = self.CAPSULE_TO_SEASONS[capsule]

        # Збираємо всі унікальні cat_id з капсули + додаємо сусідні "резервні" категорії
        # (наприклад, для зими M беремо і Кросівки/Черевики/Чоботи як добір)
        all_cat_ids = []
        seen = set()
        for _, _, cat_ids in plan_items:
            for cid in cat_ids:
                if cid not in seen:
                    seen.add(cid)
                    all_cat_ids.append(cid)

        # Додатковий резерв — всі категорії тієї ж статі, які не в плані, але
        # підходять за сезоном (це допомагає зимовим M, де план куций)
        capsule_real_seasons = self.CAPSULE_TO_SEASONS[capsule]
        for cid, meta in self.CATEGORY_META.items():
            if cid in seen:
                continue
            if meta[3] != gender:
                continue
            cat_seasons = meta[4]
            if any(s in cat_seasons for s in capsule_real_seasons):
                seen.add(cid)
                all_cat_ids.append(cid)

        pools = []
        for cid in all_cat_ids:
            meta = self.CATEGORY_META[cid]
            if cid not in fetch_cache:
                fetch_cache[cid] = self._fetch_category(cid, meta[5])
            products = fetch_cache[cid]
            if not products:
                continue
            pools.append({
                'cat_id':   cid,
                'meta':     meta,
                'products': list(products),
            })

        if not pools:
            print(f'        ⚠ немає товарів для добору')
            return 0

        saved = 0
        idx = 0
        while saved < debt:
            active = [p for p in pools if p['products']]
            if not active:
                break

            pool = pools[idx % len(pools)]
            idx += 1
            if not pool['products']:
                continue

            product = pool['products'].pop(0)
            pid = product.get('id')
            if pid and pid in saved_ids:
                continue

            if self._save_product(product, pool['meta'], seasons_for_save):
                if pid:
                    saved_ids.add(pid)
                saved += 1

        print(f'        ↳ добрано {saved}/{debt}')
        return saved

    # ────────────────────────────────────────────────────────────────
    #  ЗАВАНТАЖЕННЯ КАТЕГОРІЇ (з retry)
    # ────────────────────────────────────────────────────────────────
    def _fetch_category(self, category_id, label, retries=2):
        url = f'{self.base_url}/ua/uk/category/{category_id}/products?ajax=true'
        print(f'       → GET {label}')

        r = None
        for attempt in range(1, retries + 2):
            try:
                r = requests.get(url, headers=self.HEADERS, timeout=20)
                break
            except requests.exceptions.Timeout:
                print(f'       ⏱ Timeout (спроба {attempt}/{retries + 1})')
                if attempt <= retries:
                    time.sleep(3 * attempt)
                else:
                    return []
            except Exception as e:
                print(f'       ❌ Помилка: {e}')
                return []

        if r is None or r.status_code != 200:
            print(f'       Статус {r.status_code if r else "?"}')
            return []

        try:
            data = r.json()
        except Exception:
            return []

        products = []
        for group in data.get('productGroups', []):
            for el in group.get('elements', []):
                for item in el.get('commercialComponents', []):
                    products.append(item)

        time.sleep(0.5)
        return products

    # ────────────────────────────────────────────────────────────────
    #  ЗБЕРЕЖЕННЯ ТОВАРУ
    # ────────────────────────────────────────────────────────────────
    def _save_product(self, item, cat_meta, seasons_for_save):
        w_type, subcategory, formality, gender, _cat_seasons, label = cat_meta

        name = item.get('name', '') or item.get('description', '')
        if not name or len(name) < 3:
            return False

        pid  = item.get('id', '')
        seo  = item.get('seo', {})
        slug = seo.get('keyword', '') if isinstance(seo, dict) else ''
        source_url = (
            f'{self.base_url}/ua/uk/{slug}-p{pid}.html' if slug
            else f'{self.base_url}/ua/uk/p{pid}.html'
        )
        source_url = source_url[:255]

        price = None
        for key in ['price', 'maxPrice', 'minPrice', 'originalPrice']:
            v = item.get(key)
            if v:
                price = v / 100 if isinstance(v, int) and v > 10000 else v
                break

        image_url = ''
        color = ''
        try:
            colors = item.get('detail', {}).get('colors', [])
            if colors:
                xmedia_list = colors[0].get('xmedia', [])
                if xmedia_list:
                    image_url = xmedia_list[0].get('extraInfo', {}).get('deliveryUrl', '')
                color = colors[0].get('name', '')[:100]
        except Exception:
            pass
        image_url = image_url[:500]

        self.save_item({
            'name':        name[:255],
            'source_url':  source_url,
            'category':    w_type,
            'subcategory': subcategory,
            'formality':   formality,
            'price':       price,
            'currency':    'UAH',
            'image_url':   image_url,
            'color':       color,
            'material':    '',
            'pattern':     'solid',
            'gender':      gender,
            'seasons':     seasons_for_save,
            'tag_source':  'scraper',
            'tagged_at':   timezone.now(),
        }, [])
        return True

    # ────────────────────────────────────────────────────────────────
    #  ФІНАЛЬНИЙ ЗВІТ
    # ────────────────────────────────────────────────────────────────
    def _print_report(self, report, saved_by_gender):
        print(f'\n\n{"═"*60}\n  📊 ПІДСУМКОВИЙ ЗВІТ\n{"═"*60}')
        total = saved_by_gender['M'] + saved_by_gender['F']
        print(f'  Всього: {total} товарів')
        print(f'  • MAN:   {saved_by_gender["M"]}/{self.GENDER_TARGET}')
        print(f'  • WOMAN: {saved_by_gender["F"]}/{self.GENDER_TARGET}')

        print(f'\n  Розбивка по капсулах:')
        for gender, capsule, plan_total, got, items in report:
            print(f'\n  ── {gender} / {capsule.upper()} ({got}/{plan_total}) ──')
            for type_label, target, achieved in items:
                mark = '✓' if achieved >= target else ('⚠' if achieved > 0 else '✗')
                print(f'     {mark} {type_label:28s} {achieved}/{target}')