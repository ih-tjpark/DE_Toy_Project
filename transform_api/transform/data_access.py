import psycopg2
import json

def load_data_from_gcs(spark, dir):
    # GCS 경로 지정
    # 주소 예시 'gs://kosa-semi-datalake/review_data/2025-06-19/job_20250619_155501/*.parquet'
    # dir = review_data/2025-06-19/job_20250619_155501/
    bucket = 'kosa-semi-datalake'
    gcs_path = f"gs://{bucket}/{dir}*.parquet"

    # 파일 읽기
    df = spark.read.parquet(gcs_path)
    
    return df



def save_analysis_to_postgresql(
    product_id: int,
    positive_ratio: float,
    neutral_ratio: float,
    negative_ratio: float,
    sentiment_positive: list,
    sentiment_neutral: list,
    sentiment_negative: list
):
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            dbname="postgres",
            user="postgres",
            password="todn12",
            port=2345
        )
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO analysis_result (
            product_id,
            positive_ratio,
            neutral_ratio,
            negative_ratio,
            sentiment_positive,
            sentiment_neutral,
            sentiment_negative
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            product_id,
            positive_ratio,
            neutral_ratio, 
            negative_ratio, 
            json.dumps(sentiment_positive, ensure_ascii=False), 
            json.dumps(sentiment_neutral, ensure_ascii=False),
            json.dumps(sentiment_negative, ensure_ascii=False)
        ))

        conn.commit()
        print(f"[INFO] '{product_id}' 분석 결과 저장 완료했습니다.")

    except Exception as e:
        print(f"[ERROR] PostgreSQL 저장 실패: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()


