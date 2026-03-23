from django.urls import path
from . import views

urlpatterns = [
    path('',                  views.index,           name='index'),
    path('outfit-picker/',    views.outfit_picker,   name='outfit_picker'),
    path('generate-outfit/',  views.generate_outfit, name='generate_outfit'),
    path('outfit-results/',   views.outfit_results,  name='outfit_results'),
    path('register/',         views.register_view,   name='register'),
    path('login/',            views.login_view,      name='login'),
    path('logout/',           views.logout_view,     name='logout'),
    path('profile/',          views.profile_view,    name='profile'),

    path('brands/',                            views.brands_list,    name='brands_list'),
    path('brands/<slug:slug>/',                views.brand_detail,   name='brand_detail'),
    path('brands/<slug:slug>/<str:category>/', views.brand_category, name='brand_category'),
]