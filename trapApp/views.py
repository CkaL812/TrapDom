import re
import json
import random
import logging
import requests
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from .models import ClothingItem, Event, CustomUser, Brand, Note, Style, SavedOutfit, WishlistItem, Order, OrderItem
from .forms import RegisterForm, LoginForm, ProfileForm, SetPasswordForm, PasswordChangeForm, NoteForm
from .cart import Cart

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
#   ГОЛОВНІ СТОРІНКИ
# ═══════════════════════════════════════════════════════════════════════════════

def index(request):
    brands = list(Brand.objects.all().order_by('name').prefetch_related('items'))
    for brand in brands:
        items = list(brand.items.all())
        brand.random_items = random.sample(items, min(4, len(items)))
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

# Підкатегорії що мають анатомічний / гендерний характер.
# Навіть якщо виріб позначений 'U' (унісекс) — не показувати чоловікам.
_FEMALE_ONLY_SUBCATS = frozenset({
    'skirt', 'dress', 'sundress', 'bikini', 'swimsuit',
    'heels', 'flats', 'crop_top', 'blouse', 'clutch', 'earrings',
})

# Явно чоловічі підкатегорії — не показувати жінкам.
_MALE_ONLY_SUBCATS = frozenset({
    'tie',
})

# Яким гендер-кодам дозволено бачити onepiece (сукні, сарафани, комбінезони)
_ONEPIECE_GENDERS = frozenset({'F'})

ITEMS_PER_CATEGORY = 3
CATEGORY_ORDER     = ['tops', 'layering', 'bottoms', 'onepiece', 'outerwear', 'footwear', 'accessory']

# Шаблони образу: роздільний (верх + низ) та суцільний (плаття/комбінезон)
SEPARATED_TEMPLATE = ['tops', 'layering', 'bottoms', 'outerwear', 'footwear', 'accessory']
ONEPIECE_TEMPLATE  = ['onepiece', 'layering', 'outerwear', 'footwear', 'accessory']

# Прогресивне послаблення фільтрів: від найжорсткіших до мінімальних
FILTER_PASSES = [
    {'formality': True,  'budget': True,  'styles': True,  'time': True,  'age': True,  'season': True},
    {'formality': True,  'budget': True,  'styles': True,  'time': False, 'age': False, 'season': True},
    {'formality': True,  'budget': True,  'styles': False, 'time': False, 'age': False, 'season': True},
    {'formality': True,  'budget': False, 'styles': False, 'time': False, 'age': False, 'season': True},
    {'formality': False, 'budget': False, 'styles': False, 'time': False, 'age': False, 'season': True},
    {'formality': False, 'budget': False, 'styles': False, 'time': False, 'age': False, 'season': False},
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

    # Базова фільтрація по гендеру.
    # Правило: M-теговані та F-теговані речі ніколи не перетинаються.
    # U-тегованих речей зараз 0, але якщо з'являться — фільтруємо їх
    # за чорними списками підкатегорій щоб уникнути гендерного переносу.
    if gender_db == 'M':
        # Суворо чоловічі + гендерно-нейтральні без жіночих підкатегорій
        qs = qs.filter(
            Q(gender='M') |
            (Q(gender='U') & ~Q(subcategory__in=_FEMALE_ONLY_SUBCATS))
        )
    elif gender_db == 'F':
        # Суворо жіночі + гендерно-нейтральні без чоловічих підкатегорій
        qs = qs.filter(
            Q(gender='F') |
            (Q(gender='U') & ~Q(subcategory__in=_MALE_ONLY_SUBCATS))
        )
    else:  # 'U' — без обмеження по гендеру, показуємо всі
        pass

    if season and opts.get('season', True):
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

        # Суцільний шаблон (onepiece) — виключно для жінок
        if gender_db in _ONEPIECE_GENDERS:
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

    orders = Order.objects.filter(user=user).prefetch_related('order_items')[:5]

    return render(request, 'trapApp/profile.html', {
        'profile_form':  profile_form,
        'password_form': password_form,
        'has_password':  has_password,
        'has_google':    has_google,
        'orders':        orders,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#   БРЕНДИ
# ═══════════════════════════════════════════════════════════════════════════════

def brands_list(request):
    brands = Brand.objects.all().order_by('name')
    return render(request, 'trapApp/brands_list.html', {'brands': brands})


def _brand_context(brand, category_key=None, subcategory_key=None, gender=None,
                   price_min=None, price_max=None, color=None, sort=None, page=1):
    base_q = Q(brand=brand)
    if gender:
        base_q &= Q(gender=gender)

    scope_q = Q(brand=brand)
    if category_key:
        scope_q &= Q(category=category_key)

    gender_counts = {
        'all': ClothingItem.objects.filter(scope_q).count(),
        'M':   ClothingItem.objects.filter(scope_q, gender='M').count(),
        'F':   ClothingItem.objects.filter(scope_q, gender='F').count(),
        'U':   ClothingItem.objects.filter(scope_q, gender='U').count(),
    }

    all_categories = []
    for ck, cl in ClothingItem.CATEGORY_CHOICES:
        count = ClothingItem.objects.filter(base_q, category=ck).count()
        all_categories.append((ck, cl, count))

    total_items = ClothingItem.objects.filter(base_q).count()

    subcategories = []
    if category_key:
        subcat_labels = dict(ClothingItem.SUBCATEGORY_CHOICES)
        raw = (ClothingItem.objects
               .filter(base_q, category=category_key)
               .values('subcategory')
               .annotate(n=Count('id'))
               .order_by('-n'))
        subcategories = [
            (r['subcategory'], subcat_labels.get(r['subcategory'], r['subcategory']), r['n'])
            for r in raw if r['n'] > 0
        ]

    if category_key:
        qs = ClothingItem.objects.filter(base_q, category=category_key).select_related('brand')
        if subcategory_key:
            qs = qs.filter(subcategory=subcategory_key)
        category_labels = dict(ClothingItem.CATEGORY_CHOICES)
        category_label  = category_labels.get(category_key, '')
    else:
        qs = ClothingItem.objects.filter(base_q).select_related('brand')
        category_label = None

    # Доступні кольори для поточного набору (до цінових фільтрів)
    available_colors = (
        qs.exclude(color='')
          .values_list('color', flat=True)
          .distinct()
          .order_by('color')
    )

    # Мін/макс ціна для слайдера
    from django.db.models import Min, Max
    price_bounds = qs.filter(price__isnull=False).aggregate(lo=Min('price'), hi=Max('price'))
    price_lo = int(price_bounds['lo'] or 0)
    price_hi = int(price_bounds['hi'] or 0)

    # Застосовуємо фільтри ціни та кольору
    if price_min:
        try:
            qs = qs.filter(price__gte=int(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            qs = qs.filter(price__lte=int(price_max))
        except ValueError:
            pass
    if color:
        qs = qs.filter(color__iexact=color)

    if sort == 'price_asc':
        qs = qs.order_by('price')
    elif sort == 'price_desc':
        qs = qs.order_by('-price')
    else:
        qs = qs.order_by('category', 'id') if not category_key else qs.order_by('id')

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(page)

    return {
        'brand':            brand,
        'items':            page_obj,
        'page_obj':         page_obj,
        'all_categories':   all_categories,
        'total_items':      total_items,
        'category_key':     category_key,
        'category_label':   category_label,
        'gender':           gender or '',
        'gender_counts':    gender_counts,
        'subcategories':    subcategories,
        'subcategory_key':  subcategory_key or '',
        'available_colors': list(available_colors),
        'selected_color':   color or '',
        'price_min':        price_min or '',
        'price_max':        price_max or '',
        'price_lo':         price_lo,
        'price_hi':         price_hi,
        'sort':             sort or '',
    }


def brand_detail(request, slug):
    brand = get_object_or_404(Brand, slug=slug)
    context = _brand_context(
        brand,
        gender    = request.GET.get('gender', ''),
        price_min = request.GET.get('price_min', ''),
        price_max = request.GET.get('price_max', ''),
        color     = request.GET.get('color', ''),
        sort      = request.GET.get('sort', ''),
        page      = request.GET.get('page', 1),
    )
    return render(request, 'trapApp/brand_detail.html', context)


def brand_category(request, slug, category):
    brand = get_object_or_404(Brand, slug=slug)
    if category not in dict(ClothingItem.CATEGORY_CHOICES):
        raise Http404("Категорія не знайдена")
    context = _brand_context(
        brand,
        category_key    = category,
        subcategory_key = request.GET.get('subcat', '') or None,
        gender          = request.GET.get('gender', ''),
        price_min       = request.GET.get('price_min', ''),
        price_max       = request.GET.get('price_max', ''),
        color           = request.GET.get('color', ''),
        sort            = request.GET.get('sort', ''),
        page            = request.GET.get('page', 1),
    )
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


# ═══════════════════════════════════════════════════════════════════════════════
#   НОТАТКИ / ЗАХОДИ
# ═══════════════════════════════════════════════════════════════════════════════

def _date_to_season(d):
    m = d.month
    if m in (3, 4, 5):  return 'spring'
    if m in (6, 7, 8):  return 'summer'
    if m in (9, 10, 11): return 'autumn'
    return 'winter'


def _generate_note_outfit(note):
    """Підбирає образ для нотатки та зберігає його (по 1 речі на категорію)."""
    payload = {
        'event':  note.event_name,
        'gender': note.gender,
        'season': _date_to_season(note.event_date),
    }
    formality_levels = _resolve_formality(note.event_name, None)
    selections, _, _ = _pick_items_with_fallback(payload, formality_levels, per_category=1)
    items = [item for cat_items in selections.values() for item in cat_items]
    note.outfit_items.set(items)


@login_required(login_url='/login/')
def note_list(request):
    today = date.today()
    notes = (
        request.user.notes
        .prefetch_related('outfit_items')
        .order_by('event_date', 'event_time')
    )
    return render(request, 'trapApp/note_list.html', {'notes': notes, 'today': today})


@login_required(login_url='/login/')
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            if note.mode == 'manual':
                return redirect('note_outfit_builder', pk=note.pk)
            messages.success(request, 'Захід створено! Образ буде підібрано вчасно.')
            return redirect('note_detail', pk=note.pk)
    else:
        form = NoteForm()
    return render(request, 'trapApp/note_create.html', {'form': form})


@login_required(login_url='/login/')
def note_detail(request, pk):
    from .tasks import _compute_notify_at
    note = get_object_or_404(Note, pk=pk, user=request.user)
    items = sorted(
        note.outfit_items.select_related('brand').all(),
        key=lambda x: (CATEGORY_ORDER.index(x.category) if x.category in CATEGORY_ORDER else 99),
    )
    notify_at = _compute_notify_at(note) if note.mode == 'auto' and not note.notification_sent else None
    return render(request, 'trapApp/note_detail.html', {
        'note':      note,
        'items':     items,
        'notify_at': notify_at,
    })


@login_required(login_url='/login/')
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Нотатку видалено')
        return redirect('note_list')
    return redirect('note_detail', pk=pk)


@login_required(login_url='/login/')
def note_regenerate(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST' and note.mode == 'auto':
        note.notification_sent = False
        note.save(update_fields=['notification_sent'])
        _generate_note_outfit(note)
        messages.success(request, 'Образ оновлено!')
    return redirect('note_detail', pk=pk)


@login_required(login_url='/login/')
def note_outfit_builder(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)

    valid_cats   = [c for c, _ in ClothingItem.CATEGORY_CHOICES]
    selected_cat = request.GET.get('cat', 'tops')
    if selected_cat not in valid_cats:
        selected_cat = 'tops'

    if request.method == 'POST':
        raw_ids  = request.POST.getlist('item_ids')
        item_ids = [int(i) for i in raw_ids if i.isdigit()]

        keep   = list(note.outfit_items.exclude(category=selected_cat))
        chosen = list(ClothingItem.objects.filter(id__in=item_ids, category=selected_cat))
        note.outfit_items.set(keep + chosen)

        next_cat = request.POST.get('next_cat', '')
        if next_cat and next_cat in valid_cats:
            return redirect(f"{request.path}?cat={next_cat}")

        # Фінальне збереження — позначаємо як вручну зібраний, скасовуємо авто-нотифікацію
        note.outfit_locked = True
        note.notification_sent = False
        note.save(update_fields=['outfit_locked', 'notification_sent'])
        messages.success(request, 'Образ збережено!')
        return redirect('note_detail', pk=note.pk)

    selected_ids   = set(note.outfit_items.values_list('id', flat=True))
    selected_subcat = request.GET.get('subcat', '')

    # Фільтруємо речі по гендеру нотатки
    gender_db  = GENDER_MAP.get(note.gender, 'U')
    base_items = ClothingItem.objects.filter(category=selected_cat).select_related('brand')
    if gender_db == 'M':
        base_items = base_items.filter(
            Q(gender='M') | (Q(gender='U') & ~Q(subcategory__in=_FEMALE_ONLY_SUBCATS))
        )
    elif gender_db == 'F':
        base_items = base_items.filter(
            Q(gender='F') | (Q(gender='U') & ~Q(subcategory__in=_MALE_ONLY_SUBCATS))
        )
    # else U — без обмеження по гендеру, показуємо всі

    # Підкатегорії для поточної category (з кількостями)
    subcat_labels = dict(ClothingItem.SUBCATEGORY_CHOICES)
    raw_subcats = (base_items.values('subcategory')
                   .annotate(n=Count('id'))
                   .order_by('-n'))
    subcategories = [
        (r['subcategory'], subcat_labels.get(r['subcategory'], r['subcategory']), r['n'])
        for r in raw_subcats if r['n'] > 0
    ]

    # Застосовуємо фільтр підкатегорії
    if selected_subcat:
        base_items = base_items.filter(subcategory=selected_subcat)

    items = base_items.order_by('brand__name', 'name')[:80]

    categories_with_counts = [
        (c, label, note.outfit_items.filter(category=c).count())
        for c, label in ClothingItem.CATEGORY_CHOICES
    ]

    return render(request, 'trapApp/note_outfit_builder.html', {
        'note':                   note,
        'items':                  items,
        'selected_cat':           selected_cat,
        'selected_subcat':        selected_subcat,
        'subcategories':          subcategories,
        'selected_ids':           selected_ids,
        'categories_with_counts': categories_with_counts,
        'valid_cats':             valid_cats,
    })


@login_required(login_url='/login/')
def note_reset_outfit(request, pk):
    """Скидає ручний образ — нотатка повертається в авто-режим."""
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        note.outfit_items.clear()
        note.outfit_locked     = False
        note.notification_sent = False
        note.save(update_fields=['outfit_locked', 'notification_sent'])
        messages.success(request, 'Образ скинуто — буде підібрано автоматично вчасно.')
    return redirect('note_detail', pk=pk)


# ═══════════════════════════════════════════════════════════════════════════════
#   ГАРДЕРОБ — підбір образу до власного одягу
# ═══════════════════════════════════════════════════════════════════════════════

_WARDROBE_COMPLEMENTS = {
    'tops':      ['bottoms', 'footwear', 'layering', 'accessory'],
    'layering':  ['bottoms', 'footwear', 'accessory'],
    'bottoms':   ['tops', 'footwear', 'layering', 'accessory'],
    'onepiece':  ['footwear', 'accessory', 'outerwear'],
    'outerwear': ['bottoms', 'footwear', 'accessory'],
    'footwear':  ['tops', 'bottoms', 'accessory'],
    'accessory': ['tops', 'bottoms', 'footwear'],
}

# Людські назви категорій для форми
_WARDROBE_CATEGORY_LABELS = {
    'tops':      {'title': 'Верх',         'hint': 'футболка · сорочка · топ'},
    'layering':  {'title': 'Другий шар',   'hint': 'худі · светр · кардиган'},
    'bottoms':   {'title': 'Низ',          'hint': 'штани · джинси · шорти'},
    'onepiece':  {'title': 'Суцільний',    'hint': 'сукня · комбінезон'},
    'outerwear': {'title': 'Верхній одяг', 'hint': 'куртка · пальто · пуховик'},
    'footwear':  {'title': 'Взуття',       'hint': 'кросівки · черевики'},
    'accessory': {'title': 'Аксесуар',     'hint': 'сумка · шапка · ремінь'},
}


def _extract_dominant_color(pil_image):
    """
    Повертає (h°, s, v) домінантного кольору одягу на фото.
    Використовує тільки PIL + colorsys — без ML.
    """
    import colorsys
    try:
        img = pil_image.copy().convert('RGB')
        w, h = img.size
        # Центральна зона 60%×70% — відсікаємо фон і манекен/людину
        x0, y0 = int(w * 0.2), int(h * 0.12)
        x1, y1 = int(w * 0.8), int(h * 0.88)
        region = img.crop((x0, y0, x1, y1))
        region = region.resize((24, 24), resample=1)
        pixels = list(region.getdata())
        # Відфільтровуємо майже-білий фон і занадто темні пікселі
        filtered = [
            (r, g, b) for r, g, b in pixels
            if 18 < (r + g + b) / 3 < 228
        ]
        if len(filtered) < 8:
            filtered = pixels
        r_avg = sum(p[0] for p in filtered) / len(filtered)
        g_avg = sum(p[1] for p in filtered) / len(filtered)
        b_avg = sum(p[2] for p in filtered) / len(filtered)
        h_val, s_val, v_val = colorsys.rgb_to_hsv(r_avg / 255, g_avg / 255, b_avg / 255)
        return round(h_val * 360, 1), round(s_val, 3), round(v_val, 3)
    except Exception:
        return None, None, None


def _color_harmony_score(item_hex, dominant_hsv):
    """
    Повертає 0–10: наскільки колір item_hex гармонує з dominant_hsv.
    Вищий score → більш гармонійна пара.
    Використовує тільки colorsys (stdlib).
    """
    dh, ds, dv = dominant_hsv
    if not item_hex or dh is None:
        return 5  # немає даних → нейтральний score

    import colorsys
    try:
        hx = item_hex.lstrip('#')
        if len(hx) != 6:
            return 5
        r = int(hx[0:2], 16) / 255
        g = int(hx[2:4], 16) / 255
        b = int(hx[4:6], 16) / 255
        ih, is_, iv = colorsys.rgb_to_hsv(r, g, b)
        ih *= 360

        # Нейтральні речі (чорний/білий/сірий/беж) підходять до всього
        if is_ < 0.15 or iv < 0.12:
            return 9
        # Якщо uploaded item нейтральний — підходить будь-що
        if ds < 0.15:
            return 8

        hue_diff = abs(ih - dh)
        if hue_diff > 180:
            hue_diff = 360 - hue_diff

        if hue_diff <= 15:             return 10  # монохромний
        if hue_diff <= 30:             return 9   # аналогічний
        if hue_diff <= 60:             return 7   # близько аналогічний
        if 150 <= hue_diff <= 210:     return 6   # комплементарний
        if hue_diff <= 90:             return 4   # тріадний
        return 2                                   # конфліктний
    except Exception:
        return 5


def _wardrobe_pick_items(complement_cats, gender_code, dominant_hsv=None, per_cat=4):
    """
    Підбирає per_cat товарів для кожної категорії.
    Якщо є dominant_hsv — сортує пул за колірною гармонією,
    береться верхній ешелон з невеликою рандомізацією.
    """
    use_color = dominant_hsv and dominant_hsv[0] is not None
    cat_items = {}

    for cat in complement_cats:
        qs = ClothingItem.objects.filter(category=cat).select_related('brand')
        if gender_code == 'M':
            qs = qs.filter(
                Q(gender='M') | (Q(gender='U') & ~Q(subcategory__in=_FEMALE_ONLY_SUBCATS))
            )
        elif gender_code == 'F':
            qs = qs.filter(
                Q(gender='F') | (Q(gender='U') & ~Q(subcategory__in=_MALE_ONLY_SUBCATS))
            )

        pool = list(qs.order_by('?')[:100])
        if not pool:
            continue

        if use_color and len(pool) > per_cat:
            scored = [(item, _color_harmony_score(item.color_hex, dominant_hsv)) for item in pool]
            scored.sort(key=lambda x: x[1], reverse=True)
            best_score = scored[0][1]
            # Беремо всі items зі score в межах 2 балів від найкращого → рандомізуємо серед них
            top_tier = [item for item, s in scored if s >= best_score - 2]
            random.shuffle(top_tier)
            cat_items[cat] = top_tier[:per_cat]
        else:
            cat_items[cat] = random.sample(pool, min(per_cat, len(pool)))

    return cat_items


@login_required(login_url='/login/')
def wardrobe_upload(request):
    valid_cats = set(dict(ClothingItem.CATEGORY_CHOICES).keys())

    if request.method == 'GET':
        return render(request, 'trapApp/wardrobe_upload.html', {
            'wardrobe_categories': _WARDROBE_CATEGORY_LABELS,
        })

    # ── POST ──────────────────────────────────────────────────────────────
    photo       = request.FILES.get('photo')
    gender_raw  = request.POST.get('gender', 'U')
    category    = request.POST.get('category', 'tops')
    gender_code = {'M': 'M', 'F': 'F', 'U': 'U'}.get(gender_raw, 'U')

    if category not in valid_cats:
        category = 'tops'

    if not photo:
        messages.error(request, 'Будь ласка, завантажте фото одягу')
        return render(request, 'trapApp/wardrobe_upload.html', {
            'wardrobe_categories': _WARDROBE_CATEGORY_LABELS,
        })

    # Зберігаємо фото
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    import uuid

    ext = (photo.name.rsplit('.', 1)[-1].lower() if '.' in photo.name else 'jpg')
    ext = ext if ext in ('jpg', 'jpeg', 'png', 'webp') else 'jpg'
    filename = f'wardrobe/{uuid.uuid4().hex}.{ext}'
    photo.seek(0)
    saved_path = default_storage.save(filename, ContentFile(photo.read()))
    upload_image_url = settings.MEDIA_URL + saved_path

    # Аналіз кольору через PIL (без ML)
    dominant_hsv = (None, None, None)
    try:
        from PIL import Image as PILImage
        photo.seek(0)
        pil_img = PILImage.open(photo).convert('RGB')
        dominant_hsv = _extract_dominant_color(pil_img)
        logger.info(f'[wardrobe] dominant HSV: {dominant_hsv}')
    except Exception as exc:
        logger.warning(f'[wardrobe] color extract failed: {exc}')

    # Підбір комплементів з колірним скорингом
    complement_cats = _WARDROBE_COMPLEMENTS.get(category, ['bottoms', 'footwear', 'accessory'])
    cat_items = _wardrobe_pick_items(complement_cats, gender_code, dominant_hsv)

    ordered_cat_items = [
        (cat, cat_items[cat])
        for cat in CATEGORY_ORDER
        if cat in cat_items
    ]
    all_matched = [item for _, items in ordered_cat_items for item in items]
    cat_main_label = _WARDROBE_CATEGORY_LABELS.get(category, {}).get('title', category)

    saved_outfit_id = None
    if request.user.is_authenticated:
        outfit_obj = SavedOutfit.objects.create(
            user=request.user,
            source='wardrobe',
            name=f'Гардероб — {cat_main_label}',
            photo=saved_path,
        )
        outfit_obj.items.set(all_matched)
        saved_outfit_id = outfit_obj.pk

    return render(request, 'trapApp/wardrobe_results.html', {
        'upload_image_url':        upload_image_url,
        'uploaded_category_label': cat_main_label,
        'ordered_cat_items':       ordered_cat_items,
        'all_matched':             all_matched,
        'saved_outfit_id':         saved_outfit_id,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#   ЗБЕРЕЖЕНІ ОБРАЗИ
# ═══════════════════════════════════════════════════════════════════════════════

@login_required(login_url='/login/')
def my_outfits(request):
    outfits = (
        SavedOutfit.objects
        .filter(user=request.user)
        .prefetch_related('items__brand')
        .order_by('-created_at')
    )
    return render(request, 'trapApp/my_outfits.html', {'outfits': outfits})


@login_required(login_url='/login/')
def save_outfit(request):
    """AJAX POST: зберігає образ з picker або note в SavedOutfit."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'bad json'}, status=400)

    item_ids = [int(i) for i in body.get('item_ids', []) if str(i).isdigit()]
    source   = body.get('source', 'picker')
    name     = body.get('name', '') or 'Образ'
    note_id  = body.get('note_id')

    if source not in ('picker', 'wardrobe', 'note'):
        source = 'picker'

    outfit = SavedOutfit.objects.create(
        user=request.user,
        name=name,
        source=source,
    )
    if item_ids:
        outfit.items.set(ClothingItem.objects.filter(id__in=item_ids))
    if note_id:
        try:
            outfit.note = Note.objects.get(pk=note_id, user=request.user)
            outfit.save(update_fields=['note'])
        except Note.DoesNotExist:
            pass

    return JsonResponse({'status': 'ok', 'outfit_id': outfit.pk})


@login_required(login_url='/login/')
def outfit_detail(request, pk):
    outfit = get_object_or_404(SavedOutfit, pk=pk, user=request.user)

    items = sorted(
        outfit.items.select_related('brand').all(),
        key=lambda x: (CATEGORY_ORDER.index(x.category) if x.category in CATEGORY_ORDER else 99),
    )

    # Групуємо по категоріях
    from itertools import groupby
    ordered_cat_items = []
    for cat_key in CATEGORY_ORDER:
        cat_group = [i for i in items if i.category == cat_key]
        if cat_group:
            ordered_cat_items.append((cat_key, cat_group))

    return render(request, 'trapApp/outfit_detail.html', {
        'outfit':            outfit,
        'items':             items,
        'ordered_cat_items': ordered_cat_items,
    })


@login_required(login_url='/login/')
def delete_outfit(request, pk):
    outfit = get_object_or_404(SavedOutfit, pk=pk, user=request.user)
    if request.method == 'POST':
        outfit.delete()
    return redirect('my_outfits')


# ═══════════════════════════════════════════════════════════════════════════════
#   ВІШЛІСТ
# ═══════════════════════════════════════════════════════════════════════════════

@login_required(login_url='/login/')
def wishlist_view(request):
    items = (
        ClothingItem.objects
        .filter(wishlisted_by__user=request.user)
        .select_related('brand')
        .order_by('-wishlisted_by__added_at')
    )
    return render(request, 'trapApp/wishlist.html', {'items': items})


@login_required(login_url='/login/')
@csrf_exempt
def wishlist_toggle(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    item = get_object_or_404(ClothingItem, pk=item_id)
    obj, created = WishlistItem.objects.get_or_create(user=request.user, item=item)
    if not created:
        obj.delete()
    return JsonResponse({
        'status': 'ok',
        'in_wishlist': created,
        'count': WishlistItem.objects.filter(user=request.user).count(),
    })


# ═══════════════════════════════════════════════════════════════════════════════
#   ПОШУК
# ═══════════════════════════════════════════════════════════════════════════════

def search_view(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        results = (
            ClothingItem.objects
            .filter(Q(name__icontains=q) | Q(brand__name__icontains=q))
            .select_related('brand')
            .order_by('brand__name', 'name')[:60]
        )
    return render(request, 'trapApp/search_results.html', {'q': q, 'results': results})


# ═══════════════════════════════════════════════════════════════════════════════
#   ЧЕКАУТ / ЗАМОВЛЕННЯ
# ═══════════════════════════════════════════════════════════════════════════════

@login_required(login_url='/login/')
def checkout_view(request):
    cart = Cart(request)
    cart_items = cart.to_list()
    if not cart_items:
        return redirect('cart')

    errors = {}
    form_data = {}

    if request.method == 'POST':
        form_data = {
            'full_name': request.POST.get('full_name', '').strip(),
            'phone':     request.POST.get('phone', '').strip(),
            'city':      request.POST.get('city', '').strip(),
            'address':   request.POST.get('address', '').strip(),
            'comment':   request.POST.get('comment', '').strip(),
        }
        if not form_data['full_name']:
            errors['full_name'] = "Вкажіть ім'я та прізвище"
        if not form_data['phone']:
            errors['phone'] = 'Вкажіть номер телефону'
        if not form_data['city']:
            errors['city'] = 'Вкажіть місто'
        if not form_data['address']:
            errors['address'] = 'Вкажіть адресу доставки'

        if not errors:
            total = cart.total
            currency = cart.currency or 'UAH'

            order = Order.objects.create(
                user=request.user,
                full_name=form_data['full_name'],
                phone=form_data['phone'],
                city=form_data['city'],
                address=form_data['address'],
                comment=form_data['comment'],
                total=total,
                currency=currency,
            )

            for ci in cart_items:
                item_obj = ClothingItem.objects.filter(pk=ci['id']).first()
                OrderItem.objects.create(
                    order=order,
                    item=item_obj,
                    name=ci['name'],
                    price=ci['price'],
                    quantity=ci['quantity'],
                    size=ci.get('size', ''),
                )

            cart.clear()
            from django.urls import reverse
            return redirect(reverse('order_detail', kwargs={'pk': order.pk}) + '?new=1')

    return render(request, 'trapApp/checkout.html', {
        'cart_items': cart_items,
        'cart_total': cart.total,
        'cart_currency': cart.currency,
        'form_data': form_data,
        'errors': errors,
    })


@login_required(login_url='/login/')
def orders_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('order_items')
    return render(request, 'trapApp/orders.html', {'orders': orders})


@login_required(login_url='/login/')
def orders_clear(request):
    if request.method == 'POST':
        Order.objects.filter(user=request.user).delete()
        messages.success(request, 'Історію замовлень очищено')
    return redirect('orders')


@login_required(login_url='/login/')
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == 'POST':
        if order.status in ('pending', 'confirmed'):
            order.status = 'cancelled'
            order.save(update_fields=['status'])
            messages.success(request, f'Замовлення #{order.pk} скасовано')
        else:
            messages.error(request, 'Це замовлення неможливо скасувати')
    return redirect('order_detail', pk=pk)


@login_required(login_url='/login/')
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'trapApp/order_confirm.html', {
        'order':  order,
        'is_new': request.GET.get('new') == '1',
    })