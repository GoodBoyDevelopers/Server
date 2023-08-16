from bs4 import BeautifulSoup

def build_entertain(soup, origin_link):
    news_info = {}

    # 기사 전체 html
    try :
        origin_body = soup.select_one('div.end_body_wrp')
    except Exception as e:
        print(e)
        return False

    # 기사 내용
    try :
        article = origin_body.get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        article = ' '.join(article.split())
        article = '. '.join([x.strip() for x in article.split('.')])
        news_info['article']=article 
    except Exception as e:
        print(e)
        return False

    # 여기 아래는 없어도 됨
    # 제목
    try :
        title = soup.select_one("h2.end_tit").get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        news_info['title'] = title
    except Exception as e:
        print(e)
        news_info['title'] = "title Unknown"

    # 생성일
    try :
        created_at = soup.select_one('span.author')
        news_info['created_at'] = created_at.em.get_text()
    except Exception as e :
        print(e)
        news_info['created_at'] = 'date Unkown'

    # 기자
    try :
        writer = soup.select_one("div.byline")
        news_info['writer'] = writer.get_text().strip().split()[0] 
    except Exception as e :
        news_info['writer'] = 'Anonymous'

    # 신문사 정보
    try :
        name = soup.find('a', class_="press_logo").img['alt']
        news_info['newspaper_name'] = name
    except Exception as e :
        print(e)
        news_info['newspaper_name'] = 'newspaper unknown'

    # 뉴스 썸네일
    try :    
        img = soup.find('a', class_="press_logo").img['src']
        news_info['newspaper_thumbnail'] =img
    except Exception as e :
        print(e)
        news_info['newspaper_thumbnail'] = 'http://via.placeholder.com/32x32'

    # 원본 기사 링크
    news_info['origin_link'] = origin_link

    # 그냥 썸네일
    try :
        thumbnail = ""
        photos = origin_body.find_all(class_="end_photo_org")
        for pt in photos:
            if thumbnail == "":
                thumbnail = pt.img['src']
            pt.extract() 
        if thumbnail == "" :
            thumbnail = 'http://via.placeholder.com/32x32'
        news_info['thumbnail']=thumbnail
    except Exception as e:
        news_info['thumbnail'] = 'http://via.placeholder.com/32x32'


    return news_info

def build_sports(soup, origin_link):
    news_info = {}
    # 기사 본문
    try:
        origin_body = soup.find('div', class_="news_end font1 size3")
    except Exception as e:
        print(e)
        
    article = ""
    try:
        article = origin_body.get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        article = ' '.join(article.split())
        article = '. '.join([x.strip() for x in article.split('.')])
        news_info['article'] = article
    except Exception as e:
        print(e)
        return False
    
    # 제목
    try:
        title = soup.select_one("h4.title").get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        news_info['title'] = title
    except Exception as e: 
        print(e)
        news_info['title'] = "title unknown"
        
    # 생성일
    try:
        created_at = soup.select_one("div.info")
        news_info['created_at'] = created_at.span.get_text()[5:]
    except Exception as e:
        print(e)
        news_info['created_at'] = 'date unknown'

    #작성자
    try:
        writer = soup.select_one("p.byline")
        writer.get_text().strip().split()[0]  
    except Exception as e :
        news_info['writer'] = 'anonymous'
        print(e)
    
    # 원본 기사 링크
    news_info['origin_link'] = origin_link
    
    # 신문사 정보
    try : 
        name = soup.find('a', class_="link").img['alt']
        news_info['newspaper_name'] = name
    except Exception as e:
        print(e)
        news_info['newspaper_name'] = 'newspaper unknown'
        
    # 뉴스 썸네일
    try :    
        img = soup.find('a', class_="link").img['src']
        news_info['newspaper_thumbnail'] =img
    except Exception as e :
        print(e)
        news_info['newspaper_thumbnail'] = 'http://via.placeholder.com/32x32'
        
        # 그냥 썸네일
    try :
        photos = origin_body.find_all(class_="end_photo_org")
        thumbnail = ""
        for pt in photos:
            if thumbnail == "":
                thumbnail = pt.img['src']
            pt.extract() 
        news_info['thumbnail'] = thumbnail
    except Exception as e :
        print(e)
        news_info['thumbnail'] = "http://via.placeholder.com/32x32" 
        
    return news_info
    
def build_ordinary(soup, origin_link):
    '''
        output: 기사 title, creatd_at, (updated_at), writer, article, newspaper(name, img), thumbnail
    '''
    news_info = {}

    # 기사 본문
    try :
        origin_body = soup.find('article',class_='go_trans _article_content')
    except Exception as e :
        print(e)
        #origin_body = ""
        return False

    # 기사
    article =""
    try :
        article = origin_body.get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        article = ' '.join(article.split())
        article = '. '.join([x.strip() for x in article.split('.')])
        news_info['article'] = article
    except Exception as e:
        print(e)
        #article= ""
        return False
    
    # 여기 아래는 없어도 됨
    # 제목
    try :
        title = soup.select_one('h2.media_end_head_headline').get_text().replace('\n', ' ').replace("\t"," ").replace("\r"," ").replace("\\'", "'").replace('\\"','"').replace("\\", "")
        news_info['title'] = title
    except Exception as e: 
        print(e)
        news_info['title'] = "title unknown"

    # 생성일
    try :
        created_at = soup.select_one('div.media_end_head_info_datestamp_bunch')
        news_info['created_at'] = created_at.span.get_text()
    except Exception as e :
        print(e)
        news_info['created_at'] = 'date unknown'

    #작성자
    try :
        writer  = soup.select_one('div.media_end_head_journalist')
        news_info['writer'] = writer.get_text().strip().split()[0]  
    except Exception as e :
        news_info['writer'] = 'anonymous'
        print(e)

    # 원본 기사 링크
    news_info['origin_link'] = origin_link
    
    # 신문사 정보
    try : 
        name = soup.find('a', class_="media_end_head_top_logo").img['title']
        news_info['newspaper_name'] = name
    except Exception as e:
        print(e)
        news_info['newspaper_name'] = 'newspaper unknown'

    # 기사 썸네일
    try :
        img = soup.find('a', class_="media_end_head_top_logo").img['src']
        news_info['newspaper_thumbnail'] =img
    except Exception as e :
        print(e)
        news_info['newspaper_thumbnail'] = 'http://via.placeholder.com/32x32'

    # 그냥 썸네일
    try :
        photos = origin_body.find_all(class_="end_photo_org")
        thumbnail = ""
        for pt in photos:
            if thumbnail == "":
                thumbnail = pt.img['data-src']
            pt.extract() 
        news_info['thumbnail'] = thumbnail
    except Exception as e :
        print(e)
        news_info['thumbnail'] = "http://via.placeholder.com/32x32" 

    return news_info


