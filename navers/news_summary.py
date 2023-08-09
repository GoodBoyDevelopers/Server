from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from dotenv import load_dotenv

import pyautogui
import time
import os
import json
import requests

'''
    todo: gensim summary
'''

load_dotenv()

api_key_id = os.getenv('X_NCP_APIGW_API_KEY_ID')
api_key = os.getenv('X_NCP_APIGW_API_KEY') 

def get_summary_dynamic(naver_url):
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
            raw_news=raw_news.replace('\\', '').replace('\t','').replace('\r','').replace('\n',' ')
            return raw_news
    except Exception as e :
        print(f"Summary Error Code: {rescode}")
        print(e)
        return None
    
def get_summary_gensim(title, article):
    pass