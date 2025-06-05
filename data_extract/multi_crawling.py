from selenium_coupang import coupang_crawling
from multiprocessing import Pool, cpu_count

def run_multi_process(url_list:list) -> None:
    # CPU 절반 사용
    with Pool(processes=cpu_count() // 2) as pool:
        results = pool.map(coupang_crawling())



if __name__=="__main__":
    