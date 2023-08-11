from django.shortcuts import render
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from dotenv import load_dotenv
import os
from django.http import HttpResponse
from django.http import JsonResponse
import json

def get_summary_keywords(scripts) :
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    messages = [
        {"role": "system", "content": "Your role is to summarize the article, extract keywords, and respond appropriately to the format."},
        {"role": "user", "content": f"{scripts}"},
        {"role": "user", "content": "Summarize this article in Korean. Additionally extract 3 keywords from the article in Korean"},
        {"role": "assistant", "content": "Could you give it in JSON format with summary and keywords as key?"}
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

def script_extraction(video_id) :
    scripts = ""
    try:
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
        for s in srt :
            cleaned_s = s["text"].replace("''", "")
            scripts += cleaned_s
            if len(scripts) > 1024:
                break
    except Exception as e:
        print(e)
    return scripts

# TODO LIST
# 1. 자막 추출 안될 때
def youtube_view(request, video_id):
    if request.method == "GET":
        if video_id:
            # 유튜브 script 추출
            scripts = script_extraction(video_id)
            if scripts != "":
                print(scripts)
                # summary와 keyword가 가져오기
                summary_keyword = get_summary_keywords(scripts)
                if summary_keyword != "" :
                    # parsing하고 dictionary파일로 만들기
                    data_dict = json.loads(summary_keyword)
                    return JsonResponse(data_dict)
            else:
                return JsonResponse({"message" : "Scripts Extraction Failed"}, status=400)
        else:
            return HttpResponse("Missing video_id parameter", status=400)

