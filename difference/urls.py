from django.urls import path
from .views import ContentCreateAPIView


urlpatterns = [
    path('', ContentCreateAPIView.as_view()),
]