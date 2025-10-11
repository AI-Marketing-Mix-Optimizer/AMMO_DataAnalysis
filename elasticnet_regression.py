import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

brand = 'B'  # 'B', 'D', 'L' *********************************************************************************************************************************

####################################
######        데이터 준비        #####
####################################
data_path = r"D:\School\5-2\데이터"
# CSV 불러오기
live_df = pd.read_csv(rf"{data_path}\live_info_{brand}_2.csv")
search_df = pd.read_csv(rf"{data_path}\search_volume_total.csv")
search_df = search_df[search_df["brand"].str.contains("비에날씬", na=False)]  # 비에날씬 검색량만
proxy_df = pd.read_csv(rf"{data_path}\proxy_sales_{brand}.csv")

# 경쟁사 파일 선택
brand_competitors = {
    'B': [rf"{data_path}\live_info_D.csv", rf"{data_path}\live_info_L.csv"],
    'D': [rf"{data_path}\live_info_B.csv", rf"{data_path}\live_info_L.csv"],
    'L': [rf"{data_path}\live_info_B.csv", rf"{data_path}\live_info_D.csv"]
}

try:
    competitor_files = brand_competitors[brand]
except KeyError:
    raise ValueError("brand는 'B', 'D', 'L' 중 하나여야 합니다.")

competitor_events = []  # 경쟁사 프로모션 여부

for f in competitor_files:
    df = pd.read_csv(f)[["date", "promotion_flag"]]
    df["date"] = pd.to_datetime(df["date"])
    df["promotion_flag"] = df["promotion_flag"].fillna(0)
    competitor_events.append(df)

# 모든 경쟁사 데이터 합치기
competitor_df = pd.concat(competitor_events)
# 같은 날짜에 이벤트가 하나라도 있으면 1
competitor_df = competitor_df.groupby("date")["promotion_flag"].max().reset_index()
competitor_df.rename(columns={"promotion_flag": "competitor_event_flag"}, inplace=True)

# 날짜 datetime 변환
for df in [live_df, search_df, proxy_df]:
    df["date"] = pd.to_datetime(df["date"])

# 필요한 컬럼만 추출
live_df = live_df[["date", "live_ad_spend_est"]]
search_df = search_df[["date", "ad_spend_est"]]
proxy_df = proxy_df[["date", "proxy_sales"]]

search_df.rename(columns={"ad_spend_est": "search_ad_spend_est"}, inplace=True)

# 날짜 기준으로 병합
merged_df = proxy_df.merge(search_df, on="date", how="outer") \
                     .merge(live_df, on="date", how="outer") \
                     .merge(competitor_df, on="date", how="left") \
                     .fillna(0)

# 7일 단위 그룹 만들기
start_date = merged_df["date"].min()
merged_df["days_since_start"] = (merged_df["date"] - start_date).dt.days
merged_df["week_index"] = (merged_df["days_since_start"] // 7).astype(int)

# 7일 단위로 합계 집계
weekly_df = (
    merged_df.groupby("week_index")[["live_ad_spend_est", "search_ad_spend_est", "proxy_sales", "competitor_event_flag"]]
    .sum().reset_index()
)

# 경쟁사 이벤트 여부 0 이상이면 다 1로
weekly_df["competitor_event_flag"] = (weekly_df["competitor_event_flag"] > 0).astype(int)

# 주 시작일 계산
weekly_df["week_start"] = start_date + pd.to_timedelta(weekly_df["week_index"] * 7, unit="D")
weekly_df = weekly_df[["week_start", "live_ad_spend_est", "search_ad_spend_est", "competitor_event_flag", "proxy_sales"]]

# 데이터 저장
weekly_df.to_csv(rf"{data_path}\elasticnet_data_{brand}.csv", index=False, encoding="utf-8-sig")
# print(weekly_df.head())


########################################
######       ElasticNet 학습       #####
########################################
# feature, label 분리
X = weekly_df[["live_ad_spend_est", "search_ad_spend_est", "competitor_event_flag"]]
y = weekly_df["proxy_sales"]

# 데이터 스케일링 (ElasticNet은 스케일 민감)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# train : test = 8 : 2
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# 데이터 크기 확인
print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")

# alpha: 정규화 강도, l1_ratio: L1(Lasso)/L2(Ridge) 비율
model = ElasticNet(alpha=1.0, l1_ratio=0.5, random_state=42)

# 모델 학습
print('ElasticNet model training start')
model.fit(X_train, y_train)


############################################
######       ElasticNet 성능 평가       #####
############################################
feature_names = ["live_ad_spend_est", "search_ad_spend_est", "competitor_event_flag"]

coefficients = model.coef_  # 회귀 계수
y_pred = model.predict(X_test)  # 예측

# 전체 모델 성능
r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

# 모델 성능 결과 df
results_df = pd.DataFrame({
    "feature": feature_names,
    "beta": coefficients,
    "r2": r2,
    "rmse": rmse
})

# CSV 저장
results_df.to_csv(rf"{data_path}\elasticnet_results_{brand}.csv", index=False, encoding="utf-8-sig")
print('ElasticNet model 결과 저장 완료')