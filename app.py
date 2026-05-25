import requests
import time
import threading
import os
from flask import Flask

app = Flask(__name__)

# ================= 설정 값 =================
TELEGRAM_TOKEN = "8870775774:AAH7uofm_bvfkHB-1kUL5_TGP42mJS2mpA4"
CHAT_ID = "523461892"

# 테스트 카페 (맘이베베로 복귀하시려면 CLUB_ID="29434212", MENU_ID="2" 로 변경)
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
    """게시글 목록 데이터 수집"""
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15"
    }
    
    try:
        response = requests.get(API_URL, headers=headers)
        if response.status_code != 200:
            return

        data = response.json()
        article_list = data.get('message', {}).get('result', {}).get('articleList', [])

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
        print("조회 중 에러 발생:", e)

def run_bot():
    """백그라운드에서 60초마다 무한 반복"""
    print("서버 가동: 목록 데이터 전용 수집기 실행")
    check_hotdeal(is_first_run=True)
    
    while True:
        time.sleep(60)
        check_hotdeal(is_first_run=False)

@app.route('/')
def keep_alive():
    return "목록 수집 알림 봇이 정상 작동 중입니다!"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)