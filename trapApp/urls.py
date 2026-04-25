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

    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    path('brands/',                            views.brands_list,    name='brands_list'),
    path('brands/<slug:slug>/',                views.brand_detail,   name='brand_detail'),
    path('brands/<slug:slug>/<str:category>/', views.brand_category, name='brand_category'),

    # ── Кошик ──────────────────────────────────────────────────────────────
    path('cart/',                     views.cart_view,   name='cart'),
    path('cart/add/<int:item_id>/',   views.cart_add,    name='cart_add'),
    path('cart/update/',              views.cart_update, name='cart_update'),
    path('cart/remove/',              views.cart_remove, name='cart_remove'),

    # ── Нотатки / заходи ───────────────────────────────────────────────────
    path('notes/',                        views.note_list,       name='note_list'),
    path('notes/new/',                    views.note_create,     name='note_create'),
    path('notes/<int:pk>/',               views.note_detail,     name='note_detail'),
    path('notes/<int:pk>/delete/',        views.note_delete,         name='note_delete'),
    path('notes/<int:pk>/regenerate/',    views.note_regenerate,     name='note_regenerate'),
    path('notes/<int:pk>/builder/',       views.note_outfit_builder, name='note_outfit_builder'),
    path('notes/<int:pk>/reset/',         views.note_reset_outfit,   name='note_reset_outfit'),
]