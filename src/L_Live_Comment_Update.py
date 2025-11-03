import pandas as pd
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, JavascriptException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 파일명 설정 (기존 파일과 병합 후 저장될 새 파일명)
ORIGINAL_CSV_FILENAME = "L_Live_Comment.csv"
OUTPUT_CSV_FILENAME = "L_Live_Comment_updated.csv"

# =====================================================================================
# [정보 수집 함수]
# =====================================================================================

def setup_driver():
    """크롬 드라이버를 설정합니다."""
    print("크롬 드라이버를 설정...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 백그라운드 실행
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
        print("  - 영상 길이를 찾는 데 실패했음.")
        return None

def get_video_info(driver, video_url):
    """
    하나의 영상 URL에 접속하여 제목, 방송 ID, 총 길이를 추출합니다.
    오류 발생 시 해당 영상을 건너뜁니다.
    """
    original_url = video_url.replace('L_', '', 1)
    print(f"  - 정보 추출 중: {original_url}")

    try:
        broadcast_id = None
        video_title = None
        video_duration = None

        # 1. URL에서 방송 ID 추출
        match = re.search(r'/replays/(\d+)', original_url)
        if match:
            broadcast_id = match.group(1)

        # 2. 페이지 접속
        driver.get(original_url)
        time.sleep(3)

        # 3. 영상 제목 추출
        title_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2[class*='BroadcastTitle_title']"))
        )
        video_title = title_elem.text

        # 4. 영상 길이 추출
        video_duration = get_video_duration(driver)

        if all([video_title, broadcast_id, video_duration is not None]):
            print(f"    ✓ 추출 완료. 제목: {video_title}, 길이: {video_duration}초, ID: {broadcast_id}")
            return video_title, broadcast_id, video_duration
        else:
            raise Exception("필요한 정보 중 일부가 누락되었습니다.")

    except Exception as e:
        print(f"  - 정보 추출 실패. 해당 영상 건너뛰기. 오류: {e}")
        return None, None, None

# =====================================================================================
# [메인 로직]
# =====================================================================================

def main():
    """메인 실행 함수입니다."""
    driver = setup_driver()
    if not driver:
        return

    try:
        if not os.path.exists(ORIGINAL_CSV_FILENAME):
            print(f"오류: '{ORIGINAL_CSV_FILENAME}' 파일이 존재하지 않습니다. 먼저 댓글을 수집하세요.")
            return

        # 1. 기존 댓글 CSV 파일 불러오기
        try:
            df_comments = pd.read_csv(ORIGINAL_CSV_FILENAME, encoding='utf-8-sig')
            print(f"✓ 기존 댓글 파일 '{ORIGINAL_CSV_FILENAME}' 로드 완료. 총 {len(df_comments)}개 댓글.")
        except Exception as e:
            print(f"오류: CSV 파일 로드 중 문제 발생. {e}")
            return

        # video_url 열에서 고유한 URL 목록만 추출
        unique_urls = df_comments['video_url'].unique()
        print(f"✓ 총 {len(unique_urls)}개의 고유한 영상 URL을 찾았습니다.")

        # 2. 각 URL에서 새로운 정보(제목, ID, 길이) 추출
        video_info_list = []
        for i, url in enumerate(unique_urls, 1):
            title, broadcast_id, duration = get_video_info(driver, url)

            if all([title, broadcast_id, duration is not None]):
                video_info_list.append({
                    "video_url": url,
                    "video_title": title,
                    "broadcast_id": broadcast_id,
                    "total_duration(sec)": duration
                })

        # 3. 새로운 정보를 DataFrame으로 변환
        if not video_info_list:
            print("\n수집할 영상 정보가 없습니다. 작업을 종료합니다.")
            return

        df_info = pd.DataFrame(video_info_list)

        # 4. 두 DataFrame을 'video_url'을 기준으로 병합
        print("\n데이터 병합 중...")
        df_merged = pd.merge(df_comments, df_info, on='video_url', how='left')

        # 5. 새로운 CSV 파일로 저장
        df_merged.to_csv(OUTPUT_CSV_FILENAME, index=False, encoding='utf-8-sig')
        print(f"✓ 모든 정보가 병합된 파일이 '{OUTPUT_CSV_FILENAME}'로 저장되었습니다.")

    except Exception as e:
        print(f"\n! 작업 도중 오류 발생: {e}")

    finally:
        if driver:
            print("\n드라이버 종료.")
            driver.quit()

if __name__ == "__main__":
    main()