from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('outfit-picker/', views.outfit_picker, name='outfit_picker'),
    path('generate-outfit/', views.generate_outfit, name='generate_outfit'),
]