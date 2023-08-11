# from django.shortcuts import render
import openai
from dotenv import load_dotenv
import os
from django.http import HttpResponse
from django.http import JsonResponse
import json

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
def mix_view(request):
    youtube_scripts = "한반도에 위치한 백두산은 활화산으로, 최근들어 2025년에 폭발할 것이라는 설이 돌고 있다. 이 설은 백두산의 마지막 분화 기록이 1925년이었기 때문에 100년 주기로 폭발할 것으로 예측되고 있다. 백두산의 폭발력은 최대 7단계로 추정되며, 946년에 발생한 폭발은 7단계였다. 백두산의 폭발력은 매우 강력하며, 그 위력은 일본까지 영향을 미칠 정도였다."
    article_scripts = "백두산이 곧 터진다"
    result = mix(youtube_scripts, article_scripts)
    if result != "":
        return JsonResponse(json.loads(result))
    else:
        return JsonResponse({"message" : "mix Failed"}, status=400)
