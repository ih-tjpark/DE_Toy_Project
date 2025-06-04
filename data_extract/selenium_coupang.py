import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent



def setup_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    random_ua = UserAgent().random
    options.add_argument('user-agent=' + random_ua)

    driver = uc.Chrome(options=options, enable_cdp_events=True, incognito=True)
    return driver

def check_element(xP : str, driver) -> bool:
    try:
        return driver.find_element(By.XPATH, xP).is_enabled()
    except NoSuchElementException:
        return False

def check_element_css(css : str, driver) -> bool:
    try:
        return driver.find_element(By.CSS_SELECTOR, css).is_enabled()
    except NoSuchElementException:
        return False

def go_next_page(driver , page_num:int, review_id:str) -> bool:
    try:
        if review_id == "sdpReview":
            page_buttons = driver.find_element(By.XPATH, f'//*[@id="sdpReview"]/div/div[4]/div[2]/div/button[{page_num}]')
        else:
            page_buttons = driver.find_element(By.XPATH, f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/div[3]/button[{page_num}]')
        
        if page_num <= 3:
            driver.execute_script("arguments[0].scrollIntoView(true);", page_buttons)
            time.sleep(0.5)
            driver.execute_script("window.scrollBy(0, -150);")  # 살짝 위로 올려줌
            time.sleep(0.5)

        page_buttons.click()                               
        time.sleep(random.uniform(2,3))
        print(f"[INFO] {page_num-1} 페이지 이동")
        return True
    
    except NoSuchElementException:
        print(f"[INFO] {page_num-1} 페이지 버튼 없음.")
        return False
    
    except Exception as e:
        print(f"[ERROR] 페이지 {page_num-1} 이동 실패:", e)
        return False

def coupang_crawling(product_url, driver):
    try:
        chrome_driver = driver
        chrome_driver.get(product_url)
        time.sleep(random.uniform(3, 4))
        #actions = chrome_driver.find_element(By.CSS_SELECTOR, 'body')
        #actions.send_keys(Keys.PAGE_DOWN)
        print("url 접근 성공")
    except Exception as e:
        print("url 접근 실패:", e)

    try:
        productSelect = chrome_driver.find_element(By.XPATH, '/html/body/div[3]/section/form/div[2]/div[2]/ul/li[1]/a')
        chrome_driver.get(productSelect.get_attribute("href"))
        time.sleep(random.uniform(5, 6))
        
        chrome_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        if check_element_css("#sdpReview article", chrome_driver):
            review_id = "sdpReview"
        else:
            review_id = "btfTab"

        for p in range(2,5):
            try:
                articles = chrome_driver.find_elements(By.CSS_SELECTOR, f"#{review_id} article")

                for article in articles:
                        rating = article.find_element(By.CSS_SELECTOR, '[data-rating]').get_attribute("data-rating")
                        date = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__info__product-info__reg-date').text
                        content = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__review__content').text
                        print(f"⭐ {rating} / 📅 {date} / 내용: {content[:50]}")
            except Exception as e:
                    print("리뷰 항목 추출 실패:", e) 
            
            next_page_success = go_next_page(chrome_driver, p+1, review_id)
            if not next_page_success:
                break
        
    except Exception as e:
        print("리뷰 추출 실패:", e)
        


if __name__ == "__main__":
    driver = setup_driver()
    product_url = 'https://www.coupang.com/np/search?component=&q=청소기'
    coupang_crawling(product_url, driver)

#chrome_driver.quit()