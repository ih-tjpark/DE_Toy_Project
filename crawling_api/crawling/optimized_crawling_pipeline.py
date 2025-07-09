from crawling.optimized_crawling_job import (
    coupang_crawling_optimized, 
    get_product_links_optimized
)
from multiprocessing import Pool, cpu_count, freeze_support
from concurrent.futures import ProcessPoolExecutor, as_completed
from crawling.data_access import upload_parquet_to_gcs
from crawling.request_to_transform_api import notify_spark_server
from datetime import datetime, timedelta
import time
import asyncio
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_job_id():
    now = datetime.now()
    return "job_" + now.strftime("%Y%m%d_%H%M%S")

def run_optimized_multi_process(url_list: list, job_id: str) -> None:
    """최적화된 멀티프로세싱 실행"""
    if not url_list:
        logger.warning("처리할 URL이 없습니다.")
        return
    
    # 최적의 프로세스 수 계산 (CPU 코어의 80% 사용)
    optimal_processes = max(1, min(len(url_list), int(cpu_count() * 0.8)))
    logger.info(f"프로세스 수: {optimal_processes}, 처리 대상: {len(url_list)}개 상품")
    
    job_ids = [job_id for _ in url_list]
    
    # ProcessPoolExecutor 사용으로 더 효율적인 병렬 처리
    start_time = time.time()
    completed_count = 0
    failed_count = 0
    
    try:
        with ProcessPoolExecutor(max_workers=optimal_processes) as executor:
            # 모든 작업 제출
            future_to_url = {
                executor.submit(coupang_crawling_optimized, (url, job_id)): url 
                for url, job_id in zip(url_list, job_ids)
            }
            
            # 완료된 작업들 처리
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    future.result()  # 결과 가져오기 (예외 발생 시 여기서 처리)
                    completed_count += 1
                    
                    # 진행률 출력
                    if completed_count % 5 == 0 or completed_count == len(url_list):
                        elapsed = time.time() - start_time
                        progress = (completed_count / len(url_list)) * 100
                        logger.info(f"진행률: {progress:.1f}% ({completed_count}/{len(url_list)}) - "
                                  f"소요시간: {elapsed:.1f}초")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"크롤링 실패 - URL: {url}, 에러: {str(e)}")
    
    except Exception as e:
        logger.error(f"멀티프로세싱 실행 중 오류: {e}")
    
    finally:
        total_time = time.time() - start_time
        logger.info(f"처리 완료 - 성공: {completed_count}, 실패: {failed_count}, "
                   f"총 소요시간: {total_time:.1f}초")

def run_batch_processing(url_list: list, job_id: str, batch_size: int = 10) -> None:
    """배치 단위로 처리하여 메모리 사용량 최적화"""
    total_batches = (len(url_list) + batch_size - 1) // batch_size
    logger.info(f"배치 처리 시작 - 총 {total_batches}개 배치, 배치 크기: {batch_size}")
    
    for i in range(0, len(url_list), batch_size):
        batch_urls = url_list[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        logger.info(f"배치 {batch_num}/{total_batches} 처리 중... ({len(batch_urls)}개 상품)")
        
        try:
            run_optimized_multi_process(batch_urls, job_id)
            
            # 배치 간 쿨다운 (서버 부하 방지)
            if batch_num < total_batches:
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"배치 {batch_num} 처리 중 오류: {e}")
            continue

async def async_crawling_run(keyword: str, max_link: int, is_crawling_running) -> None:
    """비동기 크롤링 실행 (향후 확장용)"""
    # 현재는 동기 함수들을 래핑만 함
    # 향후 비동기 selenium 라이브러리 사용 시 확장 가능
    loop = asyncio.get_event_loop()
    
    # 링크 추출을 별도 스레드에서 실행
    product_links = await loop.run_in_executor(
        None, get_product_links_optimized, keyword, max_link
    )
    
    return product_links

def crawling_run_optimized(keyword: str, max_link: int, is_crawling_running, 
                          use_batch_processing: bool = True, batch_size: int = 15) -> None:
    """최적화된 전체 크롤링 파이프라인"""
    try:
        freeze_support()
        start_time = time.time()
        job_id = generate_job_id()
        
        logger.info(f"크롤링 작업 시작 - Job ID: {job_id}")
        logger.info(f"검색 키워드: '{keyword}', 최대 링크 수: {max_link}")
        
        # 1단계: 상품 링크 추출
        logger.info("1단계: 상품 링크 추출 중...")
        link_start_time = time.time()
        
        product_link_list = get_product_links_optimized(keyword, max_link)
        
        if not product_link_list:
            logger.warning("추출된 상품 링크가 없습니다. 크롤링을 중단합니다.")
            return
        
        link_extraction_time = time.time() - link_start_time
        logger.info(f"링크 추출 완료 - {len(product_link_list)}개 상품, "
                   f"소요시간: {link_extraction_time:.1f}초")
        
        # 2단계: 크롤링 실행
        logger.info("2단계: 상품 정보 및 리뷰 크롤링 시작...")
        
        if use_batch_processing and len(product_link_list) > batch_size:
            # 대량 데이터의 경우 배치 처리
            run_batch_processing(product_link_list, job_id, batch_size)
        else:
            # 소량 데이터의 경우 일반 멀티프로세싱
            run_optimized_multi_process(product_link_list, job_id)
        
        # 3단계: 후처리 (GCS 업로드, 알림 등)
        # try:
        #     logger.info("3단계: 데이터 업로드 중...")
        #     storage_dir = upload_parquet_to_gcs(job_id)
        #     notify_spark_server(storage_dir)
        # except Exception as e:
        #     logger.error(f'데이터 업로드 실패: {e}')
        
        # 완료 처리
        total_time = time.time() - start_time
        completion_time = str(timedelta(seconds=total_time))
        
        logger.info("="*50)
        logger.info("크롤링 작업 완료!")
        logger.info(f"- Job ID: {job_id}")
        logger.info(f"- 처리된 상품 수: {len(product_link_list)}개")
        logger.info(f"- 총 소요시간: {completion_time}")
        logger.info(f"- 평균 처리시간: {total_time/len(product_link_list):.2f}초/상품")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f'크롤링 작업 중 치명적 오류 발생: {e}')
        raise
    finally:
        if is_crawling_running:
            is_crawling_running.value = False

def quick_test_crawling(keyword: str, max_link: int = 3) -> None:
    """빠른 테스트용 크롤링 함수"""
    from multiprocessing import Manager
    
    manager = Manager()
    is_crawling_running = manager.Value('b', True)
    
    logger.info(f"테스트 크롤링 시작 - 키워드: '{keyword}', 링크 수: {max_link}")
    
    try:
        crawling_run_optimized(
            keyword=keyword, 
            max_link=max_link, 
            is_crawling_running=is_crawling_running,
            use_batch_processing=False  # 테스트에서는 배치 처리 비활성화
        )
    except Exception as e:
        logger.error(f"테스트 크롤링 실패: {e}")
    finally:
        manager.shutdown()

# 성능 모니터링 데코레이터
def monitor_performance(func):
    """함수 실행 시간을 모니터링하는 데코레이터"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"{func.__name__} 실행 시간: {end_time - start_time:.2f}초")
        return result
    return wrapper

if __name__ == "__main__":
    # 테스트 실행
    test_keyword = "청소기"
    quick_test_crawling(test_keyword, 5)