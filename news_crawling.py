from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import requests
import os
import json
import urllib
import pyautogui
import time


'''
    keyword 당 관련성 높은 기사 3개의 content, originalLink, summary
    - 프론트에서 필요한 것: 이미지, 신문사, 제목, 기사생성일
    - 백에서 필요한 것: 기사 원문 텍스트
'''
# 
load_dotenv()

client_id=os.getenv("X_NAVER_CLIENT_ID")
client_secret=os.getenv("X_NAVER_CLIENT_SECRET")

def get_summary(naver_url):
    summary = {}
    
    caps = DesiredCapabilities().CHROME
    caps['pageLoadStrategy'] = "none"
    
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    
    driver = webdriver.Chrome(options= options)
    driver.get(naver_url)
    time.sleep(0.5)

    sum_button = driver.find_element(By.ID, "_SUMMARY_BUTTON")
    sum_button.click()
    #wait(driver, 1).until(EC.find_element(By.ID, "_SUMMARY_BUTTON")).click()
    time.sleep(0.5)
    
    summary_body = driver.find_element(By.CLASS_NAME, '_contents_body._SUMMARY_CONTENT_BODY').text
    
    #print(summary_body)
    title = ""
    content = ""
    # 제목, 내용
    flag = 0 
    for line in summary_body:
        if (flag == 0):
            if (line == '\n'): flag = 1
            else : title += line
        else :
            if (line == '\n') : continue
            content += line
    summary['title']= title
    summary['content'] = content
    
    # print (summary )
    driver.quit()
    
    return summary


def build(soup, original_link, id, summary):
    '''
    필요한 데이터: 기사 원문, 기사 원본 링크, 네이버 뉴스 요약문
    '''
    news_info = {}
    news_info['id'] = id
    
    title = soup.select_one('h2.media_end_head_headline').span.get_text()
    news_info['title'] = title
    
    datestamp = soup.select('.media_end_head_info_datestamp_bunch')
    created_at = datestamp[0].span.get_text()
    news_info['created_at'] = created_at
    
    updated_at = ""
    if len(datestamp) == 2:
        updated_at = datestamp[1].span.get_text()
        news_info['updated_info'] = updated_at
    
    writer = soup.select_one('div.byline').span.get_text() # 기자 이름만? 이메일도 같이?
    news_info['writer'] = writer
    
    '''
        신문사 정보도 줘야 하나?
        newspaper = soup.select_one('a.media_and_head_top_logo')
    '''
    
    origin_body = soup.find('article',class_='go_trans _article_content')
    
    ''' 
        todo -> GPT한테 물어보기
            - 이미지 불러오기
            - 핵심 요약 등 strong 문구, 사진 캡션, 제보 문구 삭제 
            - '앞 \ 처리하기
    '''
    
    article =""
    for line in origin_body.get_text():
        if line == '\n': continue 
        article += line
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
                summary = get_summary(naver_url)
                news_info = build(soup, original_link, id, summary)
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
    display = 3
    
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
            response_body = response.read()
            raw_news = response_body.decode('utf-8')
            #print(json.loads(raw_news))
            return json.loads(raw_news)
        
    except Exception as e :
        print(f"Error Code: {rescode}")
        print(e)
        return None


'''
    todo: 프론트에 넘겨주는 방법 
'''    
if __name__=='__main__':
    
    keyword="칼"
    json_data = get_reponseUrl(keyword)
    
    if json_data == None:
        print("No Json Data")
    else:
        res = get_newsinfo(json_data)
        for n in res:
            print(n)
        

    