from analysis.analysis_job import summary_analyze, sentiment_analyze
import gc


def analyze_run(reviews: str ,is_running: bool):
    try:
        summary_texts = summary_analyze(reviews)
        print("[INFO] 요약 분석 완료")
        sentiment = sentiment_analyze(summary_texts)
        print(f'[INFO] 텍스트 요약 분석: {summary_texts}')
        print(f'[INFO] 텍스트 감정 분석: {sentiment}')
        return summary_texts, sentiment
    except Exception as e:
        print('[ERROR] 에러가 발생했습니다: ',e)
    finally:
        gc.collect()
        print('작업 완료')
        is_running.value = False