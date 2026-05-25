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

    # ── Гардероб ───────────────────────────────────────────────────────────
    path('wardrobe/', views.wardrobe_upload, name='wardrobe_upload'),

    # ── Вішліст ────────────────────────────────────────────────────────────
    path('wishlist/',                      views.wishlist_view,   name='wishlist'),
    path('wishlist/toggle/<int:item_id>/', views.wishlist_toggle, name='wishlist_toggle'),

    # ── Збережені образи ───────────────────────────────────────────────────
    path('outfits/',                     views.my_outfits,    name='my_outfits'),
    path('outfits/save/',                views.save_outfit,   name='save_outfit'),
    path('outfits/<int:pk>/',            views.outfit_detail, name='outfit_detail'),
    path('outfits/<int:pk>/delete/',     views.delete_outfit, name='delete_outfit'),

    # ── Пошук ─────────────────────────────────────────────────────────────
    path('search/', views.search_view, name='search'),

    # ── Чекаут / замовлення ───────────────────────────────────────────────
    path('checkout/',               views.checkout_view, name='checkout'),
    path('orders/',                 views.orders_view,   name='orders'),
    path('orders/clear/',           views.orders_clear,  name='orders_clear'),
    path('orders/<int:pk>/',        views.order_detail,  name='order_detail'),
    path('orders/<int:pk>/cancel/', views.cancel_order,  name='cancel_order'),

    # -- Oplata
    path('payment/<int:pk>/',         views.payment_view,         name='payment'),
    path('payment/<int:pk>/success/', views.payment_success_view, name='payment_success'),

    # ── Примірка ───────────────────────────────────────────────────────────────
    path('virtual-tryon/',                              views.virtual_tryon,        name='virtual_tryon'),
    path('virtual-tryon/start/',                        views.tryon_start,          name='tryon_start'),
    path('virtual-tryon/status/<str:job_id>/',          views.tryon_status,         name='tryon_status'),
    path('virtual-tryon/search/',                       views.tryon_search,         name='tryon_search'),
    path('virtual-tryon/catalog/',                      views.tryon_catalog,        name='tryon_catalog'),
    path('virtual-tryon/catalog/<slug:slug>/',          views.tryon_catalog,        name='tryon_catalog_brand'),
    path('virtual-tryon/result/<str:job_id>/',            views.tryon_result,         name='tryon_result'),
    path('virtual-tryon/history/',                      views.tryon_history,        name='tryon_history'),
    path('virtual-tryon/history/<int:pk>/delete/',      views.tryon_session_delete, name='tryon_session_delete'),

    #── Нотатки / заходи ───────────────────────────────────────────────────
    path('notes/',                        views.note_list,       name='note_list'),
    path('notes/new/',                    views.note_create,     name='note_create'),
    path('notes/<int:pk>/',               views.note_detail,     name='note_detail'),
    path('notes/<int:pk>/delete/',        views.note_delete,         name='note_delete'),
    path('notes/<int:pk>/regenerate/',    views.note_regenerate,     name='note_regenerate'),
    path('notes/<int:pk>/builder/',       views.note_outfit_builder, name='note_outfit_builder'),
    path('notes/<int:pk>/reset/',         views.note_reset_outfit,   name='note_reset_outfit'),
]