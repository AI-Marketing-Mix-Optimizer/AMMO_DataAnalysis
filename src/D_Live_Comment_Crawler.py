import time
import csv
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import JavascriptException, NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =====================================================================================
# [사용자 설정 영역]
# =====================================================================================

# 다시보기 영상 목록 채널 페이지의 URL
CHANNEL_URL = "https://shoppinglive.naver.com/search/lives?query=%EB%8D%B4%EB%A7%88%ED%81%AC%EC%9C%A0%EC%82%B0%EA%B7%A0%20%EC%8A%AC%EB%A6%BC&sort=RECENT"

# 시간 점프 설정 (초)
JUMP_INTERVAL_SECONDS = 300  # 300초 = 5분

# 댓글 로드될 때까지 설정.
POST_JUMP_WAIT_SECONDS = 2

# =====================================================================================
# [메인 로직]
# =====================================================================================

def setup_driver():
    print("크롬 드라이버를 설정...")
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # 백그라운드 실행을 원할 경우 주석 해제
    options.add_argument('--log-level=3')
    options.add_argument("--mute-audio")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("✓ 드라이버 설정 완료.")
        return driver
    except Exception as e:
        print(f"✗ 드라이버 설정 중 에러 발생: {e}")
        return None

def get_replay_links(driver, channel_url):
    print(f"\n'{channel_url}' 페이지로 이동하여 다시보기 링크를 수집.")
    driver.get(channel_url)
    time.sleep(3)

    ordered_links = []
    seen_links = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    print("페이지를 아래로 스크롤하여 모든 영상 링크를 로드...")
    while True:
        replay_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/replays/']")
        for elem in replay_elements:
            link = elem.get_attribute('href')
            if link and link not in seen_links:
                ordered_links.append(link)
                seen_links.add(link)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    print(f"✓ 총 {len(ordered_links)}개의 다시보기 영상 링크를 찾음")

    print("\n--- 수집된 URL 목록 (처리 순서) ---")
    if not ordered_links:
        print("수집된 URL이 없음")
    else:
        for idx, link in enumerate(ordered_links, 1):
            print(f"{idx}. {link}")
    print("------------------------------------")

    return ordered_links

def get_video_duration(driver):
    """비디오의 전체 길이를 가져옴 (초)"""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
        duration = driver.execute_script("return document.querySelector('video').duration")
        if duration:
            print(f"  - 영상 길이: {time.strftime('%H:%M:%S', time.gmtime(duration))} ({int(duration)}초)")
            return duration
        return None
    except (JavascriptException, TimeoutException):
        print("  - 영상 길이를 찾는 데 실패")
        return None

def jump_to_time(driver, seconds):
    """비디오를 특정 시간으로 이동."""
    try:
        driver.execute_script(f"document.querySelector('video').currentTime = {seconds};")
        return seconds
    except JavascriptException:
        return None

def scrape_comments_from_video(driver, video_url):
    """하나의 영상 URL에 접속하여 시간대별 댓글을 모두 수집"""
    driver.get(video_url)
    print("\n----------------------------------------------------")
    print(f"영상 URL: {video_url}")
    print("  - 페이지 로드 대기 중...")
    time.sleep(5)

    total_duration = get_video_duration(driver)
    if not total_duration:
        return []

    video_comments = []
    processed_comment_ids = set()

    print("  - 시간대별 댓글 수집 시작...")
    for seconds in range(0, int(total_duration), JUMP_INTERVAL_SECONDS):
        current_time = jump_to_time(driver, seconds)
        if current_time is not None:
            time_str = time.strftime('%H:%M:%S', time.gmtime(current_time))
            print(f"    -> [{time_str}] 시간대로 이동...")
            time.sleep(POST_JUMP_WAIT_SECONDS)

            comment_elements = driver.find_elements(By.CSS_SELECTOR, "div.Comment_wrap_wRrdF")
            for elem in comment_elements:
                try:
                    nickname = elem.find_element(By.CSS_SELECTOR, "strong.NormalComment_nickname_K2\\+Tx").text
                    comment_text = elem.find_element(By.CSS_SELECTOR, "span.NormalComment_comment_Yqlnf").text
                    unique_id = f"[{nickname}] {comment_text}"

                    if unique_id not in processed_comment_ids:
                        prefix_video_url = f"D_{video_url}"
                        video_comments.append({
                            "video_url": prefix_video_url,
                            "time": time_str,
                            "nickname": nickname,
                            "comment": comment_text
                        })
                        processed_comment_ids.add(unique_id)
                except (NoSuchElementException, StaleElementReferenceException):
                    continue

    print(f"  - ✓ 영상 수집 완료. 총 {len(video_comments)}개의 댓글 발견.")
    return video_comments

def append_to_csv(filename, data):
    """수집된 댓글 데이터를 CSV 파일에 이어서 저장"""
    if not data:
        return

    file_exists = os.path.isfile(filename)

    try:
        with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['video_url', 'time', 'nickname', 'comment']
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

            if not file_exists:
                writer.writeheader()

            writer.writerows(data)

        print(f"  - ✓ '{filename}'에 {len(data)}개 댓글 추가 저장 완료.")

    except Exception as e:
        print(f"✗ CSV 파일 저장 중 오류 발생: {e}")

def get_channel_id_from_url(url):
    """URL에서 채널 ID나 검색어를 추출하여 파일 이름을 생성"""
    # 채널 URL 형식일 경우 채널 ID 추출
    match_channel = re.search(r'/channels/(\d+)', url)
    if match_channel:
        return match_channel.group(1)

    # 검색 URL 형식일 경우 검색어 추출 (간단한 버전)
    match_query = re.search(r'query=([^&]+)', url)
    if match_query:
        return match_query.group(1)

    return "unknown"


if __name__ == "__main__":
    driver = setup_driver()

    if driver:
        channel_id = get_channel_id_from_url(CHANNEL_URL)
        output_filename = f"D_comments_channel_{channel_id}.csv"

        if os.path.exists(output_filename):
            print(f"\n기존 '{output_filename}' 파일을 삭제하고 새로 시작")
            os.remove(output_filename)

        try:
            replay_urls = get_replay_links(driver, CHANNEL_URL)

            # 앞에서부터 46개의 영상만 선택
            urls_to_process = replay_urls[:46]
            print(f"\n총 {len(replay_urls)}개의 영상 중, 앞에서부터 {len(urls_to_process)}개만 크롤링")

            total_comments_count = 0
            for i, url in enumerate(urls_to_process, 1):
                print(f"\n[{i}/{len(urls_to_process)}] 번째 영상 댓글 수집 시작...")
                comments = scrape_comments_from_video(driver, url)

                if comments:
                    append_to_csv(output_filename, comments)
                    total_comments_count += len(comments)

            print(f"\n\n======= 최종 수집 완료 =======")
            print(f"총 {len(urls_to_process)}개 영상에서 {total_comments_count}개의 댓글을 수집하여 '{output_filename}'에 저장했음")

        except Exception as e:
            print(f"\n! 크롤링 도중 예상치 못한 오류 발생: {e}")

        finally:
            print("\n모든 작업을 종료하고 드라이버를 닫음")
            driver.quit()