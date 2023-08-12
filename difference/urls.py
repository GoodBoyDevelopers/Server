from django.urls import path, include
from .views import ContentCreateAPIView

urlpatterns = [
    path('', ContentCreateAPIView.as_view()),
]