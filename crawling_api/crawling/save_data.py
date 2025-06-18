import pandas as pd
import psycopg2
from google.cloud import storage
from datetime import datetime
import pandas as pd
import os


# cloud storage 저장
"""
    GCS에 파일 업로드 함수
    - bucket_name: GCS 버킷 이름
    - source_file_path: 로컬 파일 경로
    - destination_blob_name: GCS 버킷 내 저장 경로
"""
def upload_parquet_to_gcs(df_list: list, keyword, product_code): 
    # 날짜 기준 폴더명 생성
    today = datetime.today().strftime("%Y-%m-%d")

    # 목적지 경로 구성: 날짜/검색어/review_상품코드.parquet
    local_path = f"review_data/{today}/{keyword}/"
    destination_blob_name = f"{local_path}/review_{product_code}.parquet"

    # 로컬 임시 파일로 저장
    if not os.path.exists(local_path):
            os.makedirs(local_path)
    df = pd.DataFrame(df_list)
    df.to_parquet(destination_blob_name, engine="pyarrow", index=False)

    # GCS에 업로드
    storage_client = storage.Client()
    bucket = storage_client.bucket('kosa-semi-datalake')
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_path)

    print(f"[INFO] GCS에 저장 완료: gs://kosa-semi-datalake/{destination_blob_name}")



# db 저장
def insert_product_info_to_db(product: dict):
    
    conn = psycopg2.connect(
        host="127.0.0.1",
        dbname="postgres",
        user="postgres",
        password="todn12",
        port=2345
    )

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO product 
                (id, name, rating, review_count, price, tag, image_url)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (
            product.get("product_code"),
            product.get("name"),
            product.get("star_rating"),
            product.get("review_count"),
            product.get("final_price"),
            product.get("tag"),
            product.get("image_url"),
        ))
        conn.commit()
        print(f"[INFO] 상품 정보 DB 저장 완료: {product.get('product_code')}")