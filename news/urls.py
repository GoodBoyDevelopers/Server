from django.urls import path
from .views import news_view


urlpatterns = [
    path('', news_view),
]