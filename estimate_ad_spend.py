import pandas as pd
import numpy as np

brand = 'D'  # 'B', 'D', 'L' ********************************************************************************************************

# CSV 불러오기
live_df = pd.read_csv(f"data/live_info_{brand}.csv")  # 라이브 정보
prod_df = pd.read_csv(f"data/prod_code_{brand}.csv")  # 상품 정보

# 필요 컬럼만 선택
prod_df = prod_df[["prod_code", "prod_price"]]

# prod_code → prod_price 딕셔너리 (가격 조회 편리)
price_dict = pd.Series(prod_df.prod_price.values, index=prod_df.prod_code).to_dict()

# 라이브 판매 상품 평균 단가 계산
def calc_avg_price(prod_codes_str):
    codes = prod_codes_str.split(",")  # 쉼표로 나누기
    prices = [price_dict.get(code, 0) for code in codes]  # 없으면 0
    return sum(prices) / len(prices) if prices else 0

live_df["avg_price"] = live_df["prod_codes"].apply(calc_avg_price)

cvr = 0.001  # 구매 전환율
# 구매자 수 추정
live_df["purchase_count_est"] = live_df["viewer_count"] * cvr

# 쇼핑라이브 수수료 비율 = 버티컬 사용료 + 판매수수료 + Npay 주문관리 수수료 (VAT 별도)
#                    = 2.7% + 3.64% + 3.63%
fee_rate = 9.97
k = 30  # 스케일링 상수

# live_ad_spend_est 계산
# 라이브 판매상품 평균 단가 * 수수료 * (1 + log(1 + 구매자 수) / 스케일링 상수)
live_df["live_ad_spend_est"] = live_df["avg_price"] * fee_rate * (1 + np.log1p(live_df["purchase_count_est"]) / k)

print(live_df.head())

# 결과 저장
live_df.to_csv(f"live_info_{brand}_2.csv", index=False, encoding="utf-8-sig")