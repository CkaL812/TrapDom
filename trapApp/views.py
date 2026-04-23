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
from django.db.models import Q, Count
from .models import ClothingItem, Event, CustomUser, Brand
from .forms import RegisterForm, LoginForm, ProfileForm, SetPasswordForm, PasswordChangeForm
from .cart import Cart

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#   ГОЛОВНІ СТОРІНКИ
# ═══════════════════════════════════════════════════════════════════════════════

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

    CATEGORY_ORDER = ['tops', 'layering', 'bottoms', 'onepiece', 'outerwear', 'footwear', 'accessory']

    items_qs = ClothingItem.objects.filter(id__in=ids).select_related('brand')
    for item in items_qs:
        item.reason = reason_map.get(item.id, '')

    items_ordered = sorted(
        items_qs,
        key=lambda x: (CATEGORY_ORDER.index(x.category) if x.category in CATEGORY_ORDER else 99)
    )

    category_labels = dict(ClothingItem.CATEGORY_CHOICES)
    seen_cats = []
    cat_counts = {}
    for item in items_ordered:
        if item.category not in seen_cats:
            seen_cats.append(item.category)
        cat_counts[item.category] = cat_counts.get(item.category, 0) + 1

    categories = [
        {'key': k, 'label': category_labels.get(k, k), 'count': cat_counts[k]}
        for k in seen_cats
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


# ═══════════════════════════════════════════════════════════════════════════════
#   ЛОГІКА ПІДБОРУ ОБРАЗУ
# ═══════════════════════════════════════════════════════════════════════════════

# Пряме відображення JS-подій → рівень формальності (без урахування регістру)
EVENT_FORMALITY_MAP = {
    'день народження':             'smart_casual',
    'ювілей':                      'cocktail',
    'заручини':                    'cocktail',
    'розпис':                      'semi_formal',
    'весільний банкет (гість)':    'cocktail',
    'коктейльна вечірка':          'cocktail',
    'формальний вечір':            'after_five',
    'корпоратив':                  'business_casual',
    'конференція':                 'business_casual',
    'нетворкінг':                  'business_casual',
    'презентація':                 'business_casual',
    'публічний виступ':            'business_formal',
    'фотосесія':                   'smart_casual',
    'випуск з університету':       'semi_formal',
    'театр':                       'smart_casual',
    'опера / філармонія':          'black_tie_creative',
    'гала-вечір':                  'black_tie',
    'благодійний бал':             'black_tie',
    'свято в родині':              'smart_casual',
    'бранч / зустріч з друзями':   'smart_casual',
}

# Розширення formality → суміжні рівні для збільшення вибірки
FORMALITY_MAP = {
    'smart_casual':       ['smart_casual', 'business_casual'],
    'business_casual':    ['smart_casual', 'business_casual', 'semi_formal'],
    'festival_chic':      ['festival_chic', 'smart_casual'],
    'semi_formal':        ['business_casual', 'semi_formal', 'cocktail'],
    'after_five':         ['cocktail', 'after_five', 'semi_formal'],
    'cocktail':           ['semi_formal', 'cocktail', 'after_five'],
    'business_formal':    ['business_casual', 'business_formal', 'semi_formal'],
    'black_tie_creative': ['black_tie_creative', 'cocktail', 'black_tie'],
    'black_tie':          ['black_tie_creative', 'black_tie', 'white_tie'],
    'white_tie':          ['black_tie', 'white_tie'],
}

GENDER_MAP    = {'male': 'M', 'female': 'F', 'unisex': 'U'}
GENDER_LABELS = {'male': 'Чоловіча', 'female': 'Жіноча', 'unisex': 'Унісекс'}
SEASON_LABELS = {'spring': 'Весна', 'summer': 'Літо', 'autumn': 'Осінь', 'winter': 'Зима'}

ITEMS_PER_CATEGORY = 3
CATEGORY_ORDER     = ['tops', 'layering', 'bottoms', 'onepiece', 'outerwear', 'footwear', 'accessory']

# Шаблони образу: роздільний (верх + низ) та суцільний (плаття/комбінезон)
SEPARATED_TEMPLATE = ['tops', 'layering', 'bottoms', 'outerwear', 'footwear', 'accessory']
ONEPIECE_TEMPLATE  = ['onepiece', 'layering', 'outerwear', 'footwear', 'accessory']

# Прогресивне послаблення фільтрів: від найжорсткіших до мінімальних
FILTER_PASSES = [
    {'formality': True,  'budget': True,  'styles': True,  'time': True,  'age': True},
    {'formality': True,  'budget': True,  'styles': True,  'time': False, 'age': False},
    {'formality': True,  'budget': True,  'styles': False, 'time': False, 'age': False},
    {'formality': True,  'budget': False, 'styles': False, 'time': False, 'age': False},
    {'formality': False, 'budget': False, 'styles': False, 'time': False, 'age': False},
]

MODELS_TO_TRY = [
    "openrouter/free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-3-27b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "deepseek/deepseek-chat:free",
]


def _age_to_range(age):
    if age is None:
        return None
    age = int(age)
    if age <= 17: return '13-17'
    if age <= 24: return '18-24'
    if age <= 34: return '25-34'
    if age <= 44: return '35-44'
    if age <= 54: return '45-54'
    return '55+'


def _resolve_formality(event_str, dresscode):
    """
    Повертає formality_levels з пріоритетом:
    1. явно обраний dresscode
    2. JS-подія через EVENT_FORMALITY_MAP
    3. подія з БД
    """
    if dresscode and dresscode in FORMALITY_MAP:
        return FORMALITY_MAP[dresscode]
    formality = EVENT_FORMALITY_MAP.get(event_str.lower().strip())
    if formality:
        return FORMALITY_MAP.get(formality, [formality])
    event_obj = Event.objects.filter(name__iexact=event_str).first()
    if event_obj and event_obj.formality in FORMALITY_MAP:
        return FORMALITY_MAP[event_obj.formality]
    return []


def _filter_qs(qs, payload, formality_levels, opts):
    """Застосовує фільтри до queryset згідно з opts."""
    gender_db = GENDER_MAP.get(payload.get('gender'), 'U')
    season    = payload.get('season')

    qs = qs.filter(gender__in=[gender_db, 'U'])
    if season:
        qs = qs.filter(seasons__name=season)

    if opts['formality'] and formality_levels:
        qs = qs.filter(formality__in=formality_levels)

    if opts['budget']:
        bmin = payload.get('budget_min')
        bmax = payload.get('budget_max')
        if bmin is not None:
            qs = qs.filter(price__gte=bmin)
        if bmax is not None:
            qs = qs.filter(price__lte=bmax)

    if opts['styles']:
        styles = payload.get('styles', [])
        if styles:
            qs = qs.filter(styles__name__in=styles)

    if opts['time']:
        time_val = payload.get('time')
        if time_val:
            qs = qs.filter(tags__time_of_day__contains=[time_val])

    if opts['age']:
        age = payload.get('age')
        if age is not None:
            age_range = _age_to_range(age)
            if age_range:
                qs = qs.filter(tags__age_ranges__contains=[age_range])

    return qs.distinct()


def _has_complete_outfit(selections, template):
    """Перевіряє наявність мінімально повного образу (верх+низ+взуття або суцільний+взуття)."""
    if 'onepiece' in template:
        return bool(selections.get('onepiece')) and bool(selections.get('footwear'))
    return (bool(selections.get('tops')) and
            bool(selections.get('bottoms')) and
            bool(selections.get('footwear')))


def _pick_for_template(base_qs, payload, formality_levels, template, opts, per_cat):
    """Підбирає товари по категоріях для одного шаблону і набору фільтрів."""
    styles = payload.get('styles', [])
    qs = _filter_qs(base_qs, payload, formality_levels, opts)
    if styles and opts.get('styles'):
        qs = qs.annotate(
            style_match=Count('styles', filter=Q(styles__name__in=styles))
        ).order_by('-style_match', '?')
    else:
        qs = qs.order_by('?')
    return {cat: list(qs.filter(category=cat)[:per_cat]) for cat in template}


def _pick_items_with_fallback(payload, formality_levels, per_category=ITEMS_PER_CATEGORY):
    """
    Підбирає образ з прогресивним послабленням фільтрів.
    Спочатку пробує роздільний шаблон (tops+bottoms), потім суцільний (onepiece).
    Повертає (selections_dict, pass_num, template_name).
    """
    base_qs = (ClothingItem.objects
               .select_related('brand')
               .prefetch_related('seasons', 'styles'))
    gender_db = GENDER_MAP.get(payload.get('gender'), 'U')

    for pass_num, opts in enumerate(FILTER_PASSES):
        # Роздільний шаблон (tops + bottoms) — для всіх статей
        sep = _pick_for_template(base_qs, payload, formality_levels, SEPARATED_TEMPLATE, opts, per_category)
        if _has_complete_outfit(sep, SEPARATED_TEMPLATE):
            logger.info(f"[OUTFIT] separated, pass={pass_num}")
            sep['onepiece'] = []
            return sep, pass_num, 'separated'

        # Суцільний шаблон (onepiece) — для жінок і унісекс
        if gender_db in ('F', 'U'):
            one = _pick_for_template(base_qs, payload, formality_levels, ONEPIECE_TEMPLATE, opts, per_category)
            if _has_complete_outfit(one, ONEPIECE_TEMPLATE):
                logger.info(f"[OUTFIT] onepiece, pass={pass_num}")
                one['tops'] = []
                one['bottoms'] = []
                return one, pass_num, 'onepiece'

    # Останній шанс — без фільтрів, повертаємо все що є
    logger.warning("[OUTFIT] fallback: не знайдено повного образу після всіх pass-ів")
    last = _pick_for_template(base_qs, payload, formality_levels, SEPARATED_TEMPLATE, FILTER_PASSES[-1], per_category)
    last['onepiece'] = []
    return last, len(FILTER_PASSES), 'separated'


def _build_catalog_for_ai(selections):
    """Текстовий каталог для AI (тільки непусті категорії)."""
    lines = []
    for category in CATEGORY_ORDER:
        for item in selections.get(category, []):
            lines.append(
                f"ID:{item.id}|cat:{item.category}|{item.brand.name} {item.name}|"
                f"form:{item.formality}|color:{item.color or 'n/a'}|"
                f"price:{item.price or '?'}"
            )
    return "\n".join(lines)


def _parse_llm_json(raw: str) -> dict:
    """Витягає JSON з AI-відповіді, прибирає markdown/коментарі."""
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
        raise ValueError("JSON не знайдено у відповіді")
    raw = raw[start:end+1]
    raw = re.sub(r'//[^\n]*', '', raw)
    raw = re.sub(r',\s*}', '}', raw)
    raw = re.sub(r',\s*]', ']', raw)
    return json.loads(raw)


def _ask_ai_for_commentary(payload, selections, api_key):
    """AI пише outfit_name + stylist_comment + reasons. Повертає None якщо не спрацював."""
    event     = payload.get('event', '')
    gender    = GENDER_LABELS.get(payload.get('gender'), '')
    season    = SEASON_LABELS.get(payload.get('season'), '')
    dresscode = payload.get('dresscode', '')
    styles    = payload.get('styles', [])
    catalog   = _build_catalog_for_ai(selections)

    system_prompt = (
        "Ти — професійний стиліст. Для вже підібраного образу напиши коментарі.\n"
        "Поверни ТІЛЬКИ валідний JSON без markdown.\n"
        'Формат: {"outfit_name":"...","stylist_comment":"...","reasons":{"123":"...","456":"..."}}\n\n'
        "Правила:\n"
        "1. outfit_name — 3-5 слів українською, що описує стиль образу\n"
        "2. stylist_comment — 2 речення українською: чому цей образ підходить\n"
        "3. reasons — для КОЖНОГО ID з каталогу 1 речення українською чому ця річ у образі\n"
        "4. НЕ змінюй ID, НЕ додавай нові\n"
        "КРИТИЧНО: JSON валідний, ключі reasons — рядки (наприклад \"123\")."
    )

    user_prompt = (
        f"Подія: {event}\n"
        f"Стать: {gender}\n"
        f"Сезон: {season}\n"
        + (f"Дрес-код: {dresscode}\n" if dresscode else "")
        + (f"Обрані стилі: {', '.join(styles)}\n" if styles else "")
        + f"\nПідібрані речі:\n{catalog}"
    )

    for model_id in MODELS_TO_TRY:
        try:
            logger.info(f"[AI] Спроба моделі {model_id}")
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type":  "application/json",
                    "HTTP-Referer":  "https://trapdom.com",
                    "X-Title":       "TrapDom Outfit Picker",
                },
                json={
                    "model":    model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    "temperature": 0.5,
                    "max_tokens":  2048,
                },
                timeout=20,
            )
            resp.raise_for_status()
            raw    = resp.json()["choices"][0]["message"]["content"].strip()
            parsed = _parse_llm_json(raw)

            raw_reasons = parsed.get('reasons', {})
            reasons = {}
            for k, v in raw_reasons.items():
                try:
                    reasons[int(k)] = str(v)
                except (ValueError, TypeError):
                    continue

            logger.info(f"[AI] outfit_name отримано, {len(reasons)} reasons")
            return {
                'outfit_name':     parsed.get('outfit_name', 'Підібраний образ'),
                'stylist_comment': parsed.get('stylist_comment', ''),
                'reasons':         reasons,
            }
        except Exception as e:
            logger.warning(f"[AI] {model_id} не спрацював: {e}")

    logger.warning("[AI] Всі моделі провалились")
    return None


@csrf_exempt
@login_required(login_url='/login/')
def generate_outfit(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не підтримується'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Невалідний запит'}, status=400)

    event  = data.get('event', '').strip()
    gender = data.get('gender', '')
    season = data.get('season', '')

    if not event:
        return JsonResponse({'status': 'error', 'message': 'Вкажіть подію'}, status=400)
    if not gender or gender not in GENDER_MAP:
        return JsonResponse({'status': 'error', 'message': 'Вкажіть стать'}, status=400)
    if not season:
        return JsonResponse({'status': 'error', 'message': 'Вкажіть сезон'}, status=400)

    formality_levels = _resolve_formality(event, data.get('dresscode'))
    logger.info(f"[OUTFIT] event={event!r} → formality_levels={formality_levels}")

    selections, pass_used, template = _pick_items_with_fallback(data, formality_levels)
    total = sum(len(v) for v in selections.values())
    logger.info(
        f"[OUTFIT] template={template} pass={pass_used} total={total}: " +
        ", ".join(f"{k}={len(v)}" for k, v in selections.items() if v)
    )

    if total == 0:
        return JsonResponse({
            'status':  'error',
            'message': 'Нічого не знайдено за вашими критеріями. Спробуйте послабити фільтри.',
        }, status=404)

    outfit_name     = 'Підібраний образ'
    stylist_comment = ''
    reasons         = {}

    api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
    if api_key:
        ai_result = _ask_ai_for_commentary(data, selections, api_key)
        if ai_result:
            outfit_name     = ai_result['outfit_name']
            stylist_comment = ai_result['stylist_comment']
            reasons         = ai_result['reasons']
    else:
        logger.info("[OUTFIT] OPENROUTER_API_KEY відсутній — пропускаємо AI коментарі")

    all_items = []
    for category in CATEGORY_ORDER:
        for item in selections.get(category, []):
            all_items.append({'id': item.id, 'reason': reasons.get(item.id, '')})

    request.session['outfit_result'] = {
        'outfit_name':     outfit_name,
        'stylist_comment': stylist_comment,
        'event_name':      event,
        'gender':          GENDER_LABELS.get(gender, gender),
        'season':          SEASON_LABELS.get(season, season),
        'items':           all_items,
    }
    request.session.modified = True

    return JsonResponse({'status': 'ok', 'redirect': '/outfit-results/'})


# ═══════════════════════════════════════════════════════════════════════════════
#   PRODUCT DETAIL
# ═══════════════════════════════════════════════════════════════════════════════

def product_detail(request, pk):
    item = get_object_or_404(ClothingItem.objects.select_related('brand').prefetch_related('sizes'), pk=pk)
    sizes = item.sizes.all().order_by('size_label')
    related = ClothingItem.objects.filter(brand=item.brand).exclude(pk=pk).select_related('brand').order_by('?')[:4]
    return render(request, 'trapApp/product_detail.html', {'item': item, 'sizes': sizes, 'related': related})


# ═══════════════════════════════════════════════════════════════════════════════
#   AUTH
# ═══════════════════════════════════════════════════════════════════════════════

def _safe_next(next_url):
    """Повертає next_url тільки якщо він відносний (захист від open redirect)."""
    if next_url and next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return '/'


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    next_url = _safe_next(request.GET.get('next') or request.POST.get('next'))
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(next_url)
    else:
        form = RegisterForm()
    return render(request, 'trapApp/register.html', {'form': form, 'next': next_url})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    next_url = _safe_next(request.GET.get('next') or request.POST.get('next'))
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email    = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user     = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return redirect(next_url)
            else:
                form.add_error(None, 'Невірний email або пароль')
    else:
        form = LoginForm()
    return render(request, 'trapApp/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required(login_url='/login/')
def profile_view(request):
    user         = request.user
    has_password = user.has_usable_password()
    has_google   = user.social_auth.filter(provider='google-oauth2').exists()

    profile_form  = ProfileForm(instance=user)
    password_form = PasswordChangeForm(user) if has_password else SetPasswordForm()

    if request.method == 'POST':
        action = request.POST.get('action', 'profile')

        if action == 'profile':
            profile_form = ProfileForm(request.POST, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Дані профілю оновлено')
                return redirect('profile')

        elif action == 'password':
            if has_password:
                password_form = PasswordChangeForm(user, request.POST)
                if password_form.is_valid():
                    user.set_password(password_form.cleaned_data['new_password1'])
                    user.save()
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, 'Пароль успішно змінено')
                    return redirect('profile')
            else:
                password_form = SetPasswordForm(request.POST)
                if password_form.is_valid():
                    user.set_password(password_form.cleaned_data['new_password1'])
                    user.save()
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, 'Пароль встановлено')
                    return redirect('profile')

    return render(request, 'trapApp/profile.html', {
        'profile_form':  profile_form,
        'password_form': password_form,
        'has_password':  has_password,
        'has_google':    has_google,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#   БРЕНДИ
# ═══════════════════════════════════════════════════════════════════════════════

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
#   КОШИК
# ═══════════════════════════════════════════════════════════════════════════════

def cart_view(request):
    cart = Cart(request)
    return render(request, 'trapApp/cart.html', {
        'cart_items':    cart.to_list(),
        'cart_total':    cart.total,
        'cart_currency': cart.currency,
    })


@csrf_exempt
def cart_add(request, item_id):
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

    return JsonResponse({
        'status':        'ok',
        'cart_count':    len(cart),
        'cart_total':    cart.total,
        'cart_currency': cart.currency,
        'cart_items':    cart.to_list(),
    })


@csrf_exempt
def cart_update(request):
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
        'status':        'ok',
        'cart_count':    len(cart),
        'cart_total':    cart.total,
        'cart_currency': cart.currency,
        'subtotal':      subtotal,
        'removed':       quantity <= 0,
        'cart_items':    cart.to_list(),
    })


@csrf_exempt
def cart_remove(request):
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
        'status':        'ok',
        'cart_count':    len(cart),
        'cart_total':    cart.total,
        'cart_currency': cart.currency,
        'cart_items':    cart.to_list(),
    })