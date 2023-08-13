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


def get_summary_clova(title, article):
    url = 'https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize'

    headers = {
        "X-NCP-APIGW-API-KEY-ID": api_key_id,
        "X-NCP-APIGW-API-KEY":api_key,
        "Content-Type": "application/json"
    }
    
    data = {}
    document = {
            "title": title,
            "content": article
    }
    option = {
        "language" : "ko",
        "model": "news",
        "tone": "0",
        "summaryCount" : "3"
    }    
    
    data['document'] = document
    data['option'] = option

    try :
        response = requests.post(url, data = json.dumps(data), headers=headers)
        if response.status_code == 200:
            print("GET REPONSE FROM CLOVA")
            response_body = json.loads(response.text)
            raw_news = response_body["summary"]
            raw_news = raw_news.replace('\\', '').replace('\t',' ').replace('\r',' ').replace('\n',' ').replace("\\'", "'").replace('\\"','"')
            news = ' '.join(raw_news.split())
            
            return news
    except Exception as e :
        print(f"Summary Error Code: {response.status_code}")
        print(e)
        return None


def build(soup, origin_link):
    '''
        output: 기사 title, creatd_at, (updated_at), writer, article, newspaper(name, img), thumbnail
    '''
    news_info = {}
    
    title = soup.select_one('h2.media_end_head_headline').span.get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
    news_info['title'] = title.replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace("\\'","'")
    
    
    datestamp = soup.select('.media_end_head_info_datestamp_bunch')
    created_at = datestamp[0].span.get_text()
    news_info['created_at'] = created_at
    
    writer = soup.select_one('div.media_end_head_journalist').em.get_text().strip().split() 
    news_info['writer'] = writer[0]
    
    news_info['origin_link'] = origin_link
    
    # 신문사 정보
    name= soup.find('a', class_="media_end_head_top_logo").img['title'] 
    name = name if name else '신문사 정보'
    
    img = soup.find('a', class_="media_end_head_top_logo").img['src'] 
    img = img if img else 'default image'
    news_info['newspaper_name'] = name
    news_info['newspaper_thumbnail'] =img
    
    ''' 
        todo 
            - 썸네일 이미지 불러오기
            - 핵심 요약 등 strong 문구, 제보 문구 \' 삭제하기
    '''
    
    article =""
            
    origin_body = soup.find('article',class_='go_trans _article_content')
    photos = origin_body.find_all(class_="end_photo_org")
    thumbnail = ""
    for pt in photos:
        if thumbnail == "":
            thumbnail = pt.img['data-src']
        pt.extract() 
    news_info['thumbnail']=thumbnail

    article = origin_body.get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
    article = ' '.join(article.split())
    article = '. '.join([x.strip() for x in article.split('.')])
    
    news_info['article']=article
    
    return news_info


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
            print("Success")
            soup = BeautifulSoup(response.text, 'html.parser')
            news_info = build(soup, origin_link)
            summary =get_summary_clova(news_info['title'], news_info['article'])
            if (summary == None):
                return 1
            
            news_info['summary']=summary
            news_info['origin_link'] = origin_link
            return news_info
        
    except Exception as e :
        print(f"Error Code: {response.status_code}")
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
                print("GET REPONSE")
                response_body = response.read().decode('utf-8')
                raw = json.loads(response_body)
                
                if (raw['total'] == 0):
                    print("No News")
                    return JsonResponse({"message": "No News"}, status=204)
                else:
                    # naver news 링크 없는 경우 
                    naver_url = "https://n.news.naver.com/mnews/article/"
                    link =  raw["items"][0]["link"]
                    
                    if re.match(naver_url, link):
                        news_info = get_newsinfo(raw["items"][0])
                        if news_info != 1:
                            print(news_info)
                            cnt += 1
                            news.append(news_info)
                            
                    start += 1
        except Exception as e :
            rescode = response.getcode()
            print(f"Error Code: {rescode}")
            print(e)
            return None
    return news


def create_news(keyword):
    try :        
        news = get_reponseUrl(keyword)
        return news

    except Exception as e:
        print(e)
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
        
        for res in results:
            res['keywords']=keyword_id
            serializer = self.get_serializer(data=res)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
        headers = self.get_success_headers(serializer.data)
        data = Article.objects.filter(keywords=keyword_id)
        serialized_data = self.get_serializer(data, many=True).data
        return Response(serialized_data, status=status.HTTP_201_CREATED, headers=headers)
