from bs4 import BeautifulSoup
from dotenv import load_dotenv
import json
import os
import requests
import urllib

from django.http import JsonResponse


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
display = 2


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
        rescode = response.status_code
        if rescode == 200:
            print("GET REPONSE FROM CLOVA")    
            response_body = json.loads(response.text)
            raw_news = response_body["summary"]
            raw_news = raw_news.replace('\\', '').replace('\t',' ').replace('\r',' ').replace('\n',' ').replace("\\'", "'").replace('\\"','"')
            news = ' '.join(raw_news.split())
            return news
    except Exception as e :
        print(f"Summary Error Code: {rescode}")
        print(e)
        return None


def build(soup, id, origin_link):
    '''
        output: 기사 title, creatd_at, (updated_at), writer, article, newspaper(name, img), thumbnail
    '''
    news_info = {}
    news_info['id'] = id
    
    title = soup.select_one('h2.media_end_head_headline').span.get_text()
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

    article = origin_body.get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"')
    article = ' '.join(article.split())
    article = '. '.join([x.strip() for x in article.split('.')])
    
    news_info['article']=article
    
    return news_info


def get_newsinfo(json_data):
    '''
        output: 기사 3개 json 형태로 반환
    '''
    id = 1
    news = []
    
    for item in json_data['items']:
        
        naver_url=item['link']
        origin_link=item['originallink'] #원본 기사 링크
        print(naver_url)
        
        try : 
            response = requests.get(naver_url)
            if (response.status_code == 200):
                print("Success")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                news_info = build(soup, id, origin_link)
                summary =get_summary_clova(news_info['title'], news_info['article'])
                #summary = get_summary_dynamic(naver_url)
                
                news_info['summary']=summary
                news_info['origin_link'] = origin_link
                id += 1
                news.append(news_info)
                
        except Exception as e :
            print(f"Error Code: {response.status_code}")
            print(e)
            return
    return news
        

def get_reponseUrl(keyword):
    '''
        ouput : 키워드 검색 시 상위 3개의 기사 추출 (naver api  이용)
    '''    
    encText=urllib.parse.quote(keyword)
    
    
    query = f"?query={encText}&start=1&display={display}&sort=sim"
    url = "https://openapi.naver.com/v1/search/news" + query
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        response = urllib.request.urlopen(request)
        print(response)
        rescode = response.getcode()
        
        if rescode == 200:
            print("GET REPONSE")    
            response_body = response.read().decode('utf-8')
            raw_news = json.loads(response_body)
            if (raw_news['total'] == 0):
                print("No News")
                return JsonResponse({"message": "No News"}, status=204)
            return raw_news
        
    except Exception as e :
        print(f"Error Code:")
        print(e)
        return None


'''
    todo: 프론트에 넘겨주는 방법 
    DB에서 keyword 가져와서 webhook으로 바로 네이버 기사 결과를 프론트에 넘겨주기
    비교해주는 함수 호출하기
'''    
def naver_news(keywords):
    keyword = ' '.join(keywords)
    print(keyword)
    try :
        json_data = get_reponseUrl(keyword)
        results = get_newsinfo(json_data)
        return results
    except Exception as e:
        print(e)
        print("No Keyword")
        
    

