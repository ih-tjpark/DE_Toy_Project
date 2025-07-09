from contextlib import asynccontextmanager
from crawling.crawling_pipeline import crawling_run
from crawling.optimized_crawling_pipeline import crawling_run_optimized, quick_test_crawling
from model.crawling_model import CrawlRequest,crawlResponse
from fastapi import FastAPI, HTTPException, Query
from multiprocessing import Process, Manager, freeze_support
import uvicorn
import time

import logging
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

# app 시작/종료 작업 설정
@asynccontextmanager
async def lifespan(app:FastAPI):
    """
    애플리케이션 시작 시 Manager와 공유 변수를 초기화합니다.
    이는 모든 FastAPI 워커 프로세스에서 단 한 번만 실행
    """
    print("애플리케이션 시작: Manager 및 공유 상태 변수 초기화")
    # manager와 status를 app.state에 저장하여 전역적으로 접근 가능
    app.state.manager = Manager()
    app.state.is_crawling_running = app.state.manager.Value('b', False)
    
    yield # yield 이전 코드는 fastapi시작할 때 실행됨 / 이후 코드는 종료될 때 실행
    
    print("애플리케이션 종료: Manager 종료")
    if hasattr(app.state, 'manager'):
        app.state.manager.shutdown()

# app 실행
app = FastAPI(lifespan=lifespan)

@app.post("/crawl")
def start_crawling(req: CrawlRequest):
    """기존 크롤링 API (호환성 유지)"""
    try:
        keyword = req.keyword
        max_links = req.max_links
        is_crawling_running = app.state.is_crawling_running
        print(f"[INFO] {keyword}가 검색되었습니다.")

        # 상태를 True로 설정하고 새 프로세스 실행
        if is_crawling_running.value == True:
            print("[INFO] 작업이 이미 실행중이라 요청을 반려합니다.")
            return {"status": "processing", "message": "작업이 이미 실행 중입니다."}
        
        is_crawling_running.value = True
        print(f"[INFO] {keyword} 크롤링 작업을 실행합니다.")
        p = Process(target=crawling_run, args=(keyword, max_links, is_crawling_running))
        p.start()

        return {"status": "started", "message": f"'{keyword}'에 대한 크롤링 작업을 시작했습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl/optimized")
def start_optimized_crawling(req: CrawlRequest, 
                           use_batch_processing: bool = Query(True, description="배치 처리 사용 여부"),
                           batch_size: int = Query(15, description="배치 크기")):
    """최적화된 크롤링 API"""
    try:
        keyword = req.keyword
        max_links = req.max_links
        is_crawling_running = app.state.is_crawling_running
        print(f"[INFO] 최적화된 크롤링 - {keyword}가 검색되었습니다.")

        # 상태 확인
        if is_crawling_running.value == True:
            print("[INFO] 작업이 이미 실행중이라 요청을 반려합니다.")
            return {"status": "processing", "message": "작업이 이미 실행 중입니다."}
        
        is_crawling_running.value = True
        print(f"[INFO] {keyword} 최적화된 크롤링 작업을 실행합니다.")
        
        # 최적화된 크롤링 실행
        p = Process(target=crawling_run_optimized, 
                   args=(keyword, max_links, is_crawling_running, use_batch_processing, batch_size))
        p.start()

        return {
            "status": "started", 
            "message": f"'{keyword}'에 대한 최적화된 크롤링 작업을 시작했습니다.",
            "optimizations": {
                "headless_mode": True,
                "resource_blocking": True,
                "smart_waiting": True,
                "batch_processing": use_batch_processing,
                "batch_size": batch_size if use_batch_processing else None
            }
        }
    except Exception as e:
        is_crawling_running.value = False
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl/test")
def test_crawling(keyword: str = Query(..., description="테스트할 키워드"),
                 max_links: int = Query(3, description="테스트할 링크 수")):
    """빠른 테스트 크롤링 API"""
    try:
        is_crawling_running = app.state.is_crawling_running
        
        if is_crawling_running.value == True:
            return {"status": "processing", "message": "다른 크롤링 작업이 실행 중입니다."}
        
        print(f"[INFO] 테스트 크롤링 시작 - {keyword}")
        
        # 별도 프로세스에서 실행
        p = Process(target=quick_test_crawling, args=(keyword, max_links))
        p.start()
        
        return {
            "status": "started",
            "message": f"'{keyword}' 테스트 크롤링을 시작했습니다. (최대 {max_links}개 상품)",
            "note": "테스트용이므로 별도 상태 관리 없이 실행됩니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crawl/status")
def get_crawling_status():
    """크롤링 상태 확인 API"""
    try:
        is_running = app.state.is_crawling_running.value
        return {
            "is_running": is_running,
            "status": "processing" if is_running else "idle",
            "message": "크롤링이 실행 중입니다." if is_running else "크롤링이 실행 중이지 않습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crawl/performance-guide")
def get_performance_guide():
    """성능 최적화 가이드 API"""
    return {
        "optimizations": {
            "browser_settings": {
                "headless_mode": "GUI 렌더링 비용 제거 (30-50% 속도 향상)",
                "resource_blocking": "이미지/CSS/JS 로딩 차단으로 네트워크 비용 절약",
                "page_load_strategy": "DOM 준비 시 즉시 진행으로 대기 시간 단축"
            },
            "waiting_optimization": {
                "smart_waiting": "time.sleep() 대신 WebDriverWait 사용",
                "dynamic_timeout": "요소별 적응형 타임아웃 설정",
                "javascript_clicks": "더 빠른 JavaScript 클릭 사용"
            },
            "processing_optimization": {
                "batch_processing": "대량 데이터 메모리 효율적 처리",
                "optimal_processes": "CPU 사용률 80% 최적화",
                "concurrent_futures": "더 효율적인 병렬 처리"
            }
        },
        "recommended_settings": {
            "small_scale": "10개 이하 상품: 일반 멀티프로세싱",
            "medium_scale": "10-50개 상품: 배치 크기 10-15",
            "large_scale": "50개 이상 상품: 배치 크기 15-20"
        },
        "expected_improvements": {
            "speed": "2-4배 속도 향상",
            "memory": "메모리 사용량 30-50% 감소",
            "stability": "에러 처리 및 복구 개선"
        }
    }

@app.get("/")
def root():
    return {
        "message": "쿠팡 크롤링 API", 
        "version": "2.0 (Optimized)",
        "endpoints": {
            "POST /crawl": "기존 크롤링 (호환성 유지)",
            "POST /crawl/optimized": "최적화된 크롤링",
            "POST /crawl/test": "빠른 테스트 크롤링",
            "GET /crawl/status": "크롤링 상태 확인",
            "GET /crawl/performance-guide": "성능 최적화 가이드"
        }
    }

if __name__ == "__main__":
    freeze_support()  # Windows 필수
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)