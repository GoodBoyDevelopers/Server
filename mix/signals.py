from django.db.models.signals import post_save
from django.dispatch import receiver

from models.models import *
from .youtubes import *
import json

@receiver(post_save, sender=Script)
def create_Keyword(sender, instance=None, created=False, **kwagrs):
    script = instance.script
    summary_keyword = json.loads(get_summary_keywords(script))
    Keyword(keyword=summary_keyword["keywords"], summary=summary_keyword["summary"], youtube=instance.youtube).save()