import requests
import time
import threading
import os
import urllib.parse
from flask import Flask

app = Flask(__name__)

# ================= 설정 값 =================
TELEGRAM_TOKEN = "8870775774:AAH7uofm_bvfkHB-1kUL5_TGP42mJS2mpA4"
CHAT_ID = "523461892"

CLUB_ID = "31731163"
MENU_ID = "1"

# 원래 요청하려던 네이버 API 주소
NAVER_API_URL = f"https://apis.naver.com/cafe-web/cafe2/ArticleList.json?search.clubid={CLUB_ID}&search.queryType=lastArticle&search.menuid={MENU_ID}&search.page=1&search.perPage=15"

# 다른 무료 프록시(CorsProxy)로 교체
PROXY_URL = f"https://corsproxy.io/?{urllib.parse.quote(NAVER_API_URL)}"
# ===========================================

sent_articles = set()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("텔레그램 전송 실패:", e)

def check_hotdeal(is_first_run=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print("\n--- 새 프록시(CorsProxy) 서버를 통해 네이버 접속 중 ---")
        response = requests.get(PROXY_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[디버그] 프록시 서버 응답 실패: {response.status_code}")
            return

        # CorsProxy는 원본 데이터를 반환하므로 바로 JSON 파싱
        data = response.json()
        article_list = data.get('message', {}).get('result', {}).get('articleList', [])
        print(f"[디버그] 우회 성공! 가져온 게시글 수: {len(article_list)}개")

        if len(article_list) == 0:
            return

        for article in reversed(article_list):
            if article.get('type') != 'ARTICLE':
                continue

            article_num = str(article.get('articleId'))
            if article_num in sent_articles:
                continue
            
            title = article.get('subject')
            link = f"https://m.cafe.naver.com/ca-fe/web/cafes/{CLUB_ID}/articles/{article_num}"

            if not is_first_run:
                clean_title = title.replace('[', '').replace(']', '').replace('*', '')
                message = f"🚨 *새로운 게시글 등장!*\n\n📌 {clean_title}\n🔗 [게시글 바로가기]({link})"
                send_telegram_message(message)
                print(f"[알림 전송 완료] {clean_title}")

            sent_articles.add(article_num)

    except Exception as e:
        print(f"[디버그] 프록시 통신 에러 발생: {e}")

def run_bot():
    print("서버 가동: 새 IP 우회 프록시 모드 실행 중...")
    check_hotdeal(is_first_run=True)
    
    while True:
        time.sleep(60)
        check_hotdeal(is_first_run=False)

@app.route('/')
def keep_alive():
    return "Render 새 프록시 우회 봇 작동 중!"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)