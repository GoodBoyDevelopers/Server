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

CLIENT_ID=os.getenv("X_NAVER_CLIENT_ID")
CLIENT_SECRET=os.getenv("X_NAVER_CLIENT_SECRET")

START = 1
DISPLAY = 10
NEWS_CNT = 3
GET_CNT = 0
NAVER_URL = "https://n.news.naver.com/mnews/article/"
ORDINARY_NEWS = ['100', '101', '102', '103', '104', '105']

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
            
            # 뉴스 추출
            if (naver_url[-3:]=='106'):
                news_info = build_entertain(soup, origin_link)
            elif naver_url[-3:] in ORDINARY_NEWS :
                news_info = build_ordinary(soup, origin_link)
            else :
                return False # 예외 : 뉴스 형식 다를 때
            
            if news_info == False :
                return False # 예외 :  Article 추출 실패 
            
            
            # Summary 추출
            summary = json.loads(get_summary_article(news_info['article']))
            if summary == "" or sorted(summary.keys()) != ["summary"]:
                return False #예외 : Summary 추출 실패        
            news_info['summary']=summary["summary"]
            
            print(news_info)
            return news_info
        
    except Exception as e :
        print ("Error Code: ", response.status_code)
        print(e)
        return


def get_responseUrl(keyword):
    '''
        ouput : 키워드 검색 시 상위 3개의 기사 추출 (naver api  이용)
    '''    
    encText=urllib.parse.quote(keyword)
    news = []

    
    query = f"?query={encText}&start={START}&display={DISPLAY}&sort=sim"
    url = "https://openapi.naver.com/v1/search/news" + query
        
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)

    try : 
        response = urllib.request.urlopen(request)
        if response.getcode() == 200:
            response_body = response.read().decode('utf-8')
            raw = json.loads(response_body)
            
            # 관련 검색어로 기사가 없는 경우
            if (raw['total'] == 0):
                print("No News")
                return False
            
            for item in raw['items']:
                # 기사 3개를 찾은 경우
                if GET_CNT == NEWS_CNT:
                    break
                
                # naver news 링크 있는 경우 
                link = item['link']
                if re.match(NAVER_URL, link):
                    news_info = get_newsinfo(raw["items"][0])
                    
                    # news 기사나 summary가 없는 경우
                    if news_info == False :
                        continue
                    GET_CNT = GET_CNT + 1
                    news.append(news_info)
                START = START + 1
    except Exception as e :
        print("Error Code in get_reponseUrl: ", response.getcode())
        print(e)
        return False
        
    # news 반환
    return news


class CreateNewsAPIView(generics.CreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def create(self, request, *args, **kwargs):
        keyword_id = request.data['id']
        keywords = Keyword.objects.get(id=keyword_id).keywords
        print(keywords)
        
        keyword = ' '.join(keywords)
        results=get_responseUrl(keyword)
        # 크롤링 실패
        if results == False:
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
