from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def index(request):
    return render(request, 'trapApp/index.html')

def outfit_picker(request):
    return render(request, 'trapApp/outfit_picker.html')

@csrf_exempt
def generate_outfit(request):
    if request.method == 'POST':
        data   = json.loads(request.body)
        event  = data.get('event', '')
        gender = data.get('gender', '')
        season = data.get('season', '')
        style  = data.get('style', '')
        return JsonResponse({'status': 'ok', 'message': f'Образ підібрано!'})
    return JsonResponse({'status': 'error'}, status=400)