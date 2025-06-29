from transformers import pipeline
import torch
import time
import datetime

def sentiment_class(review):
    sentiment_dict ={
        '기쁨(행복한)' : "긍정",
        '고마운' : "긍정",
        '설레는(기대하는)' : "긍정",
        '사랑하는' : "긍정",
        '즐거운(신나는)': "긍정",
        '일상적인' : "중립",
        '생각이 많은' : "부정", 
        '슬픔(우울한)': "부정",
        '힘듦(지침)' : "부정",
        '짜증남' : "부정",
        '걱정스러운(불안한)': "부정"
    }
    result = sentiment_dict[review]
    return result

    
def summary_analyze(reviews: list) -> list:
    model_name = "kakaocorp/kanana-nano-2.1b-instruct"
    pipe = pipeline("text-generation", model= model_name )
    results = []
    for i,review in enumerate(reviews):
        start = time.time()
        test = "다음의 상품 리뷰를 50글자 이하의 한 문장으로 요약해줘 / 리뷰: " + review
        messages = [
            {"role": "user", "content": test},
        ]
        result_dict = pipe(messages,max_new_tokens=64)
        result_text = result_dict[0]['generated_text'][1]['content']
        results.append(result_text)
        sec = time.time()-start
        times = str(datetime.timedelta(seconds=sec))

        print(f"[INFO] {i+1} 번째 요약 분석 완료. 소요 시간: {times}")
    
    return results

def sentiment_analyze(reviews: list) -> list:
    model_name = "nlp04/korean_sentiment_analysis_kcelectra"
    pipe = pipeline("text-classification", model=model_name)  

    results = []
    
    for review in reviews:
        sentiment_result = pipe(review)
        sentment = sentiment_class(sentiment_result[0]['label'])
        results.append(sentment)
    return results


# if __name__== "__main__":

#     run_analyze(text)