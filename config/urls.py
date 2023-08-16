from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('news/', include("news.urls")),
    path('youtube/', include("youtubes.urls")),
    path('difference/', include("difference.urls")),
    re_path(r'^static/(?:.*)$', serve, {'document_root': settings.STATIC_ROOT, }),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
