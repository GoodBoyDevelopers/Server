from django.urls import path
from .views import CreateNewsAPIView


urlpatterns = [
    path('', CreateNewsAPIView.as_view()),
]