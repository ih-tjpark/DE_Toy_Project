from contextlib import asynccontextmanager
from analysis_api.model.analysis_model import JobRequest
from analysis.analysis_pipeline import analyze_run
from fastapi import FastAPI, HTTPException
from multiprocessing import Manager, freeze_support
import uvicorn





@asynccontextmanager
async def lifespan(app:FastAPI):
    """
    애플리케이션 시작 시 Manager와 공유 변수를 초기화합니다.
    이는 모든 FastAPI 워커 프로세스에서 단 한 번만 실행
    """
    print("[INFO]애플리케이션 시작: Manager 및 공유 상태 변수 초기화")
    # manager와 status를 app.state에 저장하여 전역적으로 접근 가능
    app.state.manager = Manager()
    app.state.is_running = app.state.manager.Value('b', False)
    #print("[INFO] 모델을 생성합니다.")
    #print(f"초기 is_running.value: {app.state.is_running.value}")
    
    yield # yield 이전 코드는 fastapi시작할 때 실행됨 / 이후 코드는 종료될 때 실행
    
    print("애플리케이션 종료: Manager 종료")
    if hasattr(app.state, 'manager'):
        app.state.manager.shutdown()
    
app = FastAPI(lifespan=lifespan)


@app.post("/analyze")
def start_crawling(req: JobRequest):
    try:
        reviews = req.reviews
        prodcut_code = req.product_code
        
        is_running = app.state.is_running
        print(f"[INFO] 텍스트 분석이 요청되었습니다.")

        # 상태를 True로 설정하고 새 프로세스 실행
        if is_running.value == True:
            print("[INFO] 작업이 이미 실행중이라 요청을 반려합니다.")
            return {"status": "processing", "message": "작업이 이미 실행 중입니다."}
        
        is_running.value = True
        print(f"[INFO] 분석 작업을 실행합니다.")

        summary, sentiment = analyze_run(reviews, is_running)
        payload = {
            "summary" : summary,
            "sentiment" : sentiment,
        }
        # p = Process(target=analyze_job, args=(reviews, is_running))
        # p.start()

        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    freeze_support()  # Windows 필수
    uvicorn.run("main:app", host="0.0.0.0", port=3245, reload=True)