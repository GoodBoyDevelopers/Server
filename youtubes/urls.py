from django.urls import path
from .views import *
urlpatterns = [
    path('', YoutubeCreateAPIView.as_view())
]