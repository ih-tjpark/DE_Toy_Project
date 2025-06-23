from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number, udf
from pyspark.sql.window import Window
from pyspark.sql.types import StringType
from transform.data_access import save_analysis_to_postgresql
import requests
import re
import os
import pandas as pd

os.environ["PYSPARK_PYTHON"] = "C:/Users/KOSA/env_spark/Scripts/python.exe"


def after_processing( df: pd.DataFrame, product_code: int):

    total = len(df)
    positive_ratio = float(round((df['sentiment'] == '긍정').sum() / total, 3))
    neutral_ratio = float(round((df['sentiment'] == '중립').sum() / total, 3))
    negative_ratio = float(round((df['sentiment'] == '부정').sum() / total, 3))


    # 감정별 문장 리스트
    sentiment_positive = df[df['sentiment'] == '긍정']['summary'].tolist()
    sentiment_neutral = df[df['sentiment'] == '중립']['summary'].tolist()
    sentiment_negative = df[df['sentiment'] == '부정']['summary'].tolist()

    print('[INFO] 분석 결과 데이터 결과 집계를 완료했습니다.')

    save_analysis_to_postgresql(
        product_code,
        positive_ratio,
        neutral_ratio,
        negative_ratio,
        sentiment_positive,
        sentiment_neutral,
        sentiment_negative
    )

def clean_text(text):
    if text is None:
        return ""
    text = re.sub('[^A-Za-z0-9가-힣]', '', text)  # 특수문자 제거
    text = re.sub(r"(ㅋ|ㅎ){2,}", "", text)                   # ㅋㅋㅋ, ㅎㅎㅎ 제거
    text = re.sub(r"\s+", " ", text)                         # 다중 공백 제거
    return text

def create_spark_session():
    spark = SparkSession.builder \
        .appName("Review Preprocessing") \
        .master("local[*]")\
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem") \
        .config("spark.hadoop.fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") \
        .config("spark.hadoop.google.cloud.auth.service.account.enable", "true") \
        .config("spark.hadoop.google.cloud.auth.service.account.json.keyfile", "spark_api\key\kosa-semi-e79fa479a065.json") \
        .getOrCreate()
    
    return spark

def trans_data(df):
    # 쿠팡체험단 리뷰 제거
    df = df.filter(~col("review_content").startswith("쿠팡체험단"))


    # product_code별 중복 리뷰 제거
    w_dup = Window.partitionBy('product_code', 'review_writer').orderBy(col('review_date').desc())
    df = df.withColumn('row_num', row_number().over(w_dup)) \
                .filter('row_num == 1') \
                .drop('row_num')
    print('[INFO] 상품 별 중복 리뷰를 제거했습니다.' )

    # 상품 별 리뷰 10개만 가져오기 
    w_top10 = Window.partitionBy('product_code').orderBy(col('review_date').desc())
    df = df.withColumn('row_num', row_number().over(w_top10)) \
                        .filter(col('row_num') <= 10) \
                        .drop('row_num')
    print('[INFO] 상품 별 최신 날짜 기준 리뷰 10개를 추출했습니다.' )

    # 텍스트 전처리
    clean_text_udf = udf(clean_text, StringType())
    df = df.withColumn("cleaned_review", clean_text_udf(col("review_content")))
    print('[INFO] 텍스트를 전처리 했습니다..' )

    return df

def request_analyze(df):
    # Pandas로 변환 후 분석 요청
    pandas_df = df.select("product_code", "cleaned_review").toPandas()
    product_codes = pandas_df['product_code'].unique()

    results = []
    for i,product_code in enumerate(product_codes):
        # text = row["cleaned_review"]
        # product_code = row["product_code"]
        prod_df = pandas_df.loc[pandas_df['product_code']== product_code]
        reviews = prod_df["cleaned_review"].tolist()
        payload = {
            "product_code": product_code,
            "reviews": reviews
        }

        try:
            response = requests.post('http://10.128.0.180:3245/analyze', json=payload)
            print(f'[INFO] {product_code} 데이터 분석 결과를 받았습니다.')
            analyze_df = pd.DataFrame(response.json())
            after_processing(analyze_df, product_code)
            print(f'[INFO] {product_code} 데이터 분석 결과를 저장했습니다.')
        except Exception as e:
            print(f"[ERROR] 분석 요청 실패: {e}")
            results.append({
                "product_code": product_code,
                "summary": "",
                "sentiment": "error"
            })
            