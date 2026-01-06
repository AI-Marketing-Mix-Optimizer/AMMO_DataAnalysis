# AI Marketing Mix Optimizer (AMMO)

## 🎯 프로젝트 목표
광고 채널별 ROI 분석 및 LLM 기반 최적 예산 배분 추천 시스템 개발

---
## 🏷️ 개요
-	광고 채널별 매출 및 ROI를 정량 비교하고 예산 효율을 극대화하는 ‘AI 기반 마케팅 의사결정 지원 시스템’ 개발
-	ElasticNet 회귀 모델을 적용한 ROI 분석으로 광고 채널별 성과 및 매출 기여도 산출
-	정형(검색광고 등)·비정형(쇼핑라이브 등) 데이터를 통합 분석해 채널 간 최적 예산 배분 전략 제시
-	담당자의 경험 의존도를 줄이고 데이터 기반의 합리적 마케팅 의사결정을 지원

---
## 📈 프로젝트 내용
- 데이터 수집 및 전처리
  - 대상 브랜드(비에날씬)의 검색량, CPC, 방송 지표, 리뷰 등 핵심 변수를 정제하여 학습용 데이터셋 구축
  - 실제 광고비 및 매출액 데이터가 제공되지 않아, 이를 추정하기 위한 수식을 설계하여 광고비 및 매출액 산출
    
- ElasticNet 회귀 모델을 활용한 광고 채널별 매출액 및 ROI 예측
- 광고비 및 경쟁사 이벤트 여부에 따른 매출 변화 시뮬레이터 개발
- GPT-4o 기반 결과 해석 및 대화형 상담 봇 구현

---
## 🧩 시스템 구조도
<img width="585" height="345" alt="그림1" src="https://github.com/user-attachments/assets/0c7dc721-91d4-4550-b762-fb5dcce87a5a" />

---
## 🧮 Proxy 매출·광고비 산출 로직
- 검색량 추정
  
  - 네이버 데이터랩 : 전체 기간의 검색량 확인 가능. 그러나 기간 내 최대 검색량을 100으로 뒀을 때의 상대 검색량임
  - 네이버 검색광고 플랫폼 : 실제 검색량과 예상 cpc 확인 가능. 그러나 최근 1개월 것만 확인 가능
  - 절대 검색량 추청 : 데이터랩의 최근 1개월 검색량을 기준으로 검색광고 플랫폼 검색량과의 비례 관계를 가정하여 추정
  - cpc 추정 : 네이버 검색광고 플랫폼에서 확인할 수 있는 키워드 별 예상 cpc 사용

- 검색광고 광고비 추정
```
절대 검색량 x cpc
```

- 쇼핑라이브 광고비 추정
```
live_ad_spend = price x fee_rate x (1 + log(1 + purchase_count) / k )
```

  - price : 해당 쇼핑라이브에서 판매한 상품들의 평균 가격
  - fee_rate : 네이버 쇼핑라이브 고객센터에 공시된 수수료
  - purchase_count : 시청자수 x cvr(구매전환율). cvr=0.1%로 설정
  - k : 스케일링 상수. k=30으로 설정


- 매출액 추정
```
proxy_sales = search_volume + review_count + avg_rating + live_duration + live_viewers + promotion_flag
```

  - search_volume : 검색량
  - review_count : 해당 날짜의 리뷰 수
  - avg_rating : 해당 날짜 리뷰들의 별점 평균
  - live_duration : 쇼핑라이브 진행시간(분)
  - live_viewers : 쇼핑라이브 시청자수 (다시보기 조회수 포함)
  - promotion_flag : 쇼핑라이브 프로모션 여부 (0/1)

  - 2024년 비에날씬 매출액이 2688억 원인 것을 이용하여 단순 비례 방식으로 전체 날짜 매출액 추정.

---
## 🔎 화면 예시
<img width="1910" height="937" alt="스크린샷 2026-01-06 213311" src="https://github.com/user-attachments/assets/9dd6a386-4b43-4daa-89a4-ec9fdd73a3c3" />

<img width="1884" height="937" alt="스크린샷 2026-01-06 213518" src="https://github.com/user-attachments/assets/22cce23e-e5e0-43af-af7c-9f84d8d73959" />

---
## 💡 기대효과
-	광고 채널별 ROI 분석을 통한 광고비 효율화 및 매출 극대화
-	데이터 기반 근거를 확보해 예산 조정과 전략 수립에 신뢰성을 부여 
-	효율적 광고 집행을 통한 시장 경쟁력 강화

---
## 🛠️ 주요 적용 기술
개발언어 : Python, JavaScript  
개발도구 : VS Code, PyCharm, Conda, GitHub  
기술스택 : Selenium, Playwright, Scikit-learn, GPT-4o

---
## 🔗 AI-Marketing-Mix-Optimizer Web 코드
**[AMMO Web Repository](https://github.com/AI-Marketing-Mix-Optimizer/AMMO_Web)**


