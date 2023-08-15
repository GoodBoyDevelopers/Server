from django.shortcuts import render
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from dotenv import load_dotenv
import os
from django.http import HttpResponse
from django.http import JsonResponse
import json
from models.models import *
from .serializers import *
from rest_framework.generics import CreateAPIView
from rest_framework import status
from rest_framework.response import Response

def get_summary_keywords(scripts) :
    load_dotenv()
    try :
        openai.api_key = os.getenv("OPENAI_API_KEY")
        messages = [
            {"role": "system", "content": "Your role is to summarize the article, extract keywords, and respond appropriately to the format."},
            {"role": "user", "content": f"{scripts}"},
            {"role": "user", "content": "Summarize this article in Korean. Additionally extract up to two simple keywords from the article in Korean"},
            {"role": "assistant", "content": "Could you give it in JSON format with summary and keywords as key?"}
        ]
        answer = ""
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

class ScriptsCreateAPIView(CreateAPIView):
    queryset = Youtube.objects.all()
    serializer_class = YoutubeSerializer
    
    def create(self, request, *args, **kwargs):
        link = request.data["link"]
        if link:
            # 유튜브 script 추출
            video_id = link.split("v=")[1]
            print(video_id)
            script = script_extraction(video_id)
            print(script)
            if script == "":
                return JsonResponse({"message" : "Scripts Extraction Failed"}, status=400)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            youtube = Youtube.objects.get(id=serializer.data["id"])
            Script(script=script, youtube=youtube).save()
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return JsonResponse({"message" : "No Link"}, status=400)

class KeywordCreateAPIView(CreateAPIView):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    
    def create(self, request, *args, **kwargs):
        id = request.data["id"]
        if id:
            # 유튜브 script 추출
            youtube=Youtube.objects.get(id=id)
            script=Script.objects.get(youtube=youtube).script
            print(script)
            data = json.loads(get_summary_keywords(script))
            print(data)
            if data == "" or sorted(data.keys()) != ["keywords", "summary"]:
                return JsonResponse({"message" : "Summary Keywords Extraction Failed"}, status=400)
            data["youtube"]=id
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

