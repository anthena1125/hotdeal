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

# 껍데기 주소가 아닌, 게시글 목록만 있는 실제 내부 iframe 주소로 변경
CLUB_ID = "31731163"
MENU_ID = "1"
CAFE_URL = f"https://cafe.naver.com/ArticleList.nhn?search.clubid={CLUB_ID}&search.menuid={MENU_ID}&search.boardtype=L"
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

def check_hotdeal(is_first_run=False):
    """핫딜 크롤링 함수"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(CAFE_URL, headers=headers)
        if response.status_code != 200:
            print(f"페이지 로딩 실패: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('.article-board .article-table tbody tr')
        
        if len(rows) == 0:
            print("게시글을 가져오지 못했습니다. (접근 권한 없음 또는 차단)")
            return

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
            
            # 주소가 상대경로(/)로 시작할 경우 완전한 URL로 조립
            if link.startswith('/'):
                link = "https://cafe.naver.com" + link

            # 최초 실행(is_first_run=True)이 아닐 때만 알림 전송
            if not is_first_run:
                message = f"🚨 *새로운 게시글 등장!*\n\n📌 {title}\n🔗 [게시글 바로가기]({link})"
                send_telegram_message(message)
                print(f"[알림 전송 완료] {title}")

            sent_articles.add(article_num)

    except Exception as e:
        print("조회 중 에러 발생:", e)

def run_bot():
    """백그라운드에서 60초마다 무한 반복하는 함수"""
    print("서버 가동: 기존 게시글 목록을 기억합니다...")
    check_hotdeal(is_first_run=True)
    print(f"초기화 완료. 현재 {len(sent_articles)}개의 글이 인식되었습니다.")
    
    while True:
        time.sleep(60)
        check_hotdeal(is_first_run=False)

# Web Service가 정상 작동하는지 확인하기 위한 기본 주소
@app.route('/')
def keep_alive():
    return "알림 봇이 정상 작동 중입니다!"

if __name__ == "__main__":
    # 크롤러를 백그라운드 스레드로 분리하여 실행
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask 웹 서버 실행
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)