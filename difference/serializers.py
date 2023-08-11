from rest_framework.serializers import ModelSerializer
from models.models import Content


class ContentSerializer(ModelSerializer):
    class Meta:
        model = Content
        fields = "__all__"