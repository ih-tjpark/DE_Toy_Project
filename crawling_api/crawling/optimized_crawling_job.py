import re
import os
import csv
import time
import random
import pandas as pd
import psycopg2
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from fake_useragent import UserAgent
from crawling.data_access import insert_product_info_to_db, save_reviews_to_local
import threading
from queue import Queue

# 최적화된 크롬 드라이버 셋팅
def setup_optimized_driver() -> uc.Chrome:
    options = uc.ChromeOptions()
    
    # 기본 최적화 설정
    options.add_argument("--headless")  # 헤드리스 모드 (GUI 제거)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # 성능 최적화
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # 이미지 로딩 차단
    options.add_argument("--disable-javascript")  # JavaScript 차단 (가능한 경우)
    
    # 리소스 로딩 최적화
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # 이미지 차단
        "profile.default_content_setting_values.notifications": 2,  # 알림 차단
        "profile.managed_default_content_settings.stylesheets": 2,  # CSS 차단
        "profile.managed_default_content_settings.cookies": 2,  # 쿠키 차단
        "profile.managed_default_content_settings.javascript": 1,  # JS 허용 (필요시)
        "profile.managed_default_content_settings.plugins": 1,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.media_stream": 2,
    }
    options.add_experimental_option("prefs", prefs)
    
    # 페이지 로드 전략
    options.page_load_strategy = 'eager'  # DOM 준비되면 바로 진행
    
    # User Agent 랜덤화
    random_ua = UserAgent().random
    options.add_argument(f'user-agent={random_ua}')
    
    # 메모리 최적화
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=4096")
    
    return uc.Chrome(options=options, enable_cdp_events=True)

# 스마트 대기 함수
def smart_wait_for_element(driver: uc.Chrome, locator_type: str, locator: str, timeout: int = 10):
    """동적 대기를 사용하여 요소가 나타날 때까지 기다림"""
    try:
        if locator_type.lower() == 'css':
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, locator))
            )
        elif locator_type.lower() == 'xpath':
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, locator))
            )
        return element
    except TimeoutException:
        return None

# xpath로 element 있는지 체크 (최적화)
def check_element_optimized(locator_type: str, locator: str, driver: uc.Chrome, timeout: int = 3) -> bool:
    try:
        if locator_type.lower() == 'css':
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, locator))
            )
        elif locator_type.lower() == 'xpath':
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, locator))
            )
        return True
    except TimeoutException:
        return False

# 상품 코드 추출
def get_product_code(url: str) -> str:
    prod_code = url.split("products/")[-1].split("?")[0]
    return prod_code

# 별점 추출
def get_star_rating(element: str) -> float: 
    rating_percent = float(re.sub(r'[^0-9]', '', element))
    avg_rating = round((rating_percent / 20), 2) 
    return avg_rating

# 문자열에서 숫자 추출
def get_num_in_str(element: str) -> int:
    num = int(re.sub(r'[^0-9]', '', element))
    return num

# 이미지 사이즈 변경
def replace_thumbnail_size(url: str) -> str:
    return re.sub(r'/remote/[^/]+/image', '/remote/292x292ex/image', url)

# 최적화된 리뷰 페이지 이동
def go_next_page_optimized(driver: uc.Chrome, page_num: int, review_id: str) -> bool:
    try:
        if review_id == "sdpReview":
            button_xpath = f'//*[@id="sdpReview"]/div/div[4]/div[2]/div/button[{page_num}]'
        else:
            button_xpath = f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/div[3]/button[{page_num}]'
        
        # 동적 대기로 버튼이 클릭 가능할 때까지 대기
        page_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, button_xpath))
        )
        
        # 스크롤 최적화
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", page_button)
        time.sleep(0.2)  # 최소 대기
        
        # 클릭
        driver.execute_script("arguments[0].click();", page_button)  # JavaScript 클릭으로 더 빠름
        
        # 페이지 로드 확인 (더 효율적)
        WebDriverWait(driver, 5).until(
            EC.staleness_of(page_button)  # 이전 요소가 사라질 때까지 대기
        )
        
        return True
    except (TimeoutException, Exception):
        return False

# 최적화된 상품 기본 정보 추출
def get_product_info_optimized(driver: uc.Chrome) -> dict:
    product_dict = {}
    
    try:
        # 모든 요소를 한 번에 찾기 위한 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.product-title'))
        )
        
        # 병렬로 요소들 찾기
        selectors = {
            'title': 'h1.product-title',
            'image_url': 'div.product-image img',
            'star_rating_element': 'span.rating-star-num',
            'review_count_element': 'span.rating-count-txt',
            'sales_price_element': 'div.price-amount.sales-price-amount',
            'final_price_element': 'div.price-amount.final-price-amount'
        }
        
        elements = {}
        for key, selector in selectors.items():
            try:
                elements[key] = driver.find_element(By.CSS_SELECTOR, selector)
            except NoSuchElementException:
                elements[key] = None
        
        # 기본 정보 추출
        if elements['title']:
            product_dict['title'] = elements['title'].text
        
        if elements['image_url']:
            image_url = elements['image_url'].get_attribute('src')
            product_dict['image_url'] = replace_thumbnail_size(image_url)
        
        # 카테고리 추출 (간소화)
        try:
            categorys = driver.find_elements(By.CSS_SELECTOR, 'ul.breadcrumb li')
            if categorys:
                category_list = [cat.text for cat in categorys[1:]]
                product_dict['tag'] = ','.join(category_list)
        except Exception:
            product_dict['tag'] = ""
        
        # 상품명 추출
        try:
            name_element = driver.find_element(By.CSS_SELECTOR, '#itemBrief > table > tbody > tr:nth-child(1) > td:nth-child(2)')
            name = name_element.text
            product_dict['name'] = product_dict['title'] if name.startswith("상품") else name
        except NoSuchElementException:
            product_dict['name'] = product_dict.get('title', '')
        
        # 상품 코드
        product_dict['product_code'] = int(get_product_code(driver.current_url))
        
        # 별점
        if elements['star_rating_element']:
            el = elements['star_rating_element'].get_attribute("style")
            product_dict['star_rating'] = get_star_rating(el)
        else:
            product_dict['star_rating'] = 0.0
        
        # 리뷰 수
        if elements['review_count_element']:
            product_dict['review_count'] = get_num_in_str(elements['review_count_element'].text)
        else:
            product_dict['review_count'] = 0
        
        # 가격 정보
        product_dict['sales_price'] = get_num_in_str(elements['sales_price_element'].text) if elements['sales_price_element'] else 0
        product_dict['final_price'] = get_num_in_str(elements['final_price_element'].text) if elements['final_price_element'] else 0
        
        return product_dict
        
    except Exception as e:
        print(f"[ERROR] 상품 기본 정보 추출 실패: {e}")
        return product_dict

# 최적화된 상품 리뷰 추출
def get_product_review_optimized(driver: uc.Chrome, product_code: str):
    try:
        print(f"[INFO] {product_code} 리뷰 크롤링 시작")
        
        # 리뷰 영역 확인
        review_id = "sdpReview" if check_element_optimized("css", "#sdpReview article", driver) else "btfTab"
        
        product_list = []
        max_pages = 10  # 최대 페이지 제한
        
        for page in range(1, max_pages + 1):
            try:
                # 현재 페이지 리뷰 추출
                articles = driver.find_elements(By.CSS_SELECTOR, f"#{review_id} article")
                
                if not articles:
                    print(f"[INFO] {product_code} 페이지 {page}: 리뷰 없음")
                    break
                
                # 배치로 리뷰 데이터 추출
                for article in articles:
                    try:
                        review_data = {
                            'product_code': product_code,
                            'review_rating': article.find_element(By.CSS_SELECTOR, '[data-rating]').get_attribute("data-rating"),
                            'review_date': article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__info__product-info__reg-date').text,
                            'review_content': article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__review__content').text
                        }
                        product_list.append(review_data)
                    except NoSuchElementException:
                        continue
                
                # 다음 페이지로 이동
                if page < max_pages:
                    if not go_next_page_optimized(driver, page + 1, review_id):
                        break
                        
            except Exception as e:
                print(f"[INFO] {product_code} 페이지 {page} 처리 중 오류: {e}")
                break
        
        print(f"[INFO] {product_code} 리뷰 {len(product_list)}개 추출 완료")
        return product_list
        
    except Exception as e:
        print(f"[ERROR] {product_code} 리뷰 추출 실패: {e}")
        return []

# 최적화된 크롤링 파이프라인
def coupang_crawling_optimized(args) -> None:
    driver = None
    try:
        product_url, job_id = args
        driver = setup_optimized_driver()
        
        # 페이지 로드 타임아웃 설정
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(5)
        
        driver.get(product_url)
        
        # 페이지 로드 확인
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.product-title'))
        )
        
        # 상품 기본 정보 추출
        product_dict = get_product_info_optimized(driver)
        product_code = str(product_dict['product_code'])
        
        # 상품 리뷰 추출
        product_list = get_product_review_optimized(driver, product_code)
        
        # 리뷰 저장
        save_reviews_to_local(product_list, product_code, job_id)
        
        print(f'[INFO] {product_code} 크롤링 완료 - 리뷰 {len(product_list)}개')
        
    except Exception as e:
        print(f"[ERROR] 크롤링 에러: {e}")
    finally:
        if driver:
            driver.quit()

# 최적화된 상품 링크 추출
def get_product_links_optimized(keyword: str, max_links: int) -> list:
    driver = None
    try:
        driver = setup_optimized_driver()
        search_url = f"https://www.coupang.com/np/search?component=&q={keyword}"
        
        driver.get(search_url)
        
        # 검색 결과 로드 대기
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#product-list li'))
        )
        
        items = driver.find_elements(By.CSS_SELECTOR, '#product-list li')
        
        links = []
        duplicate_chk = set()
        
        for item in items:
            try:
                href = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                product_code = get_product_code(href)
                
                if product_code in duplicate_chk:
                    continue
                duplicate_chk.add(product_code)
                
                # 리뷰 수 확인 (병렬 처리를 위해 간소화)
                try:
                    review_element = item.find_element(By.XPATH, './/span[contains(@class, "ProductRating_ratingCount")]')
                    review_count = get_num_in_str(review_element.text)
                    
                    if review_count >= 200:
                        links.append(href)
                        
                    if len(links) >= max_links:
                        break
                        
                except NoSuchElementException:
                    # 리뷰 수가 없는 상품은 스킵
                    continue
                    
            except Exception as e:
                continue
        
        print(f"[INFO] {len(links)}개 상품 URL 추출 완료")
        return links
        
    except Exception as e:
        print(f"[ERROR] 상품 링크 추출 실패: {e}")
        return []
    finally:
        if driver:
            driver.quit()