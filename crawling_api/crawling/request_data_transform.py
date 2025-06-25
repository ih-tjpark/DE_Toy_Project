import requests

def notify_spark_server(dir: str):
    spark_server_url = "http://10.128.0.11:8000/start-processing"
    payload = {"dir": dir}

    try:
        response = requests.post(spark_server_url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[INFO] Spark 서버에 작업 요청 성공: {response.json()}")
        else:
            print(f"[ERROR] Spark 서버 요청 실패: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"[ERROR] Spark 서버 통신 오류: {e}")