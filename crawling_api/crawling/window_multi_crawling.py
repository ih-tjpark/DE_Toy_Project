from crawling.window_coupang_crawling import coupang_crawling, get_product_links
from multiprocessing import Pool, cpu_count, freeze_support


def run_multi_process(url_list: list) -> None:
    # CPU 절반 사용
    print("[INFO] multi processor 수: ",cpu_count()//2)
    with Pool(processes=cpu_count()//2) as pool:
        pool.map(coupang_crawling, url_list)

def crawling_start(product_name: str, max_link: int, shared_dict: dict) -> None:
    freeze_support()
    product_link_list = get_product_links(product_name, max_link)
    run_multi_process(product_link_list)

# if __name__=="__main__":
#     search_url = '청소기'
#     max_link = 10
#     freeze_support()
#     product_link_list = get_product_links(search_url, max_link)
#     run_multi_process(product_link_list)
