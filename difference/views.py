import json
import os
import openai
from dotenv import load_dotenv

from django.http import JsonResponse

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from models.models import *
from .serializers import *


def get_difference(scripts, articles) :
    load_dotenv()
    try :
        openai.api_key = os.getenv("OPENAI_API_KEY")
        messages = [
            {"role": "system", "content": "유튜브 영상 대본 요약본 하나와 뉴스 기사 요약본 1~3개를 줄게. 그러면 너는 내가 준 뉴스 기사 요약본 1~3개를 요약본 간의 공통점을 기반으로 다시 3줄짜리 새로운 한국어 요약본으로 만들어야 해. 그 다음 너가 방금 만든 뉴스 기사 요약본과 내가 처음에 준 유튜브 영상 대본 요약본이 얼마나 유사한지 판단해줘. 첫 번째 줄에는 유사성 판단을 퍼센트로 나타내줘. 두 번째 줄부터는 그렇게 판단한 이유를 설명해줘. 이  경우 3줄 미만으로 이유를 표시해줘. 한국 어르신들에게 팩트 체크를 도와주는 서비스에 사용될 것이기 때문에 이때는 매우 날카롭고 비판적으로 비교를 해줘야 해. 또 너의 답변이 모두 한국어로 되어 있어야 한다는 것을 명심해."},
            {"role": "user", "content": f"여기 유튜브 영상에 대한 요약 있어: {scripts}"}]
        for i in range(len(articles)):

            messages.append(
                {"role": "user", "content": f"이거는 기사{i}에 대한 요약이야: {articles[i].summary}"}
            )
        messages += [
            {"role": "user", "content": "유튜브 영상에 대한 요약과 기사에 대한 요약의 유사도 백분율과, 그에 대한 이유를 작성해줘"},
            {"role": "assistant", "content": "'percentage'와'reason'을 key로 가지는 JSON 형식으로 줘"}
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

        articles = Article.objects.filter(keywords=keyword.id)
        content = get_difference(summary, articles)
        print(content)

        data = json.loads(content)
        if data == "" or sorted(data.keys()) != ["percentage", "reason"]:
            return JsonResponse({"message" : "Content Extraction Failed"}, status=400)
        
        if str(data['percentage'])[-1] != '%':
            data['percentage'] = str(data['percentage']) + '%'
        data['youtube'] = youtube_id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)