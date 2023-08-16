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
display = 1
news_cnt = 3

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
    naver_url=item['link']
    origin_link=item['originallink'] #원본 기사 링크
    print(naver_url)
    
    try :
        response = requests.get(naver_url)
        if (response.status_code == 200):
            soup = BeautifulSoup(response.text, 'html.parser')
            if (naver_url[-3:]=='106'):
                news_info = build_entertain(soup, origin_link)
            elif naver_url[-3:] in ['100', '101', '102', '103', '104', '105'] :
                news_info = build_ordinary(soup, origin_link)
            else :
                # 예외 : 뉴스 형식 다를 때
                return False
            if news_info == False :
                # 예외 : 잘 안 뽑혔을 때 ( 아티클 추출 실패 )
                return False
            print(news_info)
            
            summary = json.loads(get_summary_article(news_info['article']))
            if summary == "" or sorted(summary.keys()) != ["summary"]:
                return False
            print(summary)            
            news_info['summary']=summary["summary"]
            return news_info
        
    except Exception as e :
        print(e)
        return


def get_reponseUrl(keyword):
    '''
        ouput : 키워드 검색 시 상위 3개의 기사 추출 (naver api  이용)
    '''    
    encText=urllib.parse.quote(keyword)
    start = 1
    news = []
    cnt = 0
    for _ in range(10) :
        if cnt == news_cnt:
            break
        query = f"?query={encText}&start={start}&display={display}&sort=sim"
        url = "https://openapi.naver.com/v1/search/news" + query
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
    
        try:
            response = urllib.request.urlopen(request)
            if response.getcode() == 200:
                response_body = response.read().decode('utf-8')
                raw = json.loads(response_body)
                
                # 관련 검색어로 기사가 없는 경우
                if (raw['total'] == 0):
                    print("No News")
                    return False
                #print(raw['items'][0]['title'])
                # naver news 링크 없는 경우 
                naver_url = "https://n.news.naver.com/mnews/article/"
                link =  raw["items"][0]["link"]
                if re.match(naver_url, link):
                    
                    news_info = get_newsinfo(raw["items"][0])
                    # news 기사나 summary가 없는 경우
                    if news_info == False :
                        continue
                    
                    cnt += 1
                    news.append(news_info)
                    
                start += 1
        except Exception as e :
            rescode = response.getcode()
            print(f"Error Code in get_reponseUrl: {rescode}")
            print(e)
            return False
        
    # print("뉴스 출력 --------------")
    return news


class CreateNewsAPIView(generics.CreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def create(self, request, *args, **kwargs):
        keyword_id = request.data['id']
        keywords = Keyword.objects.get(id=keyword_id).keywords
        print(keywords)
        
        keyword = ' '.join(keywords)
        results = ''
        try:
            results=get_reponseUrl(keyword)
            if results == None :
                # 크롤링 실패
                return JsonResponse({"message": "No News"}, status=204)
                
        except Exception as e:
            return JsonResponse({"message" : "crawling failed"}, status=400)

        for res in results:
            res['keywords']=keyword_id
            serializer = self.get_serializer(data=res)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
        headers = self.get_success_headers(serializer.data)
        data = Article.objects.filter(keywords=keyword_id)
        serialized_data = self.get_serializer(data, many=True).data
        return Response(serialized_data, status=status.HTTP_201_CREATED, headers=headers)
