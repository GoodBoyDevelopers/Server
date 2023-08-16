from dotenv import load_dotenv
import json
import os
import re
import urllib

from bs4 import BeautifulSoup
import requests

from django.http import JsonResponse
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response

from models.models import Article, Keyword
from .serializers import ArticleSerializer

import openai
from .crawling import *

'''
    keyword 당 관련성 높은 기사 3개의 content, originalLink, summary
    - 프론트에서 필요한 것: 이미지, 신문사, 제목, 기사생성일
    - 백에서 필요한 것: 기사 원문 텍스트
'''

load_dotenv()

client_id=os.getenv("X_NAVER_CLIENT_ID")
client_secret=os.getenv("X_NAVER_CLIENT_SECRET")
api_key_id = os.getenv('X_NCP_APIGW_API_KEY_ID')
api_key = os.getenv('X_NCP_APIGW_API_KEY')


def cut_article(article) :
    if len(article) > 2000:
        truncated_string = article[:2000]
        return truncated_string
    else:
        return article

def get_summary_article(article):
    print(article)
    load_dotenv()
    try :
        openai.api_key = os.getenv("OPENAI_API_KEY")
        article = cut_article(article)
        messages = [
            {"role": "system", "content": "Your role is to summarize the article"},
            {"role": "user", "content": f"{article}"},
            {"role": "user", "content": "Summarize this article in Korean. "},
            {"role": "assistant", "content": "Could you give it in 'JSON format' with 'summary' as key?"}
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
def build_sports(soup, origin_link):
    pass


def get_newsinfo(item):
    '''
        output: 기사 3개 json 형태로 반환
    '''
    link=item['link']
    origin_link=item['originallink'] #원본 기사 링크
    naver_url = "https://n.news.naver.com/mnews/article/"
    sports_url = "https://sports.news.naver.com/news"

    if re.match(naver_url, link):
        response = requests.get(link)
        if (response.status_code != 200):
            return False
        soup = BeautifulSoup(response.text, 'html.parser')    
        # 연예
        if (naver_url[-3:]=='106'):
            news_info = build_entertain(soup, origin_link)
        # 정치 등등
        elif naver_url[-3:] in ['100', '101', '102', '103', '104', '105'] :
            news_info = build_ordinary(soup, origin_link)
        print(news_info)
        
        # 스포츠
    elif re.match(sports_url, link):
        response = requests.get(link)
        if (response.status_code != 200):
            return False
        soup = BeautifulSoup(response.text, 'html.parser')
        news_info = build_sports(soup, origin_link)
    else :
        # 예외 : 뉴스 형식 다를 때
        return False
    if news_info == False :
        # 예외 : 잘 안 뽑혔을 때 ( 아티클 추출 실패 )
        return False
    
    summary = json.loads(get_summary_article(news_info['article']))
    if summary == "" or sorted(summary.keys()) != ["summary"]:
        # 예외 : 뉴스 요약본 안 뽑힐 때
        return False
    print(summary)            
    news_info['summary']=summary["summary"]
    return news_info

def extract_news(items) :
    news_cnt = 3
    cnt = 0
    news = []
    for item in items :
        if cnt == news_cnt:
            break
        news_info = get_newsinfo(item)
        # news 기사나 summary가 없는 경우
        if news_info == False :
            continue
        cnt += 1
        news.append(news_info)
    if len(news) == 0 :
        return False
    return news


def get_news(keyword):
    '''
        ouput : 키워드 검색 시 상위 3개의 기사 추출 (naver api  이용)
    '''    
    encText=urllib.parse.quote(keyword)
    start = 1
    news = []
    display = 10
    query = f"?query={encText}&start={start}&display={display}&sort=sim"
    url = "https://openapi.naver.com/v1/search/news" + query
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    response = urllib.request.urlopen(request)
    if response.getcode() != 200:
        return False
    response_body = response.read().decode('utf-8')
    raws = json.loads(response_body)
    print(raws)
    if (raws['total'] == 0):
        return False
    news = extract_news(raws["items"])
    if news == False :
        return False
    return news


class CreateNewsAPIView(generics.CreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def create(self, request, *args, **kwargs):
        keyword_id = request.data['id']
        keywords = Keyword.objects.get(id=keyword_id).keywords
        print(keywords)
        
        keyword = ' '.join(keywords)
        results = get_news(keyword)
        if results == False :
            # 크롤링 실패
            return JsonResponse({"message": "No News"}, status=204)


        for res in results:
            res['keywords']=keyword_id
            serializer = self.get_serializer(data=res)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
        headers = self.get_success_headers(serializer.data)
        data = Article.objects.filter(keywords=keyword_id)
        serialized_data = self.get_serializer(data, many=True).data
        return Response(serialized_data, status=status.HTTP_201_CREATED, headers=headers)
