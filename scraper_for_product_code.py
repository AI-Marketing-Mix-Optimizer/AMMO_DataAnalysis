from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

class LiveProductScraper:
    def __init__(self, driver_path, url):
        self.service = Service(driver_path)
        self.driver = webdriver.Edge(service=self.service)
        self.driver.maximize_window()  # 브라우저 시작 후 최대화
        self.url = url
        self.results = []
    
    # 라이브 방송 페이지 로드
    def load_page(self):
        self.driver.get(self.url)
        time.sleep(10)  # 페이지 로드 대기

        # iframe 존재시 전환
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            self.driver.switch_to.frame(iframes[0])

    def click_show_all(self):
        """전체 보기 버튼 클릭 (있으면)"""
        try:
            wait = WebDriverWait(self.driver, 10)
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
    def extract_products(self, start_index=1):
        items = self.driver.find_elements(By.CSS_SELECTOR, "div.ProductList_item_erjbw")
        code_index = start_index
        for item in items:
            try:
                link_tag = item.find_element(By.CSS_SELECTOR, "strong.ProductTitle_wrap_gGxmc a")
                # 상품명
                name = link_tag.text.strip()
                # 상품 url (api 바로 호출 가능한 url은 아님)
                url = link_tag.get_attribute("href")
                # 상품 코드 BP_001, BP_002, ...
                code = f"BP_{code_index:03d}"
                self.results.append((code, name, url))
                code_index += 1
            except:
                # strong a 태그 없으면 건너뜀 (상품이 아님)
                continue
        return code_index  # 여러 라이브 방송 이어서 번호 붙이기 위해
    
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
    time.sleep(5)  # 초기 페이지 로드

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
        time.sleep(3)  # 로딩 대기

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # 더 이상 로드될 방송이 없으면 종료
            break
        last_height = new_height

    return list(broadcast_urls)


def main():
    driver_path = r'D:\School\5-2\edgedriver_win64\msedgedriver.exe'  # 드라이버 경로
    channel_url = "https://shoppinglive.naver.com/channels/51290"  # 브랜드 홈

    # 드라이버로 방송 URL 먼저 수집
    service = Service(driver_path)
    driver = webdriver.Edge(service=service)
    driver.maximize_window()  # 화면 최대화
    broadcast_urls = get_broadcast_urls(driver, channel_url)
    driver.quit()
    print(f"총 {len(broadcast_urls)}개의 방송 발견")
    
    all_results = []  # 상품 추출 결과 넣을 리스트
    existing_urls = set()  # 중복 URL 체크용 집합
    code_index = 1  # 코드 인덱스 1부터 시작

    # 각 쇼핑라이브 크롤링
    for i, url in enumerate(broadcast_urls):
        print(f"[{i+1}/{len(broadcast_urls)}] 크롤링 시작: {url}")
        scraper = LiveProductScraper(driver_path, url)  # LiveProductScraper 객체
        scraper.load_page()
        scraper.click_show_all()
        scraper.scroll_to_load()
        code_index = scraper.extract_products(start_index=code_index)
        all_results.extend(scraper.results)
        scraper.quit()

        print(f"총 {len(scraper.results)}개의 상품 추출 완료")

        # 중복 제외하고 all_results에 추가
        for code, name, prod_url in scraper.results:
            if prod_url not in existing_urls:
                all_results.append((code, name, prod_url))
                existing_urls.add(prod_url)  # 집합에 추가
                code_index += 1


    # CSV 저장
    with open("all_products.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["prod_code", "prod_name", "prod_url"])
        writer.writerows(all_results)

    print(f"총 {len(all_results)}개의 상품 CSV 저장 완료")


if __name__ == "__main__":
    main()