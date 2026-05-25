import requests
import time
import threading
import os
import xml.etree.ElementTree as ET
from flask import Flask

app = Flask(__name__)

# ================= 설정 값 =================
TELEGRAM_TOKEN = "8870775774:AAH7uofm_bvfkHB-1kUL5_TGP42mJS2mpA4"
CHAT_ID = "523461892"

CLUB_ID = "31731163"
MENU_ID = "1"

# API가 아닌, 데이터센터 IP 접근이 허용되는 RSS 피드 주소로 우회
RSS_URL = f"https://cafe.rss.naver.com/ArticleList.nhn?search.clubid={CLUB_ID}&search.menuid={MENU_ID}"
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
        print("\n--- RSS 피드 우회 요청 중 ---")
        response = requests.get(RSS_URL, headers=headers)
        
        if response.status_code != 200:
            print(f"[디버그] RSS 접근 거부됨 (상태 코드: {response.status_code})")
            return

        # HTML이 아닌 XML(RSS) 데이터 파싱
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        
        print(f"[디버그] RSS에서 읽어온 게시글 수: {len(items)}개")

        # 최신 글이 위에 있으므로 역순으로 처리하여 과거 글부터 알림
        for item in reversed(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # 고유 식별자로 링크 자체를 활용
            if link in sent_articles:
                continue

            if not is_first_run:
                # 텔레그램 마크다운 에러 방지를 위해 특수문자 제거
                clean_title = title.replace('[', '').replace(']', '').replace('*', '')
                message = f"🚨 *새로운 게시글 등장!*\n\n📌 {clean_title}\n🔗 [게시글 바로가기]({link})"
                send_telegram_message(message)
                print(f"[알림 전송 완료] {clean_title}")

            sent_articles.add(link)

    except ET.ParseError:
        print("[디버그] 에러: 가져온 데이터가 RSS 형식이 아닙니다. (네이버 방화벽이 HTML 차단 창을 띄움)")
    except Exception as e:
        print(f"[디버그] RSS 파싱 중 알 수 없는 에러 발생: {e}")

def run_bot():
    print("서버 가동: RSS 피드 우회 모드 실행 중...")
    check_hotdeal(is_first_run=True)
    
    while True:
        time.sleep(60)
        check_hotdeal(is_first_run=False)

@app.route('/')
def keep_alive():
    return "RSS 기반 우회 봇 가동 중!"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)