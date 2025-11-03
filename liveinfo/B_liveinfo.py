from playwright.sync_api import sync_playwright
import requests
import pandas as pd

CHANNEL_URL = "https://shoppinglive.naver.com/channels/51290"  # 비엔날씬 채널
OUTFILE = "B_liveinfo.csv"  # 결과 파일명

def get_broadcast_detail(session, broadcast_id, referer):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": referer,
        "Accept": "application/json, text/plain, */*"
    }
    detail_url = f"https://apis.naver.com/live_commerce_web/viewer_api_web/v1/broadcast/{broadcast_id}?needTimeMachine=true"
    counts_url = f"https://apis.naver.com/live_commerce_web/viewer_api_web/v1/broadcast/{broadcast_id}/counts"
    promo_url = f"https://apis.naver.com/live_commerce_web/viewer_api_web/v1/promotions?broadcastId={broadcast_id}"

    try:
        r = session.get(detail_url, headers=headers, timeout=10)
        detail = r.json() if r.status_code == 200 else {}
    except:
        detail = {}

    try:
        r2 = session.get(counts_url, headers=headers, timeout=10)
        counts = r2.json() if r2.status_code == 200 else {}
    except:
        counts = {}

    try:
        r3 = session.get(promo_url, headers=headers, timeout=10)
        promos = r3.json().get("events", []) if r3.status_code == 200 else []
    except:
        promos = []

    # 방송 시간 처리
    date = start_time = end_time = ""
    duration_min = 0
    if detail.get("startDate") and detail.get("endDate"):
        try:
            start_ts = pd.to_datetime(detail["startDate"])
            end_ts = pd.to_datetime(detail["endDate"])
            date = str(start_ts.date())
            start_time = str(start_ts.time()).split(".")[0]
            end_time = str(end_ts.time()).split(".")[0]
            duration_min = int((end_ts - start_ts).total_seconds() // 60)
        except:
            pass

    live_name = detail.get("title", "") if isinstance(detail, dict) else ""
    viewer_count = counts.get("viewerCount", 0) if isinstance(counts, dict) else 0
    promotion_flag = 1 if promos else 0
    promotion_text = "; ".join([
        f"{p.get('name','')} / {p.get('mission','')} / {p.get('reward',{}).get('giveawayName','')}"
        for p in promos
    ])

    return {
        "broadcast_id": broadcast_id,
        "live_name": live_name,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "duration_min": duration_min,
        "viewer_count": viewer_count,
        "promotion_flag": promotion_flag,
        "promotion_text": promotion_text,
        "url": f"https://view.shoppinglive.naver.com/replays/{broadcast_id}"
    }

def main():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=True로 하면 창 안 뜸
        context = browser.new_context()
        page = context.new_page()
        print("채널 페이지 이동:", CHANNEL_URL)
        page.goto(CHANNEL_URL, timeout=30000)

        try:
            page.wait_for_selector("a[href*='/replays/']", timeout=15000)
        except:
            print("replay 카드가 나타나지 않음")
            browser.close()
            return

        # 무한 스크롤 + 더보기
        prev_count = 0
        while True:
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            load_more = page.query_selector("button:has-text('더보기')")
            if load_more:
                try:
                    load_more.click()
                    page.wait_for_timeout(800)
                except:
                    pass
            cards = page.query_selector_all("a[href*='/replays/']")
            curr_count = len(cards)
            if curr_count == prev_count:
                break
            prev_count = curr_count

        urls = [card.get_attribute("href") for card in cards if card.get_attribute("href")]
        urls = list(dict.fromkeys(urls))
        print("최종 방송 카드 개수:", len(urls))

        # 쿠키를 requests 세션에 옮기기
        cookies = context.cookies()
        session = requests.Session()
        for c in cookies:
            session.cookies.set(c["name"], c["value"], domain=c.get("domain"), path=c.get("path"))

        referer = CHANNEL_URL

        for url in urls:
            if "replays" not in url:
                continue
            broadcast_id = url.split("/replays/")[-1].split("?")[0]
            info = get_broadcast_detail(session, broadcast_id, referer)
            if info:
                results.append(info)
                print(f"저장: {info['live_name']} ({info['date']} {info['start_time']})")

        browser.close()

    if results:
        df = pd.DataFrame(results)
        df.to_csv(OUTFILE, index=False, encoding="utf-8-sig")
        print(f"CSV 저장 완료: {len(df)} 행 → {OUTFILE}")
    else:
        print("수집된 데이터 없음")

if __name__ == "__main__":
    main()
