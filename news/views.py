from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
import os
import re
import requests
import urllib

from django.http import JsonResponse
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response

from models.models import Article, Keyword
from .serializers import ArticleSerializer

import openai


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
news_cnt = 1

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

def build_entertain(soup, origin_link):
    news_info = {}
    # 제목
    if soup.select_one("h2.end_tit"):
        title = soup.select_one("h2.end_tit").get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        news_info['title'] = title
    else:
        news_info['title'] = "title Unknown"

    
    # 생성일
    if soup.select_one('span.author'):
        created_at = soup.select_one('span.author')
        if created_at.em:
            news_info['created_at'] = created_at.em.get_text()
        else:
            news_info['created_at'] = 'date Unkown'

    # 기자
    if soup.select_one("div.byline"):
        writer = soup.select_one("div.byline")
        if writer.span:
            news_info['writer'] = writer.get_text().strip().split()[0] 
        else:
            news_info['writer'] = 'Anonymous'

    
    # 신문사 정보
    if soup.find('a', class_="press_logo").img['alt']:
        name = soup.find('a', class_="press_logo").img['alt']
        news_info['newspaper_name'] = name
    else:
        news_info['newspaper_name'] = 'newspaper unknown'

    
    if soup.find('a', class_="press_logo").img['src']:
        img = soup.find('a', class_="press_logo").img['src']
        news_info['newspaper_thumbnail'] =img
    else:
        news_info['newspaper_thumbnail'] = 'default image'

        
    # 원본 기사 링크
    news_info['origin_link'] = origin_link

    article =""
            
    origin_body = soup.select_one('div.end_body_wrp')
    photos = origin_body.find_all(class_="end_photo_org")

    if photos :
        thumbnail = ""
        for pt in photos:
            if thumbnail == "":
                thumbnail = pt.img['src']
            pt.extract() 
        news_info['thumbnail']=thumbnail
    else:
        news_info['thumbnail'] = 'default image'

    if origin_body:
        article = origin_body.get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        article = ' '.join(article.split())
        article = '. '.join([x.strip() for x in article.split('.')])
    else:
        article= None
        
    news_info['article']=article 
    # print("entertain success!",news_info)
    
    return news_info

def build_sports(soup, origin_link):
    pass

def build_ordinary(soup, origin_link):
    '''
        output: 기사 title, creatd_at, (updated_at), writer, article, newspaper(name, img), thumbnail
    '''
    news_info = {}
    
    # 제목
    if soup.select_one('h2.media_end_head_headline'):
        title = soup.select_one('h2.media_end_head_headline').get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        news_info['title'] = title
    else: 
        news_info['title'] = "title unknown"
    print(news_info['title'])
    
    #생성일 - span 오류 처리해야 하는데....왜 안 먹히냐
    if soup.select_one('div.media_end_head_info_datestamp_bunch'):
        created_at = soup.select_one('div.media_end_head_info_datestamp_bunch')
        if created_at.span:
            news_info['created_at'] = created_at.span.get_text() 
    else:
        news_info['created_at'] = 'date unknown'
    print(news_info['created_at'])

    #작성자
    if soup.select_one('em.media_end_head_journalist_name'):
        writer  = soup.select_one('div.media_end_head_journalist')
        news_info['writer'] = writer.get_text().strip().split()[0]  
    else:
        news_info['writer'] = 'anonymous'
    print(news_info['writer'])
    
    # 원본 기사 링크
    news_info['origin_link'] = origin_link
    
    # 신문사 정보

    if soup.find('a', class_="media_end_head_top_logo").img['title']:
        name = soup.find('a', class_="media_end_head_top_logo").img['title']
        news_info['newspaper_name'] = name
    else:
        news_info['newspaper_name'] = 'newspaper unknown'
    
    if soup.find('a', class_="media_end_head_top_logo").img['src']:
        img = soup.find('a', class_="media_end_head_top_logo").img['src']
        news_info['newspaper_thumbnail'] =img
    else:
        news_info['newspaper_thumbnail'] = 'default image'
    
    ''' 
        todo 
            - 썸네일 이미지 불러오기
            - 핵심 요약 등 strong 문구, 제보 문구 \' 삭제하기
    '''
    
    article =""
            
    origin_body = soup.find('article',class_='go_trans _article_content')
    photos = origin_body.find_all(class_="end_photo_org")
    
    if photos :
        thumbnail = ""
        for pt in photos:
            if thumbnail == "":
                thumbnail = pt.img['data-src']
            pt.extract() 
        news_info['thumbnail']=thumbnail
    else:
        news_info['thumbnail'] = 'default image'

    if origin_body:
        article = origin_body.get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        article = ' '.join(article.split())
        article = '. '.join([x.strip() for x in article.split('.')])
    else:
        article= None
        
    news_info['article']=article 
    # print("Build 함수 끝까지 왔다!!")
    return news_info


def get_newsinfo(item):
    '''
        output: 기사 3개 json 형태로 반환
    '''
    naver_url=item['link']
    origin_link=item['originallink'] #원본 기사 링크
    print(naver_url)
    
    try :
        #naver_url="https://n.news.naver.com/mnews/article/008/0004925361?sid=106"
        response = requests.get(naver_url)
        if (response.status_code == 200):
            soup = BeautifulSoup(response.text, 'html.parser')

            
            if (naver_url[-3:]=='106'):
                news_info = build_entertain(soup, origin_link)
            else:
                news_info = build_ordinary(soup, origin_link)
                
            if news_info == None or news_info['article'] == None:
                return False
            print(news_info)
            
            summary = json.loads(get_summary_article(news_info['article']))
            if summary == "" or sorted(summary.keys()) != ["summary"]:
                return False
            print(summary)            
            
            news_info['summary']=summary["summary"]
            news_info['origin_link'] = origin_link
            return news_info
        
    except Exception as e :
        print(f"Error Code in get_newsinfo: {response.status_code}")
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
    while cnt < news_cnt:
        
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
                print(raw['items'][0]['title'])
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


def create_news(keyword):
    try :        
        news = get_reponseUrl(keyword)
        # 기사가 없거나 오류가 나면 False를 반환할 것
        return news

    except Exception as e:
        #print(e)
        return Response({"message": "Missing keyword parameter"}, status=400)
    

class CreateNewsAPIView(generics.CreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    
    def create(self, request, *args, **kwargs):
        keyword_id = request.data['id']
        keywords = Keyword.objects.get(id=keyword_id).keywords
        print(keywords)
        
        keyword = ' '.join(keywords)
        results = create_news(keyword)
        
        if results == None :
            # 크롤링 실패
            return Response({"message" : "crawling failed"}, status=400)
        elif results == False:
            # 크롤링할 기사가 없을 때
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
