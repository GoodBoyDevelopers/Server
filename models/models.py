import uuid

from django.db import models


class Youtube(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    link = models.CharField(max_length=100)
    

class Script(models.Model):
    script = models.TextField()
    youtube = models.OneToOneField(Youtube, on_delete=models.CASCADE, related_name='scripts')
    

class Keyword(models.Model):
    keywords = models.JSONField()
    summary = models.TextField()
    youtube = models.OneToOneField(Youtube, on_delete=models.CASCADE, related_name='keywords')
    

class Article(models.Model):
    title = models.TextField()
    created_at = models.CharField(max_length=50)
    writer = models.CharField(max_length=50)
    newspaper_name = models.CharField(max_length=50)
    newspaper_thumbnail = models.URLField(null=True, blank=True)
    article = models.TextField()
    thumbnail = models.URLField(null=True, blank=True)
    summary = models.TextField()
    keywords = models.ForeignKey(Keyword, on_delete=models.CASCADE, related_name='articles')
    origin_link = models.URLField(null=True, blank=True)


class Content(models.Model):
    percentage = models.TextField()
    reason = models.TextField()
    article = models.OneToOneField(Article, on_delete=models.CASCADE, related_name='contents')