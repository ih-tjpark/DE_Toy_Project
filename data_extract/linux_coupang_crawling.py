import re
import time
import random
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent

# 크롬 드라이버 셋팅
def setup_driver() -> uc.Chrome:
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--headless=new")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    random_ua = UserAgent().random
    options.add_argument('user-agent=' + random_ua)
    
    driver = uc.Chrome(#driver_executable_path='C:\\Users\\student\\AppData\\Roaming\\undetected_chromedriver\\undetected_chromedriver.exe',
                     options=options, enable_cdp_events=True, incognito=True, use_subprocess=False )
    return driver

# xpath로 element 있는지 체크
def check_element(xP: str, driver: uc.Chrome) -> bool:
    try:
        return driver.find_element(By.XPATH, xP).is_enabled()
    except:
        return False

# css로 element 있는지 체크
def check_element_css(css: str, driver: uc.Chrome) -> bool:
    try:
        return driver.find_element(By.CSS_SELECTOR, css).is_enabled()
    except:
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

# 리뷰 페이지 버튼 동작 컨트롤
def go_next_page(driver: uc.Chrome , page_num: int, review_id: str) -> bool:
    try:
        if review_id == "sdpReview":
            page_buttons = driver.find_element(By.XPATH, f'//*[@id="sdpReview"]/div/div[4]/div[2]/div/button[{page_num}]')
        else:
            page_buttons = driver.find_element(By.XPATH, f'//*[@id="btfTab"]/ul[2]/li[2]/div/div[6]/section[4]/div[3]/button[{page_num}]')
        
        # 처음 페이지 버튼을 누를 시 화면에 노출되야 클릭됨
        if page_num <= 3:
            driver.execute_script("arguments[0].scrollIntoView(true);", page_buttons)
            time.sleep(0.5)
            driver.execute_script("window.scrollBy(0, -150);")  # 살짝 위로 올려줌
            time.sleep(0.5)

        page_buttons.click()                               
        time.sleep(random.uniform(2,3))
        #print(f"[INFO] {product_code} 리뷰 {page_num-1} 페이지 이동")
        return True
    
    except:
        #print(f"[INFO] 리뷰 {page_num-1} 페이지 버튼 없음.")
        return False

# 리뷰 저장 
def save_reviews_to_parquet(reviews: list, product_code: str) -> None:
    df = pd.DataFrame(reviews)
    file_path = f"DE_Toy_Project/review_data_save/coupang_review_{product_code}.parquet"
    df.to_parquet(file_path, engine="pyarrow", index=False)
    #print(f"[INFO] {product_code} 리뷰가 parquet 파일로 저장되었습니다")

# 상품 기본 정보 추출
def get_product_info(driver: uc.Chrome) -> dict:
    try:
        product_dict = dict()
        
        # 상품 판매 제목
        title = driver.find_element(By.CSS_SELECTOR, '[data-sentry-component="ProductTitle"]').text
        product_dict['title'] = title

        # 카테고리 추출
        try:
            categorys = driver.find_elements(By.CSS_SELECTOR, '[data-sentry-component="Breadcrumb"] a')
            category_list = []
            for i in range(1, len(categorys)):
                category_list.append(categorys[i].text) 
                #product_dict[f'category{i}'] = categorys[i].text
                #print('category:',categorys[i].text)
            
            category_str = '[' + ', '.join(category_list) + ']'
        except NoSuchElementException as e:
            print("[ERROR] 카테고리 추출 실패:",e)
        
        # 상품명 추출
        try:
            name = driver.find_element(By.CSS_SELECTOR, '#itemBrief > table > tbody > tr:nth-child(1) > td:nth-child(2)').text
            product_dict['name'] = category_str + name
            #print('name:', name)
        except NoSuchElementException as e:
            name = ''
            print("[ERROR] 상품명 추출 실패:",e)
        
        # 상품 코드 추출
        product_code = get_product_code(driver.current_url)
        product_dict['product_code'] = product_code
        #print(product_code)

        # 별점 추출
        try:
            el = driver.find_element(By.CSS_SELECTOR, 'span.rating-star-num').get_attribute("style")
            star_rating = get_star_rating(el)
            product_dict['star_rating'] = star_rating
            #print(star_rating)
        except NoSuchElementException as e:
            star_rating = 0.0
            print("[INFO] 별점 없음")

        # 리뷰 수 추출
        try:
            el = driver.find_element(By.CSS_SELECTOR, 'span.rating-count-txt').text
            review_count = get_num_in_str(el)
            product_dict['review_count'] = review_count
            #print('review_count:',review_count)
        except NoSuchElementException as e:
            review_count = ''
            print("[INFO] 리뷰 수 없음")

        # 할인 전 가격 추출
        try:
            sales_price = driver.find_element(By.CSS_SELECTOR, 'div.price-amount.sales-price-amount').text
            product_dict['sales_price'] = sales_price
            #print('sales_price:',sales_price)
        except NoSuchElementException as e:
            sales_price = ''
            print("[INFO] 할인 전 가격 없음")
        # 할인 후 가격 추출
        try:
            final_price = driver.find_element(By.CSS_SELECTOR, 'div.price-amount.final-price-amount').text
            product_dict['final_price'] = final_price
            #print('final_price:',final_price)
        except NoSuchElementException as e:
            sales_price = ''
            print("[INFO] 할인 후 가격 없음")
        
        return product_dict
    except Exception as e:
        print(f"[ERROR] {product_code} 상품 기본 정보 추출 실패:",e)
        #driver.quit()
        return product_dict

# 상품 리뷰 추출
def get_product_review(driver: uc.Chrome, product_code):
    try:
        print(f"[INFO] {product_code}리뷰 크롤링을 시작합니다.")

        # 리뷰 추출
        if check_element_css("#sdpReview article", driver):
            review_id = "sdpReview"
        else:
            review_id = "btfTab"

        product_list = []
        for p in range(2,10):
            try:
                articles = driver.find_elements(By.CSS_SELECTOR, f"#{review_id} article")

                for article in articles:
                    review_rating = article.find_element(By.CSS_SELECTOR, '[data-rating]').get_attribute("data-rating")
                    review_date = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__info__product-info__reg-date').text
                    review_content = article.find_element(By.CSS_SELECTOR, 'div.sdp-review__article__list__review__content').text
                    #print(f" 별점:{rating} /  등록 날짜:{date} / 내용: {content[:50]}")
                
                product_list.append({
                    'product_code':product_code, 
                    'review_rating':review_rating, 
                    'review_date':review_date, 
                    'review_content':review_content
                    })
            except NoSuchElementException:
                print(f"[INFO] {product_code}리뷰가 없음:")
                continue
            except Exception as e:
                print(f"[INFO] {product_code}리뷰 추출 실패:", e)
                continue
            
            next_page_success = go_next_page(driver, p+1, review_id)
            if not next_page_success:
                break
        return product_list
    except:
        print(f"[ERROR] {product_code} 리뷰 추출 실패 :", e)
        return product_list

# 쿠팡 크롤링 전체 파이프라인 
def coupang_crawling(product_url: str) -> None:
    try:
        driver = setup_driver()
        driver.get(product_url)
        time.sleep(random.uniform(5, 6))

        # 상품 기본 정보 추출
        product_dict = get_product_info(driver)
        product_code = product_dict['product_code']
        
        # 기본 정보 DB 저장
        # save_to_db(product_dict)
        
        # 상품 리뷰 추출
        product_list = get_product_review(driver, product_code)
        
        # 리뷰 저장
        save_reviews_to_parquet(product_list, product_code)
        print(f'[INFO] {product_code} 리뷰 추출을 완료했습니다.')
    except Exception as e:
        print(f"[ERROR] {product_code} 에러 발생 :", e)
    finally:
        driver.quit()
        return

# 쿠팡 검색 후 상품 url 추출 
def get_product_links(keyword: str, max_links: int) -> list:

    driver = setup_driver()
    search_url = f"https://www.coupang.com/np/search?component=&q={keyword}"
    driver.get(search_url)
    time.sleep(random.uniform(3, 4))

    links = []
    duplicate_chk = set()
    print(driver.page_source)
    try:
        items = driver.find_elements(By.CSS_SELECTOR, '#product-list li')
    except NoSuchElementException as e:
        print("[INFO] 검색된 상품이 없습니다.:", e)
        return []
    
    try:
        for item in items:
            
            # 링크 주소
            href = item.find_element(By.TAG_NAME, 'a').get_attribute('href')

            # 상품 코드 추출
            product_code = get_product_code(href)

            # 중복 확인
            if product_code in duplicate_chk:
                continue
            else:
                duplicate_chk.add(product_code)
            # # 이미지 주소
            # img = item.find_element(By.TAG_NAME, 'img').get_attribute('src')
            # # 상품 제목
            # title = item.find_elements(By.TAG_NAME, 'div')[2].text
            # # 최종 가격
            # price = item.find_element(By.TAG_NAME, 'strong').text
            # # 원래 가격
            # try:
            #     origin_price = item.find_element(By.TAG_NAME, 'del').text
            # except NoSuchElementException:
            #     origin_price = 0
            # 상품 별점, 리뷰 수
            try:
                product_info = item.find_elements(By.CSS_SELECTOR, '[data-sentry-component="ProductRating"] span')
            except NoSuchElementException:
                star_rating = 0
                review_count = 0
            # try:
            #     star_rating = product_info[0].find_element(By.CSS_SELECTOR, 'div').text
            # except NoSuchElementException:
            #     star_rating = 0
            try:
                review_count = get_review_count(product_info[1].text)
            except:
                review_count = 0
            
            # 특정 개수 이상의 리뷰가 있는 상품만 가져오기
            if review_count >= 200:
                links.append(href)
            
            if len(links) >= max_links:
                break
        print(f"[INFO] {len(links)}개 상품 url 추출 완료.")        
        #driver.quit()
        return links
    except Exception as e:
        print("[ERROR] 상품 url 추출 실패.:", e)
        return []
    finally:
        driver.quit()


if __name__ == "__main__":
    keyword = '청소기'
    max_links = 10
    product_url_list = get_product_links(keyword, max_links)
    coupang_crawling(product_url_list[0])

