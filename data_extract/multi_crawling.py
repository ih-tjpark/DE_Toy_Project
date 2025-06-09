from selenium_coupang import get_coupang_review, get_product_links
from multiprocessing import Pool, cpu_count


def run_multi_process(url_list:list) -> None:
    # CPU 절반 사용
    print("cpu개수: ",cpu_count())
    with Pool(processes=cpu_count() // 2) as pool:
        pool.map(get_coupang_review, url_list)



if __name__=="__main__":
    search_url = '청소기'
    product_link_list = get_product_links()
    run_multi_process(product_link_list[:3])
