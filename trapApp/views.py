from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Event, UserWardrobeItem, OutfitSuggestion, Product
from .services.openrouter_service import analyze_wardrobe_image

def home(request):
    return render(request, 'trapApp/index.html')

def digital_wardrobe(request):
    events = Event.objects.all()
    
    if request.method == "POST":
        # 1. Отримуємо фото та подію
        photo = request.FILES.get("wardrobe_image")
        event_id = request.POST.get("event")
        
        if not photo or not event_id:
            messages.error(request, "Будь ласка, завантажте фото та оберіть подію.")
            return redirect("digital_wardrobe")
            
        event = get_object_or_404(Event, id=event_id)
        
        # 2. Зберігаємо фото в базі
        # Тимчасовий ідентифікатор сесії (в реальному житті це request.user)
        session_id = request.session.session_key or "anonymous_user"
        wardrobe_item = UserWardrobeItem.objects.create(
            user_identifier=session_id,
            image=photo
        )
        
        # 3. Аналізуємо через ШІ
        image_path = wardrobe_item.image.path
        ai_result = analyze_wardrobe_image(image_path)
        
        wardrobe_item.category_guess = ai_result.get("category_guess", "Unknown")
        wardrobe_item.color = ai_result.get("color", "Unknown")
        wardrobe_item.style = ai_result.get("style", "Unknown")
        wardrobe_item.save()
        
        # 4. Підбираємо товари з бази даних (проста логіка підбору для MVP)
        # Спочатку знаходимо товари, які підходять під потрібну подію
        matching_products = Product.objects.filter(events=event)
        
        # Рекомендуємо лише ті товари, категорія яких ВІДРІЗНЯЄТЬСЯ від завантаженої речі 
        # (якщо користувач завантажив "Верхній одяг", підберемо штани або взуття)
        exclude_keyword = "верхній" if "сороч" in wardrobe_item.category_guess.lower() else "нижній"
        if wardrobe_item.category_guess != "Unknown":
            matching_products = matching_products.exclude(category__name__icontains=exclude_keyword)
            
        # Беремо 3 рандомні підходящі речі
        suggested = matching_products.order_by("?")[:3]
        
        # 5. Зберігаємо комбінацію (Лукбук)
        suggestion = OutfitSuggestion.objects.create(
            wardrobe_item=wardrobe_item,
            event=event,
            ai_reasoning=f"AI detected: {wardrobe_item.color} {wardrobe_item.category_guess} ({wardrobe_item.style}). Matching with event dress code."
        )
        for prod in suggested:
            suggestion.suggested_products.add(prod)
            
        return redirect("digital_wardrobe_result", suggestion_id=suggestion.id)

    return render(request, "trapApp/digital_wardrobe.html", {"events": events})

def digital_wardrobe_result(request, suggestion_id):
    suggestion = get_object_or_404(OutfitSuggestion, id=suggestion_id)
    return render(request, "trapApp/outfit_result.html", {"suggestion": suggestion})
