# from django.db.models.signals import post_save
# from django.core import serializers
# from django.dispatch import receiver

# from models.models import Article, Keyword
# from .serializers import ArticleSerializer
# from .navernews import naver_news
# import requests


# @receiver(post_save, sender=Keyword)
# def create_post(sender, instance=None,  **kwargs):
#     keywords = instance.keyword
#     results = naver_news(keywords)
#     for res in results:
#         res['keyword'] = instance.id
#         serializer = ArticleSerializer(data=res)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         print(serializer.data)
        
    
