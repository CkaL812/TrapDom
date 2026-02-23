from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from trapApp.views import home, digital_wardrobe, digital_wardrobe_result

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('digital-wardrobe/', digital_wardrobe, name='digital_wardrobe'),
    path('digital-wardrobe/result/<int:suggestion_id>/', digital_wardrobe_result, name='digital_wardrobe_result'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
