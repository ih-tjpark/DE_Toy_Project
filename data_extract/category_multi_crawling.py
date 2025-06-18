from window_coupang_crawling import coupang_crawling, get_product_links
from multiprocessing import Pool, cpu_count, freeze_support
from info_data_merge import data_merge

def run_multi_process(url_list: list) -> None:
    # CPU 절반 사용
    print("[INFO] cpu 사용 개수: ",cpu_count()//2)
    with Pool(processes=cpu_count()//2) as pool:
        pool.map(coupang_crawling, url_list)



if __name__=="__main__":
    keyword = input("크롤링할 카테고리를 입력하세요: ")
    max_link = 3
    freeze_support()
    product_link_list = get_product_links(keyword, max_link)
    run_multi_process(product_link_list)
    data_merge(keyword)
    print("카테고리 데이터 병합 완료")
    
