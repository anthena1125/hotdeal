import requests
from bs4 import BeautifulSoup
import time
import threading
import os
from flask import Flask

app = Flask(__name__)

# ================= 설정 값 입력 =================
TELEGRAM_TOKEN = "8870775774:AAH7uofm_bvfkHB-1kUL5_TGP42mJS2mpA4"
CHAT_ID = "523461892"
CAFE_URL = "https://cafe.naver.com/f-e/cafes/31731163/menus/1?viewType=L"
# ===============================================

sent_articles = set()

def send_telegram_message(text):
    """텔레그램 전송 함수"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("텔레그램 전송 실패:", e)

def check_hotdeal():
    """핫딜 크롤링 함수"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(CAFE_URL, headers=headers)
        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('.article-board .article-table tbody tr')

        for row in reversed(rows):
            if 'board-notice' in row.get('class', []):
                continue

            article_num_tag = row.select_one('.type_articleNumber')
            if not article_num_tag:
                continue
            article_num = article_num_tag.text.strip()

            if article_num in sent_articles:
                continue

            title_tag = row.select_one('.inner_list .article')
            if not title_tag:
                continue
            
            title = title_tag.text.strip()
            link = title_tag['href']

            if len(sent_articles) > 0:
                message = f"🚨 *새로운 핫딜 등장!*\n\n📌 {title}\n🔗 [게시글 바로가기]({link})"
                send_telegram_message(message)
                print(f"[알림 전송] {title}")

            sent_articles.add(article_num)

    except Exception as e:
        print("조회 중 에러 발생:", e)

def run_bot():
    """백그라운드에서 60초마다 무한 반복하는 함수"""
    check_hotdeal() # 처음 실행 시 기존 글 캐싱
    while True:
        time.sleep(60)
        check_hotdeal()

# Web Service가 정상 작동하는지 확인하기 위한 기본 주소(엔드포인트)
@app.route('/')
def keep_alive():
    return "맘이베베 핫딜 알리미가 정상 작동 중입니다!"

if __name__ == "__main__":
    # 크롤러를 백그라운드 스레드로 분리하여 실행
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask 웹 서버 실행 (Render 환경에 맞춘 포트 설정)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)