import json
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ClothingItem, Event, CustomUser
from .forms import RegisterForm, LoginForm, ProfileForm


def index(request):
    return render(request, 'trapApp/index.html')


@login_required(login_url='/login/')
def outfit_picker(request):
    return render(request, 'trapApp/outfit_picker.html')


def outfit_results(request):
    result = request.session.get('outfit_result')
    if not result:
        return redirect('outfit_picker')

    items_data = result.get('items', [])
    ids = [item['id'] for item in items_data]
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


@csrf_exempt
@login_required(login_url='/login/')
def generate_outfit(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)

    data   = json.loads(request.body)
    event  = data.get('event', '').strip()
    gender = data.get('gender', '')
    season = data.get('season', '')

    qs = ClothingItem.objects.select_related('brand').all()

    if gender in GENDER_MAP:
        qs = qs.filter(gender__in=[GENDER_MAP[gender], 'U'])

    event_obj = Event.objects.filter(name__iexact=event).first()
    if event_obj and event_obj.formality in FORMALITY_MAP:
        qs = qs.filter(formality__in=FORMALITY_MAP[event_obj.formality])

    items = list(qs[:100])

    if not items:
        items = list(
            ClothingItem.objects.select_related('brand')
            .filter(gender__in=[GENDER_MAP.get(gender, 'U'), 'U'])[:100]
        )

    if not items:
        return JsonResponse({'status': 'error', 'message': 'У базі даних немає речей для підбору.'}, status=404)

    catalog_lines = []
    for item in items:
        line = (
            f"ID:{item.id}|{item.brand.name} {item.name}|"
            f"cat:{item.category}|form:{item.formality}|"
            f"color:{item.color or 'n/a'}|mat:{item.material or 'n/a'}|"
            f"pat:{item.pattern}|gender:{item.gender}"
        )
        catalog_lines.append(line)
    catalog_text = "\n".join(catalog_lines)

    system_prompt = (
        "You are a professional fashion stylist AI. "
        "Select clothing items from the catalog to compose a complete, stylish outfit. "
        "You MUST return ONLY a valid JSON object — no markdown, no explanation, no extra text. "
        'Exact format: {"outfit_name":"...", "stylist_comment":"...", "items":[{"id":1,"reason":"..."}]} '
        "Rules: "
        "1. Use ONLY IDs from the catalog. "
        "2. Select 3–7 items covering different categories (tops/bottoms or onepiece, footwear, optional layering/accessory). "
        "3. Ensure color harmony and formality consistency. "
        "4. outfit_name: short Ukrainian name (3–5 words). "
        "5. stylist_comment: 2–3 sentences in Ukrainian explaining why this outfit works. "
        "6. reason per item: 1 short Ukrainian sentence."
    )

    user_prompt = (
        f"Event: {event or 'general occasion'}\n"
        f"Gender: {gender or 'unisex'}\n"
        f"Season: {season or 'any'}\n\n"
        f"Catalog:\n{catalog_text}"
    )

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://trapdom.com",
                "X-Title": "TrapDom Outfit Picker",
            },
            json={
                "model": "google/gemini-2.0-flash-001",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                "temperature": 0.4,
                "max_tokens": 512,
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        return JsonResponse({'status': 'error', 'message': f'OpenRouter помилка: {str(e)}'}, status=502)

    try:
        raw = response.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        llm_data       = json.loads(raw)
        selected_items = llm_data.get("items", [])

        if not selected_items:
            return JsonResponse({'status': 'error', 'message': 'LLM не повернув жодного елементу.'}, status=500)

    except (KeyError, json.JSONDecodeError, IndexError) as e:
        return JsonResponse({'status': 'error', 'message': f'Помилка парсингу: {str(e)}'}, status=500)

    selected_ids = [item['id'] for item in selected_items]
    reason_map   = {item['id']: item.get('reason', '') for item in selected_items}

    valid_items = ClothingItem.objects.filter(id__in=selected_ids).select_related('brand')

    request.session['outfit_result'] = {
        'outfit_name':     llm_data.get('outfit_name', 'Підібраний образ'),
        'stylist_comment': llm_data.get('stylist_comment', ''),
        'event_name':      event,
        'gender':          GENDER_LABELS.get(gender, gender),
        'season':          SEASON_LABELS.get(season, season),
        'items': [
            {'id': item.id, 'reason': reason_map.get(item.id, '')}
            for item in valid_items
        ],
    }

    return JsonResponse({'status': 'ok', 'redirect': '/outfit-results/'})


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