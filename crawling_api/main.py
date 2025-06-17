from crawling.window_multi_crawling import crawling_start
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from multiprocessing import Process, Manager, freeze_support
import time
import uvicorn

app = FastAPI()
#status = None
# 🔐 공유 상태 관리용 dict (멀티프로세싱-safe)


# 🔐 공유 상태 관리용 dict (멀티프로세싱-safe)
#manager = Manager()
#crawl_status: dict[str,bool] = {}#manager.dict()  # type: ignore
# manager = Manager()

# status_ = manager.Value('b', False)  # 'b' = boolean
#status = False

class CrawlRequest(BaseModel):
    keyword: str
    max_links: int

class crawlResponse(BaseModel):
    message: str
    status: str
    

def crawl_job(keyword: str, max_count: int, shared_status, shared_dict):
    try:
        crawling_start(keyword, max_count, shared_dict)
    finally:
        print('작업 완료')
        shared_status.value = False

@app.post("/crawl",response_model = crawlResponse )
def start_crawling(req: CrawlRequest):
    try:
        keyword = req.keyword
        max_links = req.max_links

        # 크롤링 작업 중이면 작업 중이라고 반환 
        try:
            if status.value == True:
                return {"status": "processing", "message": "작업이 이미 실행 중입니다."}
        except NameError:
            # 처음 실행 시 멀티 프로세싱 간 공유 변수 생성
            manager = Manager()
            status = manager.Value('b', False) # type: ignore
            product_info_dict : dict = manager.dict() # type: ignore
        # 상태를 True로 설정하고 새 프로세스 실행

        status.value = True
        p = Process(target=crawl_job, args=(keyword, max_links, status, product_info_dict))
        p.start()

        return {"status": "started", "message": f"'{keyword}'에 대한 크롤링 작업을 시작했습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    freeze_support()  # Windows 필수
    manager = Manager()
    global status
    status = manager.Value('b', False) # type: ignore
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)