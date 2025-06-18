from crawling.window_coupang_crawling import coupang_crawling, get_product_links
from multiprocessing import Pool, cpu_count, freeze_support
from crawling.save_data import upload_parquet_to_gcs
import datetime

def generate_job_id():
    now = datetime.now()
    return "job_" + now.strftime("%Y%m%d_%H%M%S")

def run_multi_process(url_list: list, job_id: str) -> None:
    # CPU 절반 사용
    print("[INFO] multi processor 수: ",cpu_count()//2)

    args = [(url, job_id) for url in url_list]
    with Pool(processes=cpu_count()//2) as pool:
        pool.map(coupang_crawling, args)

def crawling_job(keyword: str, max_link: int, is_crawling_running: bool ) -> None:
    try:
        freeze_support()
        job_id = generate_job_id()
        print(f"[INFO] 생성된 작업 ID: {job_id}")

        product_link_list = get_product_links(keyword, max_link)
        run_multi_process(product_link_list, job_id)
        
        upload_parquet_to_gcs(job_id)
        print('[INFO] 크롤링 요청 작업 완료')
    except Exception as e:
        print('[ERROR] 에러가 발생했습니다: ',e)
    finally:
        is_crawling_running.value = False

# if __name__=="__main__":
#     search_url = '청소기'
#     max_link = 10
#     freeze_support()
#     product_link_list = get_product_links(search_url, max_link)
#     run_multi_process(product_link_list)
