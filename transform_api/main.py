from contextlib import asynccontextmanager
from transform_api.transform.transform_pipeline import transform_run, add_path
from transform_api.model.transform_model import JobRequest, JobResponse
#from spark_job.data_transform import 
from fastapi import FastAPI, HTTPException
from multiprocessing import Process, Manager, freeze_support
import uvicorn





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
    app.state.is_running = app.state.manager.Value('b', False)
    #print(f"초기 is_running.value: {app.state.is_running.value}")

    add_path()
    
    yield # yield 이전 코드는 fastapi시작할 때 실행됨 / 이후 코드는 종료될 때 실행
    
    print("애플리케이션 종료: Manager 종료")
    if hasattr(app.state, 'manager'):
        app.state.manager.shutdown()

# app 실행
app = FastAPI(lifespan=lifespan)


@app.post("/start-processing")
def start_crawling(req: JobRequest):
    try:
        gcs_dir = req.dir
        is_running = app.state.is_running
        
        print(f"[INFO] 수신된 작업 dir: {gcs_dir}")

        # 상태를 True로 설정하고 새 프로세스 실행
        if is_running.value == True:
            print("[INFO] 작업이 이미 실행중이라 요청을 반려합니다.")
            return {"status": "processing", "message": "작업이 이미 실행 중입니다."}
        
        is_running.value = True
        print(f"[INFO] {gcs_dir} 데이터 처리 작업을 실행합니다.")
        p = Process(target=transform_run, args=(gcs_dir, is_running))
        p.start()

        return {"status": "started", "message": f"'{gcs_dir}'에 대한 데이터 처리 작업을 시작했습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    freeze_support()  # Windows 필수
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)