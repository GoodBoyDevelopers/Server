# from django.shortcuts import render
import openai
from dotenv import load_dotenv
import os
from django.http import HttpResponse
from django.http import JsonResponse
import json
from models.models import *

def mix(youtube_scripts, article_scripts) :
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    messages = [
        {"role": "system", "content": "Your role is to analyze two articles."},
        {"role": "user", "content": f"{youtube_scripts}"},
        {"role": "user", "content": f"{article_scripts}"},
        {"role": "user", "content": "Analyze these two articles together in Korean."},
        {"role": "assistant", "content": "Could you give it in JSON format with result as key?"}
    ]
    answer = ""
    try :
        response = openai.ChatCompletion.create(
            model = "gpt-3.5-turbo",
            messages = messages,
            temperature = 0,
        )
        answer = response['choices'][0]['message']['content']
    except Exception as e :
        print(e)
    return answer

# TODO LIST
# 1. 자막 추출 안될 때
def mix_view(video_id):
    youtube_scripts = Keyword.objects.get()
    
    article_scripts = "백두산이 곧 터진다"
    result = mix(youtube_scripts, article_scripts)
    if result != "":
        return JsonResponse(json.loads(result))
    else:
        return JsonResponse({"message" : "mix Failed"}, status=400)
