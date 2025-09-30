from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs, unquote
import time
import csv


class LiveScraper:
    def __init__(self, driver_path, url):
        self.service = Service(driver_path)
        self.driver = webdriver.Edge(service=self.service)
        self.driver.maximize_window()  # 브라우저 시작 후 최대화
        self.url = url
        self.results = []
    
    # 라이브 방송 페이지 로드
    def load_page(self):
        self.driver.get(self.url)
        time.sleep(3)  # 페이지 로드 대기

        # iframe 존재시 전환
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            self.driver.switch_to.frame(iframes[0])

    def click_show_all(self):
        try:
            wait = WebDriverWait(self.driver, 5)
            buttons = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "button")))
            clicked = False
            for b in buttons:
                # print(b.text)
                if "전체 보기" in b.text:
                    b.click()
                    clicked = True
                    # print("'전체 보기' 버튼 클릭 완료")
                    time.sleep(3)  # 클릭 후 로딩 대기
                    break
            if not clicked:
                print("'전체 보기' 버튼이 없거나 이미 전체 표시됨")
        except Exception as e:
            print("버튼 클릭 오류:", e)

    # 스크롤하여 모든 상품 로딩
    def scroll_to_load(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    # 상품 정보 추출 (상품명, url)
    def extract_products(self):
        items = self.driver.find_elements(By.CSS_SELECTOR, "div.ProductList_item_erjbw")
        for item in items:
            try:
                link_tag = item.find_element(By.CSS_SELECTOR, "strong.ProductTitle_wrap_gGxmc a")
                # 상품명
                name = link_tag.text.strip()

                # 브리지 URL (네이버 쇼핑라이브 중계용 주소)
                raw_url = link_tag.get_attribute("href")

                # raw_url 내 sourceUrl 디코딩 -> 실제 상품 url 복원
                parsed = urlparse(raw_url)
                qs = parse_qs(parsed.query)
                if "sourceUrl" in qs:
                    prod_url = unquote(qs["sourceUrl"][0])  # 디코딩된 실제 URL
                else:
                    prod_url = raw_url

                self.results.append((name, prod_url))

            except:
                # strong a 태그 없으면 건너뜀 (상품이 아님)
                continue
        return self.results
    
    # csv 저장
    def save_csv(self, filename):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["prod_code", "prod_name", "prod_url"])
            writer.writerows(self.results)
    
    # 브라우저 종료
    def quit(self):
        self.driver.quit()


# 전체 쇼핑라이브 url 리스트 얻기
def get_broadcast_urls(driver, channel_url):
    driver.get(channel_url)
    time.sleep(3)  # 초기 페이지 로드

    broadcast_urls = set()  # 중복 제거
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # 방송 링크 추출
        links = driver.find_elements(By.CSS_SELECTOR, "a.VideoBoxLinkWrapper_wrap_GLkZS")
        for a in links:
            href = a.get_attribute("href")
            if href:
                broadcast_urls.add(href)

        # 스크롤해서 전체 라이브 얻기
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 로딩 대기

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # 더 이상 로드될 방송이 없으면 종료
            break
        last_height = new_height

    return list(broadcast_urls)

# csv 저장
def save_to_csv(data, filename, headers=None, encoding="utf-8-sig"):
    with open(filename, "w", newline="", encoding=encoding) as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        writer.writerows(data)


def main():
    driver_path = r'D:\School\5-2\edgedriver_win64\msedgedriver.exe'  # 드라이버 경로

    # 브랜드 정보 딕셔너리
    brand_info = {
        'B': {'url': "https://shoppinglive.naver.com/channels/51290", 'prod_prefix': 'BP', 'live_prefix': 'BL', 'name': '비에날씬'},
        'D': {'url': "https://shoppinglive.naver.com/channels/26959", 'prod_prefix': 'DP', 'live_prefix': 'DL', 'name': '덴마크'},
        'L': {'url': "https://shoppinglive.naver.com/channels/12886", 'prod_prefix': 'LP', 'live_prefix': 'LL', 'name': '락토핏'}
    }

    # 사용할 브랜드 (비에날씬, 덴마크, 락토핏)
    brand = 'D'  # 'B', 'D', 'L' *********************************************************************************************************************************
    channel_url = brand_info[brand]['url']
    prod_prefix = brand_info[brand]['prod_prefix']
    live_prefix = brand_info[brand]['live_prefix']
    brand_name = brand_info[brand]['name']

    # 드라이버로 방송 URL 먼저 수집
    service = Service(driver_path)
    driver = webdriver.Edge(service=service)
    driver.maximize_window()  # 화면 최대화
    broadcast_urls = get_broadcast_urls(driver, channel_url)
    driver.quit()
    print(f"총 {len(broadcast_urls)}개의 방송 발견")

    live_results = []
    prod_results = []
    existing_names = set()  # 중복 상품 체크용 집합
    prod_index = 1  # 상품 코드 인덱스 1부터 시작

    # 각 쇼핑라이브 크롤링
    for i, url in enumerate(broadcast_urls):
        print(f"[{i+1}/{len(broadcast_urls)}] 크롤링 시작: {url}")
        scraper = LiveScraper(driver_path, url)  # LiveScraper 객체
        scraper.load_page()
        scraper.click_show_all()
        scraper.scroll_to_load()

        # 라이브 제목
        try:
            meta_tag = scraper.driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']")
            live_name = meta_tag.get_attribute("content").strip()
        except:
            try:
                live_name = scraper.driver.title.strip()
            except:
                live_name = f"라이브_{i + 1}"
        live_code = f"{live_prefix}_{i+1:03d}"  # 라이브 코드
        live_results.append((live_code, live_name, url))

        products = scraper.extract_products()  # (name, url) 리스트

        # 중복 제외하고 prod_results에 추가
        for name, prod_url in products:
            if name not in existing_names:
                # 상품 코드 BP_001, BP_002, ...
                code = f"{prod_prefix}_{prod_index:03d}"
                prod_results.append((code, name, prod_url))
                existing_names.add(name)  # 집합에 추가
                prod_index += 1

        scraper.quit()
        print(f"총 {len(products)}개의 상품 추출 완료")

    # CSV 저장
    save_to_csv(live_results, f"라이브코드_{brand_name}.csv", ["live_code", "live_name", "live_url"])
    print(f"총 {len(live_results)}개의 라이브 CSV 저장 완료")
    save_to_csv(prod_results, f"상품코드_{brand_name}.csv", ["prod_code", "prod_name", "prod_url"])
    print(f"총 {len(prod_results)}개의 상품 CSV 저장 완료")


if __name__ == "__main__":

    main()
