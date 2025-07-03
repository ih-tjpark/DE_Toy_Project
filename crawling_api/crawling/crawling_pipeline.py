from crawling.crawling_job import coupang_crawling, get_product_links
from multiprocessing import Pool, cpu_count, freeze_support
from crawling.data_access import upload_parquet_to_gcs
from crawling.request_to_transform_api import notify_spark_server
from datetime import datetime, timedelta
import time

def generate_job_id():
    now = datetime.now()
    return "job_" + now.strftime("%Y%m%d_%H%M%S")

def run_multi_process(url_list: list, job_id: str) -> None:
    # CPU 절반 사용
    #print("[INFO] multi processor 수: ",cpu_count()//2)

    job_ids = [job_id for _ in url_list]
    # with Pool(processes=cpu_count()//2) as pool:
    with Pool(6) as pool:
        pool.map(coupang_crawling, zip(url_list, job_ids))

# 전체 파이프라인
def crawling_run(keyword: str, max_link: int, is_crawling_running: bool ) -> None:
    try:
        freeze_support()
        start = time.time()
        job_id = generate_job_id()
        print(f"[INFO] 생성된 작업 ID: {job_id}")

        # 크롤링 멀티프로세싱
        product_link_list = get_product_links(keyword, max_link)
        run_multi_process(product_link_list, job_id)
        
        # gcs 파일 저장
        # try:
        #     storage_dir = upload_parquet_to_gcs(job_id)
        # except Exception as e:
        #     print('[ERROR] 리뷰 데이터 저장을 실패했습니다.: ', e)
            
        # spark server 작업 완료 알람
        #notify_spark_server(storage_dir)
        

        print('[INFO] 크롤링 요청 작업 완료')
        sec = time.time()-start
        times = str(timedelta(seconds=sec))

        print(f"[INFO] 크롤링 작업 완료. 소요 시간: {times}")
    except Exception as e:
        print(f'[ERROR] {job_id} 작업 중 에러가 발생했습니다: ',e)
    finally:
        is_crawling_running.value = False

# if __name__=="__main__":
#     search_url = '청소기'
#     max_link = 10
#     freeze_support()
#     product_link_list = get_product_links(search_url, max_link)
#     run_multi_process(product_link_list)
