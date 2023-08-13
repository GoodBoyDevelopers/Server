from django.urls import path
from .views import *
urlpatterns = [
    path('script/', ScriptsCreateAPIView.as_view()),
    path('keyword/', KeywordCreateAPIView.as_view())
]