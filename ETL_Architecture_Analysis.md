# DE_TOY_Project ETL 구조 분석 보고서

## 📋 현재 구조 개요

### ETL 아키텍처
```
data_extract/ (별도 크롤링 스크립트)
    ↓
crawling_api/ (Extract) → transform_api/ (Transform) → analysis_api/ (Load/Analysis)
```

### 각 API 구성
- **crawling_api** (Port: 8000): 데이터 수집 (Extract)
- **transform_api** (Port: 8000): 데이터 변환 (Transform) 
- **analysis_api** (Port: 3245): 데이터 분석 (Load/Analysis)

## 🚨 발견된 문제점

### 1. **코드 중복 및 일관성 부족**
- `data_extract/` 디렉토리에 별도의 크롤링 코드 존재
- `crawling_api/crawling/crawling_job.py`와 `data_extract/linux_coupang_crawling.py`가 비슷한 기능 수행
- 두 곳에서 같은 크롤링 로직을 다르게 구현

### 2. **API 간 통신 구조의 비효율성**
```python
# crawling_api/crawling/request_to_transform_api.py
spark_server_url = "http://<spark_server_ip>:<port>/start-processing"  # 하드코딩된 주석 상태
```
- 하드코딩된 서버 주소가 주석 처리됨
- API 간 통신이 제대로 구현되지 않음

### 3. **포트 충돌 위험**
```python
# crawling_api/main.py
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# transform_api/main.py  
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)  # 같은 포트 사용
```

### 4. **잘못된 임포트 경로**
```python
# transform_api/main.py
from transform_api.transform.transform_pipeline import transform_run, add_path
```
- 상대 경로가 아닌 절대 경로 사용으로 모듈 경로 오류 가능성

### 5. **분석 API의 설계 문제**
```python
# analysis_api/main.py의 analyze 엔드포인트
summary, sentiment = analyze_run(reviews, is_running)
return payload  # 동기적 처리
```
- 다른 API는 비동기 처리인데 분석 API만 동기 처리
- ETL의 "Load" 단계가 아닌 분석 결과를 바로 반환

### 6. **데이터 흐름의 불명확성**
- 크롤링된 데이터가 GCS에 저장되지만 실제 업로드 코드가 주석 처리됨
- Transform API에서 분석 요청 후 결과 처리 로직 미완성

### 7. **의존성 관리 문제**
- `requirements.txt`와 `crawl_requirements.txt` 두 개 파일 존재
- 일부 의존성이 중복되거나 버전 충돌 가능성

## 💡 개선 제안사항

### 1. **통합된 크롤링 모듈**
- `data_extract/` 디렉토리의 스크립트를 `crawling_api/`로 통합
- 공통 크롤링 로직을 모듈화하여 재사용성 향상

### 2. **환경 설정 파일 도입**
```yaml
# config.yaml
services:
  crawling_api:
    host: "0.0.0.0"
    port: 8000
  transform_api:
    host: "0.0.0.0"
    port: 8001  # 포트 변경
  analysis_api:
    host: "0.0.0.0"
    port: 8002  # 포트 변경
```

### 3. **API 게이트웨이 또는 오케스트레이터 도입**
- Apache Airflow, Prefect 등을 사용한 워크플로 관리
- API 간 의존성과 순서 보장

### 4. **데이터베이스 계층 추가**
```
Extract (crawling_api) → Database/Queue → Transform (transform_api) → Database → Analysis (analysis_api)
```

### 5. **비동기 처리 일관성**
- 모든 API에서 비동기 처리 패턴 통일
- 작업 상태 추적을 위한 Job Queue 시스템 도입

### 6. **로깅 및 모니터링 강화**
```python
import logging
import structlog

# 구조화된 로깅 설정
logger = structlog.get_logger()
```

### 7. **Docker 컨테이너화**
```dockerfile
# 각 API별 독립적인 컨테이너 환경
# docker-compose.yml로 전체 시스템 관리
```

## 🏗️ 권장 아키텍처

### 개선된 ETL 구조
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Crawling API  │    │  Transform API   │    │  Analysis API   │
│   (Port: 8000)  │    │   (Port: 8001)   │    │  (Port: 8002)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw Data DB   │    │ Processed Data   │    │   Analysis      │
│   (PostgreSQL)  │    │     (GCS)        │    │   Results DB    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 워크플로 관리
```python
# Airflow DAG 예시
from airflow import DAG
from airflow.operators.http_operator import SimpleHttpOperator

dag = DAG('etl_pipeline', schedule_interval='@daily')

crawl_task = SimpleHttpOperator(
    task_id='crawl_data',
    http_conn_id='crawling_api',
    endpoint='/crawl',
    dag=dag
)

transform_task = SimpleHttpOperator(
    task_id='transform_data',
    http_conn_id='transform_api',
    endpoint='/start-processing',
    dag=dag
)

crawl_task >> transform_task
```

## 🎯 우선순위 개선사항

1. **즉시 수정 필요**: 포트 충돌 문제
2. **단기 개선**: API 간 통신 로직 완성 
3. **중기 개선**: 코드 중복 제거 및 모듈 통합
4. **장기 개선**: 워크플로 관리 시스템 도입

현재 구조는 ETL의 기본 개념은 잘 구현되어 있지만, 실제 운영 환경에서는 여러 문제점이 발생할 수 있습니다. 위 개선사항들을 단계적으로 적용하면 더 안정적이고 확장 가능한 데이터 파이프라인을 구축할 수 있습니다.