import pandas as pd
import psycopg2
#from google.cloud import storage



# def upload_parquet_to_gcs(df: pd.DataFrame, bucket_name: str, destination_blob_name: str):
#     # 로컬 임시 파일로 저장
#     local_path = f"/tmp/{destination_blob_name}"
#     df.to_parquet(local_path, engine="pyarrow", index=False)

#     # GCS에 업로드
#     storage_client = storage.Client()
#     bucket = storage_client.bucket(bucket_name)
#     blob = bucket.blob(destination_blob_name)
#     blob.upload_from_filename(local_path)

#     print(f"[INFO] GCS에 저장 완료: gs://{bucket_name}/{destination_blob_name}")




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