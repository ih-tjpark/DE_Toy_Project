import pandas as pd
import psycopg2
from google.cloud import storage
from datetime import datetime
import pandas as pd
import os
import csv


# Local에 parquet형식 리뷰 저장 
def save_reviews_to_local(reviews: list, product_code: str, job_id: str) -> None:
    today = datetime.today().strftime("%Y-%m-%d")
    dir_name = f'review_data/{today}/{job_id}/'
    
    if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    
    df = pd.DataFrame(reviews)
    file_path = f"{dir_name}/coupang_review_{product_code}.parquet"
    df.to_parquet(file_path, engine="pyarrow", index=False)
    #print(f"[INFO] {product_code} 리뷰가 parquet 파일로 저장되었습니다")


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "crawling_api/key/kosa-semi-e79fa479a065.json"

# cloud storage 저장
"""
    GCS에 파일 업로드 함수
    - bucket_name: GCS 버킷 이름
    - source_file_path: 로컬 파일 경로
    - destination_blob_name: GCS 버킷 내 저장 경로
"""
def upload_parquet_to_gcs(job_id: str): 
    today = datetime.today().strftime("%Y-%m-%d")
    dir = f'review_data/{today}/{job_id}/'
    bucket_name = 'kosa-semi-datalake'
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    

    # GCS에 업로드
    for file in os.listdir(dir):
        if file.endswith(".parquet"):
            local_file_path = os.path.join(dir, file)
            gcs_path = f"{dir}{file}"

            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(local_file_path)
            print(f"[INFO] GCS 업로드 완료: gs://{bucket_name}/{gcs_path}")
    
    return dir


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


# 상품 기본 정보 csv 로컬 저장
def save_product_info_to_csv(product_dict:dict) -> None:
    dir_name = './product_info_data'
    
    if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    fieldnames = list(product_dict.keys())

    filepath = os.path.join(dir_name, str(product_dict["product_code"])+'.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()           
        writer.writerow(product_dict)        
