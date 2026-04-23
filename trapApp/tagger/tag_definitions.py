"""
Визначення для тагера:
  • CLIP-промпти для subcategory / style / formality
  • Правила (subcategory → time_of_day, age_ranges) для полів,
    які CLIP ненадійно визначає

Ці промпти на ENGLISH, бо CLIP тренувався англійською.
"""


# ══════════════════════════════════════════════════════════════════
#  CLIP-ПРОМПТИ: subcategory
#  Для ефективності звужуються до категорії товару (tops → тільки tops-підкатегорії)
# ══════════════════════════════════════════════════════════════════
SUBCATEGORY_PROMPTS = {
    # tops
    't_shirt':     'a photo of a t-shirt',
    'shirt':       'a photo of a button-up shirt',
    'blouse':      'a photo of a women\'s blouse',
    'polo':        'a photo of a polo shirt',
    'tank_top':    'a photo of a tank top or sleeveless shirt',
    'long_sleeve': 'a photo of a long sleeve top',
    'crop_top':    'a photo of a crop top',
    # layering
    'blazer':      'a photo of a blazer or suit jacket',
    'cardigan':    'a photo of an open-front cardigan',
    'sweater':     'a photo of a knit sweater or pullover',
    'hoodie':      'a photo of a hoodie with hood',
    'sweatshirt':  'a photo of a crew-neck sweatshirt',
    'vest':        'a photo of a sleeveless vest',
    'suit_set':    'a photo of a matching suit set',
    # bottoms
    'jeans':       'a photo of blue denim jeans',
    'trousers':    'a photo of dress trousers or pants',
    'linen_pants': 'a photo of loose linen pants',
    'shorts':      'a photo of shorts',
    'skirt':       'a photo of a skirt',
    'leggings':    'a photo of tight leggings',
    # onepiece
    'dress':       'a photo of a dress',
    'sundress':    'a photo of a light summer sundress',
    'jumpsuit':    'a photo of a jumpsuit or romper',
    'swimsuit':    'a photo of a one-piece swimsuit',
    'bikini':      'a photo of a bikini set',
    # outerwear
    'coat':            'a photo of a long coat',
    'wool_coat':       'a photo of a thick wool coat',
    'trench':          'a photo of a belted trench coat',
    'puffer':          'a photo of a puffy down-filled jacket',
    'quilted_jacket':  'a photo of a quilted jacket',
    'leather_jacket':  'a photo of a leather jacket',
    'denim_jacket':    'a photo of a denim jacket',
    'bomber':          'a photo of a bomber jacket',
    'parka':           'a photo of a parka with hood',
    'fur_coat':        'a photo of a fur coat',
    # footwear
    'sneakers':      'a photo of sneakers or athletic shoes',
    'boots':         'a photo of ankle boots',
    'winter_boots':  'a photo of warm winter boots',
    'cowboy_boots':  'a photo of western cowboy boots',
    'loafers':       'a photo of leather loafers',
    'oxford_shoes':  'a photo of oxford lace-up dress shoes',
    'heels':         'a photo of high heel shoes',
    'flats':         'a photo of flat ballet shoes',
    'sandals':       'a photo of open sandals',
    'flip_flops':    'a photo of flip flops',
    # accessory
    'belt':        'a photo of a belt',
    'tie':         'a photo of a necktie',
    'scarf':       'a photo of a scarf',
    'hat':         'a photo of a hat',
    'sunglasses':  'a photo of sunglasses',
    'jewelry':     'a photo of jewelry',
    'earrings':    'a photo of earrings',
    'bracelet':    'a photo of a bracelet',
    'bag':         'a photo of a handbag',
    'tote':        'a photo of a tote shopping bag',
    'clutch':      'a photo of a small clutch bag',
    'socks':       'a photo of socks',
    'other_accessory': 'a photo of a fashion accessory',
}


# ══════════════════════════════════════════════════════════════════
#  CLIP-ПРОМПТИ: style
# ══════════════════════════════════════════════════════════════════
STYLE_PROMPTS = {
    'minimalism':    'minimalist clean neutral clothing, simple and understated',
    'old_money':     'old money aesthetic, quiet luxury, preppy classic elegance',
    'streetwear':    'urban streetwear, oversized hip-hop style clothing',
    'gorpcore':      'gorpcore outdoor technical hiking gear aesthetic',
    'grunge':        'grunge 90s rock aesthetic, distressed edgy clothing',
    'cyberpunk':     'techwear cyberpunk futuristic black utility clothing',
    'vintage':       'vintage retro 70s 80s clothing',
    'dark_academia': 'dark academia aesthetic, tweed wool vintage scholarly clothing',
    'avant_garde':   'avant-garde experimental deconstructed fashion',
    'workwear':      'rugged workwear heavy duty utility clothing',
}


# ══════════════════════════════════════════════════════════════════
#  CLIP-ПРОМПТИ: formality (дрес-код)
# ══════════════════════════════════════════════════════════════════
FORMALITY_PROMPTS = {
    'white_tie':          'ultra formal white tie evening wear, tailcoat',
    'black_tie':          'black tie formal tuxedo or floor-length gown',
    'black_tie_creative': 'creative black tie, artistic formal evening wear',
    'business_formal':    'formal business suit, professional office attire',
    'business_casual':    'business casual office clothing, smart but relaxed',
    'smart_casual':       'smart casual outfit, neat but not formal',
    'cocktail':           'cocktail party dress, elegant knee-length',
    'after_five':         'semi-formal evening wear for after-five events',
    'festival_chic':      'festival chic bohemian outfit for outdoor events',
    'semi_formal':        'semi-formal evening or daytime attire',
}


# ══════════════════════════════════════════════════════════════════
#  ПРАВИЛА: subcategory → time_of_day
#  (визначаються детерміновано, без CLIP)
# ══════════════════════════════════════════════════════════════════
TIME_OF_DAY_RULES = {
    # верх
    't_shirt':     ['day', 'evening'],
    'shirt':       ['morning', 'day', 'evening'],
    'blouse':      ['day', 'evening'],
    'polo':        ['morning', 'day'],
    'tank_top':    ['day'],
    'long_sleeve': ['morning', 'day', 'evening'],
    'crop_top':    ['evening', 'night'],
    # шари
    'blazer':     ['morning', 'day', 'evening'],
    'cardigan':   ['morning', 'day', 'evening'],
    'sweater':    ['morning', 'day', 'evening'],
    'hoodie':     ['day', 'evening'],
    'sweatshirt': ['morning', 'day'],
    'vest':       ['day', 'evening'],
    'suit_set':   ['morning', 'day', 'evening'],
    # низ
    'jeans':       ['morning', 'day', 'evening'],
    'trousers':    ['morning', 'day', 'evening'],
    'linen_pants': ['day'],
    'shorts':      ['day'],
    'skirt':       ['day', 'evening'],
    'leggings':    ['morning', 'day'],
    # суцільний
    'dress':    ['day', 'evening', 'night'],
    'sundress': ['day'],
    'jumpsuit': ['day', 'evening'],
    'swimsuit': ['day'],
    'bikini':   ['day'],
    # верхній одяг
    'coat':           ['morning', 'day', 'evening'],
    'wool_coat':      ['morning', 'day', 'evening'],
    'trench':         ['morning', 'day', 'evening'],
    'puffer':         ['morning', 'day', 'evening'],
    'quilted_jacket': ['morning', 'day', 'evening'],
    'leather_jacket': ['evening', 'night'],
    'denim_jacket':   ['day', 'evening'],
    'bomber':         ['day', 'evening'],
    'parka':          ['morning', 'day'],
    'fur_coat':       ['evening', 'night'],
    # взуття
    'sneakers':     ['morning', 'day', 'evening'],
    'boots':        ['morning', 'day', 'evening'],
    'winter_boots': ['morning', 'day', 'evening'],
    'cowboy_boots': ['day', 'evening'],
    'loafers':      ['morning', 'day', 'evening'],
    'oxford_shoes': ['morning', 'day', 'evening', 'night'],
    'heels':        ['evening', 'night'],
    'flats':        ['day', 'evening'],
    'sandals':      ['day'],
    'flip_flops':   ['day'],
    # аксесуари
    'belt':       ['morning', 'day', 'evening'],
    'tie':        ['morning', 'day', 'evening'],
    'scarf':      ['morning', 'day', 'evening'],
    'hat':        ['morning', 'day'],
    'sunglasses': ['day'],
    'jewelry':    ['day', 'evening', 'night'],
    'earrings':   ['day', 'evening', 'night'],
    'bracelet':   ['day', 'evening', 'night'],
    'bag':        ['morning', 'day', 'evening'],
    'tote':       ['morning', 'day'],
    'clutch':     ['evening', 'night'],
    'socks':      ['morning', 'day', 'evening'],
    'other_accessory': ['morning', 'day', 'evening'],
}


# ══════════════════════════════════════════════════════════════════
#  ПРАВИЛА: (style, formality) → age_ranges
#  Вікові діапазони залежать від комбінації стилю й формальності
# ══════════════════════════════════════════════════════════════════

# Базовий діапазон для стилю (коли немає даних про formality)
STYLE_AGE_BASE = {
    'minimalism':    ['25-34', '35-44', '45-54'],
    'old_money':     ['25-34', '35-44', '45-54', '55+'],
    'streetwear':    ['13-17', '18-24', '25-34'],
    'gorpcore':      ['18-24', '25-34', '35-44'],
    'grunge':        ['18-24', '25-34'],
    'cyberpunk':     ['18-24', '25-34'],
    'vintage':       ['18-24', '25-34', '35-44'],
    'dark_academia': ['18-24', '25-34', '35-44'],
    'avant_garde':   ['25-34', '35-44'],
    'workwear':      ['25-34', '35-44', '45-54'],
}

# Коригування за formality (зсув догори/додолу)
FORMALITY_AGE_SHIFT = {
    'white_tie':          ['35-44', '45-54', '55+'],
    'black_tie':          ['25-34', '35-44', '45-54', '55+'],
    'black_tie_creative': ['25-34', '35-44'],
    'business_formal':    ['25-34', '35-44', '45-54', '55+'],
    'business_casual':    ['25-34', '35-44', '45-54'],
    'smart_casual':       ['18-24', '25-34', '35-44'],
    'cocktail':           ['25-34', '35-44', '45-54'],
    'after_five':         ['25-34', '35-44'],
    'festival_chic':      ['13-17', '18-24', '25-34'],
    'semi_formal':        ['25-34', '35-44', '45-54'],
}

# Дефолтний діапазон, якщо нема стилю і формальності
DEFAULT_AGE_RANGES = ['18-24', '25-34', '35-44']


def compute_age_ranges(styles, formality):
    """
    Повертає віковий діапазон на основі стилів і дрес-коду.
    Беремо перетин множин (якщо можливо), інакше об'єднання.
    """
    sets = []

    if styles:
        for s in styles:
            if s in STYLE_AGE_BASE:
                sets.append(set(STYLE_AGE_BASE[s]))

    if formality and formality in FORMALITY_AGE_SHIFT:
        sets.append(set(FORMALITY_AGE_SHIFT[formality]))

    if not sets:
        return list(DEFAULT_AGE_RANGES)

    # Пробуємо перетин (більш точно)
    intersection = sets[0]
    for s in sets[1:]:
        intersection = intersection & s

    if intersection:
        result = sorted(intersection)
    else:
        # Перетину немає — беремо об'єднання
        union = set()
        for s in sets:
            union |= s
        result = sorted(union)

    # Сортуємо за логічним порядком вікових діапазонів
    order = ['13-17', '18-24', '25-34', '35-44', '45-54', '55+']
    return [r for r in order if r in result]


def compute_time_of_day(subcategory):
    """Повертає список часів доби для підкатегорії."""
    return list(TIME_OF_DAY_RULES.get(subcategory, ['morning', 'day', 'evening']))