from window_coupang_crawling import coupang_crawling, get_product_links
from multiprocessing import Pool, cpu_count, freeze_support


def run_multi_process(url_list: list) -> None:
    # CPU 절반 사용
    print("cpu개수: ",cpu_count())
    with Pool(processes=4) as pool:
        pool.map(coupang_crawling, url_list)



if __name__=="__main__":
    search_url = '청소기'
    max_link = 10
    freeze_support() 
    product_link_list = get_product_links(search_url, max_link)
    run_multi_process(product_link_list)
