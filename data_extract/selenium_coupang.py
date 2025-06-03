import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent
import time
import random
from selenium.webdriver.common.keys import Keys

class ChromeDriver:
    def __init__(self) -> None:
        self.set_options()
        self.set_driver()
    
    def set_options(self) -> None:
        self.random_ua = UserAgent().random
        self.options = uc.ChromeOptions()
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-popup-blocking")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--incognito")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument('user-agent=' + self.random_ua)
    
    def set_driver(self) -> None:
        self.driver = uc.Chrome(options=self.options, enable_cdp_events=True, incognito=True)





def check_element(xP : str) -> bool:
    try:
        return chrome_driver.find_element(By.XPATH, xP).is_enabled()
    except NoSuchElementException:
        return False

def check_element_css(css : str) -> bool:
    try:
        return chrome_driver.find_element(By.CSS_SELECTOR, css).is_enabled()
    except NoSuchElementException:
        return False

try:
    chrome_driver = ChromeDriver().driver
    chrome_driver.get('https://www.coupang.com/np/search?component=&q=청소기')
    time.sleep(random.uniform(5, 6))
    actions = chrome_driver.find_element(By.CSS_SELECTOR, 'body')
    actions.send_keys(Keys.PAGE_DOWN)
    print(chrome_driver.title)
except Exception as e:
    print("url 접근 실패:", e)

try:
    productSelect = chrome_driver.find_element(By.XPATH, '/html/body/div[3]/section/form/div[2]/div[2]/ul/li[1]/a')
    chrome_driver.get(productSelect.get_attribute("href"))
    time.sleep(random.uniform(5, 6))
    
    # chrome_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # # chrome_driver.find_element(By.XPATH, '/html/body').send_keys(Keys.PAGE_DOWN)
    
    # time.sleep(random.uniform(4, 6))

    
    # # 상품평 클릭
    # xpath1 =  '/html/body/div[2]/div[1]/main/div[2]/div[3]/a[2]'
    # xpath2 =  '/html/body/div[2]/section/div[2]/div[2]/div[7]/ul[1]/li[2]'
    # if check_element(xpath1):
    #     print("xpath1 선택함")
    #     reviewBtn = chrome_driver.find_element(By.XPATH, xpath1)
    # elif check_element(xpath2):
    #     print("xpath2 선택함")
    #     reviewBtn = chrome_driver.find_element(By.XPATH, xpath2)
    # else:
    #     raise Exception("리뷰 버튼을 찾지 못했습니다.")
    # reviewBtn.click()
    # time.sleep(random.uniform(1, 2))

    ## 댓글 있는지 없는지 확인
    ## 
    ## 별점 / 날짜 / 리뷰 타이틀 / 리뷰 / 카테고리 리뷰
    ## btfTab 아니면 sdpReview
    for p in range(3,12):
        try:
            if check_element_css("#sdpReview article"):
                articles = chrome_driver.find_elements(By.CSS_SELECTOR, "#sdpReview article")
            else:
                articles = chrome_driver.find_elements(By.CSS_SELECTOR, "#btfTab article")

            for article in articles:
                    rating = article.find_element(By.CSS_SELECTOR, '[data-rating]').get_attribute("data-rating")
                    date = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__info__product-info__reg-date').text
                    content = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__review__content').text
                    print(f"⭐ {rating} / 📅 {date} / 내용: {content[:50]}")
        except Exception as e:
                print("리뷰 항목 추출 실패:", e)   

        # nextBtn = chrome_driver.find_element(By.XPATH,f'//*[@id="sdpReview"]/div/div[4]/div[2]/div/button[{p}]' )
        # nextBtn.click()
         
    # for p in range(3,12):
    #     for i in range(1, 10):
    #         # 리뷰 요소 탐색
    #         try:
    #             if check_element(f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/article[{i}]/div[1]/div[3]/div[1]/div'):
    #                 review_data_rating = chrome_driver.find_element(By.XPATH,f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/article[{i}]/div[1]/div[3]/div[1]/div').get_attribute('data-rating')
    #                 review_date = chrome_driver.find_element(By.XPATH, f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/article[{i}]/div[1]/div[3]/div[2]').text
    #                 xpath1 = chrome_driver.find_element(By.XPATH, f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/article[{i}]/div[1]/div[3]/div[2]')
    #                 xpath2 = chrome_driver.find_element(By.XPATH, f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/article[{i}]/div[4]/div')
    #                 #xpath3 = chrome_driver.find_element(By.XPATH, '#btfTab > ul.tab-contents > li.product-review.tab-contents__content > div > div.sdp-review__article.js_reviewArticleContainer > section.js_reviewArticleListContainer > article:nth-child(3) > div.sdp-review__article__list__headline')
    #             else:
    #                 review_data_rating = chrome_driver.find_element(By.XPATH,f'//*[@id="sdpReview"]/div/div[4]/div[2]/article[{i}]/div[1]/div[3]/div[1]/div').get_attribute('data-rating')
    #                 review_date = chrome_driver.find_element(By.XPATH,f'//*[@id="sdpReview"]/div/div[4]/div[2]/article[{i}]/div[1]/div[3]/div[2]').text
    #                 xpath1 = chrome_driver.find_element(By.XPATH, f'//*[@id="sdpReview"]/div/div[4]/div[2]/article[{i}]/div[3]')
    #                 xpath2 = chrome_driver.find_element(By.XPATH, f'//*[@id="sdpReview"]/div/div[4]/div[2]/article[{i}]/div[4]')
    #                 #xpath3 = chrome_driver.find_element(By.XPATH,f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/article[{i}]/div[4]/div')
    #         except Exception as e:
    #             print("에러 발생:", e)

    #         # if check_element_css(xpath1):
    #         #     review = chrome_driver.find_element(By.CSS_SELECTOR, xpath1)
    #         # elif check_element_css(xpath2):
    #         #     review = chrome_driver.find_element(By.CSS_SELECTOR, xpath2)
    #         # elif check_element_css(xpath3):
    #         #     review = chrome_driver.find_element(By.CSS_SELECTOR, xpath3)
    #         # else:
    #         #     raise Exception(" 리뷰를 찾지 못함")
    #         # reviewText = review.text
    #         # print("리뷰 내용:", reviewText[:20])
    #     # 리뷰 다음 페이지
    #     nextBtn = chrome_driver.find_element(By.XPATH,f'//*[@id="sdpReview"]/div/div[4]/div[2]/div/button[{p}]' )
    #     nextBtn.click()
    #     time.sleep(random.uniform(2, 3))
    #     print("다음 페이지로")
    #     break
except Exception as e:
    print("리뷰 추출 실패:", e)


#chrome_driver.quit()