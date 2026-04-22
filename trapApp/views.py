import re
import json
import logging
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ClothingItem, Event, CustomUser, Brand
from .forms import RegisterForm, LoginForm, ProfileForm
from .cart import Cart
logger = logging.getLogger(__name__)


def index(request):
    brands = Brand.objects.all().order_by('name')
    return render(request, 'trapApp/index.html', {'brands': brands})


@login_required(login_url='/login/')
def outfit_picker(request):
    return render(request, 'trapApp/outfit_picker.html')


def outfit_results(request):
    result = request.session.get('outfit_result')
    if not result:
        return redirect('outfit_picker')

    items_data = result.get('items', [])
    ids        = [item['id'] for item in items_data]
    reason_map = {item['id']: item.get('reason', '') for item in items_data}

    items_qs = ClothingItem.objects.filter(id__in=ids).select_related('brand')
    for item in items_qs:
        item.reason = reason_map.get(item.id, '')

    items_ordered = sorted(items_qs, key=lambda x: ids.index(x.id))

    category_labels = dict(ClothingItem.CATEGORY_CHOICES)
    cat_counts = {}
    for item in items_ordered:
        cat_counts[item.category] = cat_counts.get(item.category, 0) + 1

    categories = [
        {'key': k, 'label': category_labels.get(k, k), 'count': v}
        for k, v in cat_counts.items()
    ]

    context = {
        'items':           items_ordered,
        'categories':      categories,
        'outfit_name':     result.get('outfit_name', 'Підібраний образ'),
        'stylist_comment': result.get('stylist_comment', ''),
        'event_name':      result.get('event_name', ''),
        'gender':          result.get('gender', ''),
        'season':          result.get('season', ''),
    }
    return render(request, 'trapApp/outfit_results.html', context)


# ─── Мапи ─────────────────────────────────────────────────────────────────────

FORMALITY_MAP = {
    'casual':       ['casual'],
    'smart_casual': ['casual', 'smart_casual'],
    'business':     ['smart_casual', 'business'],
    'cocktail':     ['smart_casual', 'business', 'cocktail'],
    'formal':       ['business', 'cocktail', 'formal'],
    'black_tie':    ['cocktail', 'formal', 'black_tie'],
    'white_tie':    ['formal', 'black_tie'],
}

GENDER_MAP    = {'male': 'M', 'female': 'F', 'unisex': 'U'}
GENDER_LABELS = {'male': 'Чоловіча', 'female': 'Жіноча', 'unisex': 'Унісекс'}
SEASON_LABELS = {'spring': 'Весна', 'summer': 'Літо', 'autumn': 'Осінь', 'winter': 'Зима'}

ITEMS_PER_CATEGORY = 8  # збільшено з 5

MODELS_TO_TRY = [
    
    "nvidia/nemotron-3-super-120b-a12b:free",
    
]


def _build_catalog(gender: str, season: str, formality_levels: list) -> list:
    gender_db = GENDER_MAP.get(gender, 'U')
    result = []
    all_categories = [c[0] for c in ClothingItem.CATEGORY_CHOICES]

    for category in all_categories:
        qs = ClothingItem.objects.select_related('brand').filter(
            category=category,
            gender__in=[gender_db, 'U'],
        ).order_by('?')  # рандомізація — кожен запит дає різні речі
        if season:
            qs = qs.filter(seasons__name=season)
        if formality_levels:
            qs = qs.filter(formality__in=formality_levels)
        result.extend(list(qs[:ITEMS_PER_CATEGORY]))

    return result


def _format_catalog(items: list) -> str:
    lines = []
    for item in items:
        lines.append(
            f"ID:{item.id}|{item.brand.name} {item.name}|"
            f"cat:{item.category}|form:{item.formality}|"
            f"color:{item.color or 'n/a'}|pat:{item.pattern}"
        )
    return "\n".join(lines)


def _parse_llm_json(raw: str) -> dict:
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                raw = part
                break

    start = raw.find('{')
    end   = raw.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("JSON об'єкт не знайдено у відповіді")
    raw = raw[start:end+1]

    raw = re.sub(r'//[^\n]*', '', raw)
    raw = re.sub(r',\s*}', '}', raw)
    raw = re.sub(r',\s*]', ']', raw)

    return json.loads(raw)


@csrf_exempt
@login_required(login_url='/login/')
def generate_outfit(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не підтримується'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Необхідна авторизація'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Невалідний запит'}, status=400)

    event  = data.get('event', '').strip()
    gender = data.get('gender', 'unisex')
    season = data.get('season', '')

    if not event:
        return JsonResponse({'status': 'error', 'message': 'Вкажіть подію'}, status=400)
    if not gender:
        return JsonResponse({'status': 'error', 'message': 'Вкажіть стать'}, status=400)
    if not season:
        return JsonResponse({'status': 'error', 'message': 'Вкажіть сезон'}, status=400)

    # ── DEBUG: перевірка ключа ────────────────────────────────
    api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
    if not api_key:
        logger.error("[OUTFIT] OPENROUTER_API_KEY відсутній у settings!")
        return JsonResponse(
            {'status': 'error', 'message': 'API ключ не налаштований. Зверніться до адміністратора.'},
            status=500
        )
    logger.error(f"[OUTFIT] API KEY знайдено: {api_key[:10]}...")
    # ─────────────────────────────────────────────────────────

    event_obj = Event.objects.filter(name__iexact=event).first()
    formality_levels = []
    if event_obj and event_obj.formality in FORMALITY_MAP:
        formality_levels = FORMALITY_MAP[event_obj.formality]

    items = _build_catalog(gender, season, formality_levels)
    if len(items) < 3:
        items = _build_catalog(gender, '', formality_levels)
    if len(items) < 3:
        items = _build_catalog(gender, '', [])

    if not items:
        return JsonResponse(
            {'status': 'error', 'message': 'У базі даних немає речей для підбору.'},
            status=404
        )

    items = items[:50]  # збільшено з 30
    catalog_text   = _format_catalog(items)
    available_cats = list({item.category for item in items})
    season_ua      = SEASON_LABELS.get(season, season)
    gender_ua      = GENDER_LABELS.get(gender, gender)

    system_prompt = (
        "Ти — професійний стиліст. Підбери образ із каталогу одягу.\n"
        "Поверни ТІЛЬКИ валідний JSON. Без markdown, без коментарів, без зайвого тексту.\n"
        'Формат: {"outfit_name":"...","stylist_comment":"...","items":[{"id":1,"reason":"..."}]}\n\n'
        "Правила:\n"
        "1. Використовуй ТІЛЬКИ ID з каталогу.\n"
        "2. Обери 3–5 речей з різних категорій.\n"
        "3. Tops + bottoms обов'язково (або onepiece).\n"
        "4. Footwear додай якщо є в каталозі.\n"
        "5. Стеж за гармонією кольорів.\n"
        "6. outfit_name — 3–5 слів українською.\n"
        "7. stylist_comment — 2 речення українською.\n"
        "8. reason — 1 речення українською для кожної речі.\n"
        "ВАЖЛИВО: JSON має бути повністю завершеним і валідним."
    )

    user_prompt = (
        f"Подія: {event}\n"
        f"Стать: {gender_ua}\n"
        f"Сезон: {season_ua}\n"
        f"Доступні категорії: {', '.join(available_cats)}\n\n"
        f"Каталог:\n{catalog_text}"
    )

    last_error  = None
    ai_response = None

    for model_id in MODELS_TO_TRY:
        logger.error(f"[OUTFIT] Спроба моделі: {model_id}")
        try:
            ai_response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type":  "application/json",
                    "HTTP-Referer":  "https://trapdom.com",
                    "X-Title":       "TrapDom Outfit Picker",
                },
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens":  2048,
                },
                timeout=30,
            )
            logger.error(f"[OUTFIT] Відповідь від {model_id}: status={ai_response.status_code}")
            logger.error(f"[OUTFIT] Тіло відповіді (перші 500 символів): {ai_response.text[:500]}")
            ai_response.raise_for_status()
            logger.error(f"[OUTFIT] Модель {model_id} — успішно!")
            break
        except requests.RequestException as e:
            last_error  = str(e)
            logger.error(f"[OUTFIT] Помилка моделі {model_id}: {last_error}")
            ai_response = None
            continue

    if ai_response is None or not ai_response.ok:
        logger.error(f"[OUTFIT] Всі моделі провалились. Остання помилка: {last_error}")
        return JsonResponse(
            {'status': 'error', 'message': 'AI сервіс недоступний. Спробуйте пізніше.'},
            status=502
        )

    try:
        raw = ai_response.json()["choices"][0]["message"]["content"].strip()
        logger.error(f"\n=== RAW LLM ===\n{raw}\n===============\n")

        llm_data       = _parse_llm_json(raw)
        selected_items = llm_data.get("items", [])

        if not selected_items:
            return JsonResponse(
                {'status': 'error', 'message': 'AI не повернув жодного елементу. Спробуйте ще раз.'},
                status=500
            )

    except (KeyError, IndexError) as e:
        logger.error(f"[OUTFIT] KeyError/IndexError при парсингу: {e}")
        return JsonResponse(
            {'status': 'error', 'message': 'Неочікувана відповідь від AI. Спробуйте ще раз.'},
            status=500
        )
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"[OUTFIT] JSON parse error: {e}")
        return JsonResponse(
            {'status': 'error', 'message': 'AI повернув некоректну відповідь. Спробуйте ще раз.'},
            status=500
        )

    selected_ids = [item['id'] for item in selected_items]
    reason_map   = {item['id']: item.get('reason', '') for item in selected_items}
    valid_items  = ClothingItem.objects.filter(id__in=selected_ids).select_related('brand')

    request.session['outfit_result'] = {
        'outfit_name':     llm_data.get('outfit_name', 'Підібраний образ'),
        'stylist_comment': llm_data.get('stylist_comment', ''),
        'event_name':      event,
        'gender':          gender_ua,
        'season':          season_ua,
        'items': [
            {'id': item.id, 'reason': reason_map.get(item.id, '')}
            for item in valid_items
        ],
    }
    request.session.modified = True

    return JsonResponse({'status': 'ok', 'redirect': '/outfit-results/'})


def product_detail(request, pk):
    item = get_object_or_404(ClothingItem.objects.select_related('brand').prefetch_related('sizes'), pk=pk)
    sizes = item.sizes.all().order_by('size_label')
    related = ClothingItem.objects.filter(brand=item.brand).exclude(pk=pk).select_related('brand').order_by('?')[:4]
    return render(request, 'trapApp/product_detail.html', {'item': item, 'sizes': sizes, 'related': related})


# ─── Auth ─────────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'trapApp/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email    = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user     = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return redirect('index')
            else:
                form.add_error(None, 'Невірний email або пароль')
    else:
        form = LoginForm()
    return render(request, 'trapApp/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required(login_url='/login/')
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дані оновлено')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'trapApp/profile.html', {'form': form})


# ─── Бренди ───────────────────────────────────────────────────────────────────

def brands_list(request):
    brands = Brand.objects.all().order_by('name')
    return render(request, 'trapApp/brands_list.html', {'brands': brands})


def _brand_context(brand, category_key=None):
    all_categories = []
    for cat_key, cat_label in ClothingItem.CATEGORY_CHOICES:
        count = ClothingItem.objects.filter(brand=brand, category=cat_key).count()
        all_categories.append((cat_key, cat_label, count))

    total_items = brand.items.count()

    if category_key:
        items = ClothingItem.objects.filter(
            brand=brand, category=category_key
        ).select_related('brand').order_by('name')
        category_labels = dict(ClothingItem.CATEGORY_CHOICES)
        category_label = category_labels.get(category_key, '')
    else:
        items = ClothingItem.objects.filter(
            brand=brand
        ).select_related('brand').order_by('category', 'name')
        category_label = None

    return {
        'brand':          brand,
        'items':          items,
        'all_categories': all_categories,
        'total_items':    total_items,
        'category_key':   category_key,
        'category_label': category_label,
    }


def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    context = _brand_context(brand, category_key=None)
    return render(request, 'trapApp/brand_detail.html', context)


def brand_category(request, slug, category):
    brand = get_object_or_404(Brand, slug=slug)
    category_labels = dict(ClothingItem.CATEGORY_CHOICES)
    if category not in category_labels:
        raise Http404("Категорія не знайдена")
    context = _brand_context(brand, category_key=category)
    return render(request, 'trapApp/brand_detail.html', context)


def nav_brands(request):
    brands = Brand.objects.all().order_by('name')
    return {'nav_brands': brands}




# ═══════════════════════════════════════════════════════════════════════════════
# КРОК 1: Додай імпорт на початок views.py (після наявних імпортів):
# from .cart import Cart
# ═══════════════════════════════════════════════════════════════════════════════
#
# КРОК 2: Додай ці функції в КІНЕЦЬ views.py
# ═══════════════════════════════════════════════════════════════════════════════


# ── Кошик ─────────────────────────────────────────────────────────────────────

def cart_view(request):
    """Повна сторінка кошика."""
    cart = Cart(request)
    return render(request, 'trapApp/cart.html', {
        'cart_items': cart.to_list(),
        'cart_total': cart.total,
        'cart_currency': cart.currency,
    })


@csrf_exempt
def cart_add(request, item_id):
    """POST /cart/add/<id>/ — додати товар у кошик, повернути JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    item = get_object_or_404(ClothingItem.objects.select_related('brand'), id=item_id)
    cart = Cart(request)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        body = {}

    size     = body.get('size', '')
    quantity = max(1, int(body.get('quantity', 1)))
    cart.add(item, size=size, quantity=quantity)

    # Повертаємо оновлений список для drawer
    return JsonResponse({
        'status':      'ok',
        'cart_count':  len(cart),
        'cart_total':  cart.total,
        'cart_currency': cart.currency,
        'cart_items':  cart.to_list(),
    })


@csrf_exempt
def cart_update(request):
    """POST /cart/update/ — змінити кількість."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'bad request'}, status=400)

    cart     = Cart(request)
    key      = body.get('key', '')
    quantity = int(body.get('quantity', 0))
    cart.update(key, quantity)

    subtotal = None
    for entry in cart:
        if entry['key'] == key:
            subtotal = entry['subtotal']
            break

    return JsonResponse({
        'status':      'ok',
        'cart_count':  len(cart),
        'cart_total':  cart.total,
        'cart_currency': cart.currency,
        'subtotal':    subtotal,
        'removed':     quantity <= 0,
        'cart_items':  cart.to_list(),
    })


@csrf_exempt
def cart_remove(request):
    """POST /cart/remove/ — видалити рядок."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'bad request'}, status=400)

    cart = Cart(request)
    key  = body.get('key', '')
    cart.remove(key)

    return JsonResponse({
        'status':      'ok',
        'cart_count':  len(cart),
        'cart_total':  cart.total,
        'cart_currency': cart.currency,
        'cart_items':  cart.to_list(),
    })