
from transform.data_transform import create_spark_session, trans_data, request_analyze, after_processing
from transform.data_access import load_data_from_gcs

def spark_job_pipeline(gcs_dir, is_running):

    # Spark app 생성
    spark = create_spark_session()
    
    # Cloud Storage에서 데이터 불러옴
    df = load_data_from_gcs(spark, gcs_dir)

    # 데이터 변환 작업 진행
    trans_df = trans_data(df)
    
    # 분석 요청
    analyze_df, product_code = request_analyze(trans_df)

    # 분석 된 data 취합 및 저장
    after_processing(analyze_df, int(product_code))

    is_running.value = False
    print('[INFO] 데이터 처리 작업 완료')