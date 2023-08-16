from django.urls import path
from .views import ScriptsCreateAPIView, KeywordCreateAPIView


urlpatterns = [
    path('script/', ScriptsCreateAPIView.as_view()),
    path('keyword/', KeywordCreateAPIView.as_view()),
]