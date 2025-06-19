import requests

def notify_spark_server(job_id: str):
    spark_server_url = "http://<spark_server_ip>:<port>/start-processing"
    payload = {"job_id": job_id}

    try:
        response = requests.post(spark_server_url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[INFO] Spark 서버에 작업 요청 성공: {response.json()}")
        else:
            print(f"[ERROR] Spark 서버 요청 실패: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"[ERROR] Spark 서버 통신 오류: {e}")