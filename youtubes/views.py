from django.shortcuts import render
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from dotenv import load_dotenv
import os
from django.http import HttpResponse
from django.http import JsonResponse

# Create your views here.

def parsing(summary_keyword):
    content, keyword_section = summary_keyword.split("\n\n")
    summary = content
    keywords = keyword_section.split(" ")
    data_dict = {
                "summary": summary,
                "keywords" : keywords,
            }
    return data_dict

def get_summary_keywords(scripts) :
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    messages = [
        {"role": "system", "content": "Your role is to summarize the article, extract keywords, and respond appropriately to the format."},
        {"role": "user", "content": f"{scripts} Summarize this article in Korean. Additionally extract 3 keywords from the article in Korean"},
        {"role": "assistant", "content": "[INSERT SUMMARY HERE]\n\n[INSERT KEYWORDS HERE]"}
    ]
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = messages,
    )
    answer = response['choices'][0]['message']['content']
    return answer

def script_extraction(video_id) :
    srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
    scripts = ""
    for s in srt :
        cleaned_s = s["text"].replace("''", "")
        scripts += cleaned_s
        if len(scripts) > 1024 :
            break
    return (scripts)

def youtube_view(request, video_id):
    if request.method == "GET":
        if video_id:
            # 유튜브 script 추출
            scripts = script_extraction(video_id)
            # summary와 keyword가 가져오기
            summary_keyword = get_summary_keywords(scripts)
            # parsing하고 dictionary파일로 만들기
            data_dict = parsing(summary_keyword)
            # JsonResponse 생성 및 반환
            return JsonResponse(data_dict)
        else:
            return HttpResponse("Missing video_id parameter", status=400)

