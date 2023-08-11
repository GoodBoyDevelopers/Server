from django.urls import path
from .views import mix_view


urlpatterns = [
    path('', mix_view),
]