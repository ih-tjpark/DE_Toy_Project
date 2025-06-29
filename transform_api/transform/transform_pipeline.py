
from transform_api.transform.transform_job import create_spark_session, trans_data, request_analyze, after_processing
from transform.data_access import load_data_from_gcs
import sys
import os

# spark_api 폴더의 절대 경로를 PYTHONPATH에 추가
def add_path():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    os.environ["PYTHONPATH"] = project_root

def transform_run(gcs_dir, is_running):


    # Spark app 생성
    print('[INFO] Spark app을 생성합니다.' )
    spark = create_spark_session()
    
    # Cloud Storage에서 데이터 불러옴
    print('[INFO] Cloud Storage에서 데이터 불러옵니다.')
    df = load_data_from_gcs(spark, gcs_dir)


    # 데이터 변환 작업 진행
    print('[INFO] 데이터 변환 작업을 진행합니다.')
    trans_df = trans_data(df)

    
    # 분석 요청 및 저장
    print('[INFO] 분석 요청 및 저장을 진행합니다.')
    request_analyze(trans_df)


    # 분석 된 data 취합 및 저장
    # print('[INFO] 분석 요청을 진행합니다.')
    # after_processing(analyze_df, int(product_code))


    is_running.value = False
    print('[INFO] 데이터 처리 작업 완료')