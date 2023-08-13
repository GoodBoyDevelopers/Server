from django.shortcuts import render
import openai
from dotenv import load_dotenv
import os
from django.http import HttpResponse
from django.http import JsonResponse
import json
from models.models import *
from rest_framework.generics import CreateAPIView
from .serializers import *
from rest_framework import status
from rest_framework.response import Response

def get_difference(scripts, articles) :
    load_dotenv()
    try :
        openai.api_key = os.getenv("OPENAI_API_KEY")
        messages = [
            {"role": "system", "content": "I will give you a summary of YouTube video script and 1 to 3 summaries of news articles. Then, first of all, please newly summarize the summaries of the news articles you received into three new sentences focusing on the similarities between them. Then you have to compare the summary of news articles you just made to the summary of YouTube video script that I already gave you at the first time. And then, please judge how similar these two summaries are. Please indicate the judgement of similarity as a percentage in the first line. From the second line, please explain why you judged like that. In this case, please indicate the reason less than 3 sentences. You should compare it very sharply and critically at this time because you will be used for a service that helps the elders with fact-checking."},
            {"role": "user", "content": f"Here is the summary of youtube video script. {scripts}"}]
        for i in range(len(articles)):

            messages.append(
                {"role": "user", "content": f"Here is the summary of article{i}. {articles[i].article}"}
            )
        messages += [
            {"role": "user", "content": "For the output, at the first line, please show me the percentage of the similarity between the summary of Youtube video script that I gave you and the summary you just made. From the second line, please tell me the reason why you judge the similarty like that. You have to return the answer in Korean."},
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

class ContentCreateAPIView(CreateAPIView):
    queryset = Content
    serializer_class = ContentSerializer

    def create(self, request, *args, **kwargs):
        youtube_id = request.data.get("id")
        keyword = Keyword.objects.get(youtube=youtube_id)
        summary = keyword.summary
        articles = Article.objects.filter(keyword = keyword.id)
        content = get_difference(summary, articles)
        data = {
            "content" : content,
            "youtube" : youtube_id
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)