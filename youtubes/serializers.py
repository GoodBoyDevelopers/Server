from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from models.models import *

class YoutubeSerializer(ModelSerializer):
    class Meta:
        model = Youtube
        fields = '__all__'

class ScriptsSerializer(ModelSerializer):
    class Meta:
        model = Script
        fields = '__all__'

class KeywordSerializer(ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'

