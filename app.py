import requests
import time
import threading
import os
from flask import Flask

app = Flask(__name__)

# ================= 설정 값 =================
TELEGRAM_TOKEN = "8870775774:AAH7uofm_bvfkHB-1kUL5_TGP42mJS2mpA4"
CHAT_ID = "523461892"

CLUB_ID = "31731163"
MENU_ID = "1"

API_URL = f"https://apis.naver.com/cafe-web/cafe2/ArticleList.json?search.clubid={CLUB_ID}&search.queryType=lastArticle&search.menuid={MENU_ID}&search.page=1&search.perPage=15"
# ===========================================

sent_articles = set()

def send_telegram_message(text):
    """텔레그램 전송 함수"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("텔레그램 전송 실패:", e)

def check_hotdeal(is_first_run=False):
    # 봇 차단을 우회하기 위한 필수 헤더(Referer) 추가 (네이버 카페 앱에서 접속한 것처럼 위장)
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
        "Referer": f"https://m.cafe.naver.com/ca-fe/web/cafes/{CLUB_ID}/menus/{MENU_ID}",
        "Accept": "application/json, text/plain, */*"
    }
    
    try:
        print("\n--- 네이버 서버에 데이터 요청 중 ---")
        response = requests.get(API_URL, headers=headers)
        print(f"[디버그] 네이버 응답 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[디버그] 접근 거부됨. 네이버의 답변: {response.text[:300]}")
            return

        data = response.json()
        article_list = data.get('message', {}).get('result', {}).get('articleList', [])
        
        print(f"[디버그] 현재 네이버에서 읽어온 게시글 수: {len(article_list)}개")

        if len(article_list) == 0:
            print("[디버그] 경고: 접속은 성공했으나 게시글이 없습니다. (게시판이 비어있거나 권한 차단)")

        for article in reversed(article_list):
            if article.get('type') != 'ARTICLE':
                continue

            article_num = str(article.get('articleId'))
            if article_num in sent_articles:
                continue
            
            title = article.get('subject')
            link = f"https://m.cafe.naver.com/ca-fe/web/cafes/{CLUB_ID}/articles/{article_num}"

            if not is_first_run:
                message = f"🚨 *새로운 게시글 등장!*\n\n📌 {title}\n🔗 [게시글 바로가기]({link})"
                send_telegram_message(message)
                print(f"[알림 전송 완료] {title}")

            sent_articles.add(article_num)

    except Exception as e:
        print(f"[디버그] 조회 중 치명적 에러 발생: {e}")

def run_bot():
    print("서버 가동: 정밀 진단 모드 실행 중...")
    check_hotdeal(is_first_run=True)
    
    while True:
        time.sleep(60)
        check_hotdeal(is_first_run=False)

@app.route('/')
def keep_alive():
    return "알림 봇 정밀 진단 모드 가동 중!"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)