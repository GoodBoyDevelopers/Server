from django.urls import path
from .views import *
urlpatterns = [
    path('<str:video_id>/', youtube_view)
]