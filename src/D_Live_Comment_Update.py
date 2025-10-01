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

# 파일명 (새로운 컬럼을 포함하여 저장됩니다)
OUTPUT_FILENAME = "D_Live_Comment.csv"
VIDEO_URL_PREFIX = "D_" # URL 식별자

# =====================================================================================
# [함수 정의 영역]
# =====================================================================================

def setup_driver():
    """크롬 드라이버를 설정합니다."""
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
    """채널 페이지를 스크롤하며 모든 다시보기 링크를 수집합니다."""
    print(f"\n'{channel_url}' 페이지로 이동하여 다시보기 링크를 수집.")
    driver.get(channel_url)
    time.sleep(3)

    ordered_links = []
    seen_links = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    print("페이지를 아래로 스크롤하여 모든 영상 링크를 로드...")
    while True:
        # '/replays/'가 포함된 <a> 태그를 찾음
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
    """비디오의 전체 길이를 가져옴 (초)."""
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

def get_video_metadata(driver, video_url):
    """하나의 영상 URL에 접속하여 제목, 방송 ID, 총 길이를 추출합니다."""
    print(f"  - 메타 데이터 추출 중: {video_url}")

    try:
        broadcast_id = None
        video_title = None

        # 1. URL에서 방송 ID 추출 (페이지 접속 전)
        match = re.search(r'/replays/(\d+)', video_url)
        if match:
            broadcast_id = match.group(1)

        # 2. 페이지 접속
        driver.get(video_url)
        time.sleep(3) # 페이지 로드 대기

        # 3. 영상 제목 추출 (개별 영상 페이지의 안정적인 선택자 사용)
        title_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2[class*='BroadcastTitle_title']"))
        )
        # <h2> 내의 <span>에서 최종 텍스트 추출 (슬라이딩 텍스트를 고려)
        video_title = title_elem.find_element(By.CSS_SELECTOR, "span[class*='SlidingText_text']").text

        # 4. 영상 길이 추출
        video_duration = get_video_duration(driver)

        if all([video_title, broadcast_id, video_duration is not None]):
            print(f"    ✓ 메타데이터 추출 완료. 제목: {video_title}, 길이: {video_duration}초, ID: {broadcast_id}")
            return video_title, broadcast_id, video_duration
        else:
            print("  - 메타데이터 추출 실패: 제목, ID 또는 길이가 누락되었습니다.")
            return None, None, None

    except Exception as e:
        print(f"  - 메타데이터 추출 중 오류 발생. 건너뜀. 오류: {e}")
        return None, None, None


def scrape_comments_from_video(driver, video_url, video_title, broadcast_id, total_duration):
    """주어진 메타데이터와 함께 시간대별 댓글을 모두 수집합니다."""
    # 이미 접속한 페이지를 재사용 (get_video_metadata에서 접속했기 때문에)
    # 하지만 안정성을 위해 페이지 메타데이터 수집 후 댓글 수집 시 페이지를 다시 로드하거나,
    # 메타데이터 수집 후 바로 댓글 수집을 진행할 수 있습니다. 여기서는 안정성을 위해 메타데이터 수집 후
    # 페이지는 이미 로딩되어 있다고 가정하고 댓글을 수집합니다.

    # 총 길이는 이미 get_video_metadata 과정에서 얻었으므로 재계산하지 않습니다.
    if not total_duration:
        return [] # 길이가 없으면 댓글 수집 불가

    video_comments = []
    processed_comment_ids = set()

    print("  - 시간대별 댓글 수집 시작...")
    # 타임라인을 점프하며 댓글 수집
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
                        video_comments.append({
                            "video_url": f"{VIDEO_URL_PREFIX}{video_url}",
                            "video_title": video_title,         # 새 컬럼
                            "broadcast_id": broadcast_id,       # 새 컬럼
                            "total_duration(sec)": total_duration,   # <-- 수정된 부분 1: 딕셔너리 키 변경
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
            # 새로운 컬럼 3개 추가: video_title, broadcast_id, total_duration
            # fieldnames를 'total_duration(sec)'로 변경해야 합니다.
            fieldnames = ['video_url', 'video_title', 'broadcast_id', 'total_duration(sec)', 'time', 'nickname', 'comment'] # <-- 수정된 부분 2: CSV 헤더 변경
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

            if not file_exists:
                writer.writeheader()

            writer.writerows(data)

        print(f"  - ✓ '{filename}'에 {len(data)}개 댓글 추가 저장 완료.")

    except Exception as e:
        print(f"✗ CSV 파일 저장 중 오류 발생: {e}")


if __name__ == "__main__":
    driver = setup_driver()

    if driver:
        # 최종 파일명
        output_filename = OUTPUT_FILENAME

        # 스크립트를 새로 시작할 때, 이전 결과 파일이 있다면 삭제
        if os.path.exists(output_filename):
            print(f"\n기존 '{output_filename}' 파일을 삭제하고 새로 시작")
            os.remove(output_filename)

        try:
            # 1. 모든 영상 링크 수집
            replay_urls = get_replay_links(driver, CHANNEL_URL)

            # 2. 모든 영상 처리 (46개 제한 제거)
            urls_to_process = replay_urls
            print(f"\n총 {len(urls_to_process)}개의 모든 영상을 대상으로 크롤링을 시작합니다.")

            total_comments_count = 0
            for i, url in enumerate(urls_to_process, 1):
                print(f"\n[{i}/{len(urls_to_process)}] 번째 영상 처리 시작...")

                # 메타데이터 (제목, ID, 길이) 추출
                video_title, broadcast_id, total_duration = get_video_metadata(driver, url)

                comments = []
                if total_duration:
                    # 메타데이터를 사용하여 댓글 수집
                    # get_video_metadata에서 이미 페이지에 접속했으므로 driver.get(url)을 다시 호출할 필요 없음
                    comments = scrape_comments_from_video(driver, url, video_title, broadcast_id, total_duration)

                if comments:
                    append_to_csv(output_filename, comments)
                    total_comments_count += len(comments)
                else:
                    print("  - 해당 영상에서 댓글을 찾지 못했거나 메타데이터가 불완전하여 건너뜁니다.")


            print(f"\n\n======= 최종 수집 완료 =======")
            print(f"총 {len(urls_to_process)}개 영상에서 {total_comments_count}개의 댓글을 수집하여 '{output_filename}'에 저장했음")

        except Exception as e:
            print(f"\n! 크롤링 도중 예상치 못한 오류 발생: {e}")

        finally:
            print("\n모든 작업을 종료하고 드라이버를 닫음")
            driver.quit()
