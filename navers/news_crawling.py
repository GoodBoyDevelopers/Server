from dotenv import load_dotenv
from bs4 import BeautifulSoup

import bs4.element
import requests
import os
import json
import urllib

import news_summary

'''
    keyword 당 관련성 높은 기사 3개의 content, originalLink, summary
    - 프론트에서 필요한 것: 이미지, 신문사, 제목, 기사생성일
    - 백에서 필요한 것: 기사 원문 텍스트
'''

load_dotenv()

client_id=os.getenv("X_NAVER_CLIENT_ID")
client_secret=os.getenv("X_NAVER_CLIENT_SECRET")
display = 3

'''
    todo: 예외처리
    - 클릭 버튼이 없을 때
'''

def build(soup, original_link, id, summary):
    '''
    필요한 데이터: 기사 원문, 기사 원본 링크, 네이버 뉴스 요약문
    '''
    news_info = {}
    news_info['id'] = id
    
    title = soup.select_one('h2.media_end_head_headline').span.get_text()
    news_info['title'] = title.replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\'", "'").replace("\"",'"')
    
    
    datestamp = soup.select('.media_end_head_info_datestamp_bunch')
    created_at = datestamp[0].span.get_text()
    news_info['created_at'] = created_at
    
    updated_at = ""
    if len(datestamp) == 2:
        updated_at = datestamp[1].span.get_text()
        news_info['updated_at'] = updated_at
    
    writer = soup.select_one('div.media_end_head_journalist').em.get_text().strip() # 기자 이름만? 이메일도 같이?
    news_info['writer'] = writer
    
    
    # 신문사 정보
    # newspaper = soup.img.attrs.get('alt') if soup.img else soup.a.text.replace("\n", "").replace("\t","").replace("\r","")
    # newspaper_imag = soup.img.attrs.get('src') if soup.img else 'default image'
    
    ''' 
        todo -> GPT한테 물어보기
            - 이미지 불러오기
            - 핵심 요약 등 strong 문구, 사진 캡션, 제보 문구 삭제 
            - '앞 \ 처리하기
            - 신문사 정보 넘겨주기 - 썸네일로, 문구로
    '''
    
    article =""
            
    origin_body = soup.find('article',class_='go_trans _article_content')
    photos = origin_body.find_all(class_="end_photo_org")
    for pt in photos:
        pt.extract() 


    article = origin_body.get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"')
    article = ' '.join(article.split())
    article = '. '.join([x.strip() for x in article.split('.')])
    
    news_info['article']=article
    news_info['summary']=summary
    
    return news_info


def get_newsinfo(json_data):
    '''
        원본 url -> 원본 기사 추출
    '''
    id = 1
    news = []
    
    for item in json_data['items']:
        
        naver_url=item['link']
        original_link=item['originallink'] #원본 기사 링크
        print(naver_url)
        
        try : 
            response = requests.get(naver_url)
            if (response.status_code == 200):
                print("Success")
                soup = BeautifulSoup(response.text, 'html.parser')
                summary = 'no summary'
                #summary = news_summary.get_summary_dynamic(naver_url)
                news_info = build(soup, original_link, id, summary)
                summary = news_summary.get_summary_clova(news_info['title'], news_info['article'])

                news_info['summary']=summary
                id += 1
                news.append(news_info)
        except Exception as e :
            print(f"Error Code: {response.status_code}")
            print(e)
            return
    return news
        

def get_reponseUrl(keyword):
    '''
        naver api -> 키워드 검색 시 상위 3개의 기사 추출
    '''    
    encText=urllib.parse.quote(keyword)
    
    
    query = f"?query={encText}&start=1&display={display}&sort=sim"
    url = "https://openapi.naver.com/v1/search/news" + query
    
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    
    '''
        todo: 요약 불가능한 기사 처리
        -> 칼럼이나 사설 등 오피니언 기사, 동영상 기사, 본문이 외국어로 구성된 기사, 본문 기사가 300자 이하 혹은 3문장 이하인 기사 등에는 자동 요약 기능을 지원하지 않습니다.
    '''
    try:
        response = urllib.request.urlopen(request)
        print(response)
        rescode = response.getcode()
        
        if rescode == 200:
            print("GET REPONSE")    
            response_body = response.read().decode('utf-8')
            raw_news = json.loads(response_body)
            if (raw_news['total']==0):
                print("No News")
                return
            return raw_news
        
    except Exception as e :
        print(f"Error Code: {rescode}")
        print(e)
        return None


'''
    todo: 프론트에 넘겨주는 방법 
'''    
if __name__=='__main__':
    
    keyword = "잼버리"
    try :
        json_data = get_reponseUrl(keyword)
    

        res = get_newsinfo(json_data)
        print(res)
    except Exception as e:
        
        print(e)

    