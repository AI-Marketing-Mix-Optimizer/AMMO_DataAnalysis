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
data_path = r"data"
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

# 정렬 (시계열 순서 유지)
merged_df = merged_df.sort_values("date").reset_index(drop=True)

# Lag / Rolling 추가
model_input_df = merged_df.copy()

# 광고비 lag (3일)
model_input_df["search_ad_spend_lag3"] = model_input_df["search_ad_spend_est"].shift(3)
model_input_df["live_ad_spend_lag3"] = model_input_df["live_ad_spend_est"].shift(3)

# 광고비 rolling sum (7일 누적합)
model_input_df["search_ad_spend_7d_sum"] = (
    model_input_df["search_ad_spend_est"].rolling(window=7, min_periods=1).sum()
)
model_input_df["live_ad_spend_7d_sum"] = (
    model_input_df["live_ad_spend_est"].rolling(window=7, min_periods=1).sum()
)

# 경쟁사 이벤트 lag (3일)
model_input_df["competitor_event_flag_lag3"] = model_input_df["competitor_event_flag"].shift(3)

# month 변수 추가
model_input_df["month"] = model_input_df["date"].dt.month

# NaN 처리
model_input_df = model_input_df.fillna(0)

# 최종 feature 순서 정리
final_columns = [
    "date",
    "search_ad_spend_est",
    "live_ad_spend_est",
    "search_ad_spend_lag3",
    "live_ad_spend_lag3",
    "search_ad_spend_7d_sum",
    "live_ad_spend_7d_sum",
    "competitor_event_flag",
    "competitor_event_flag_lag3",
    "month",
    "proxy_sales"
]

model_input_df = model_input_df[final_columns]

# 데이터 저장
model_input_df.to_csv(rf"{data_path}\elasticnet_data_{brand}.csv", index=False, encoding="utf-8-sig")


# # 7일 단위 데이터 구축 (Optional)
# start_date = merged_df["date"].min()
# merged_df["days_since_start"] = (merged_df["date"] - start_date).dt.days
# merged_df["week_index"] = (merged_df["days_since_start"] // 7).astype(int)
#
# # 7일 단위로 합계 집계
# weekly_df = (
#     merged_df.groupby("week_index")[["live_ad_spend_est", "search_ad_spend_est", "proxy_sales", "competitor_event_flag"]]
#     .sum().reset_index()
# )
#
# # 주 시작일 계산
# weekly_df["week_start"] = start_date + pd.to_timedelta(weekly_df["week_index"] * 7, unit="D")
# weekly_df = weekly_df[["week_start", "live_ad_spend_est", "search_ad_spend_est", "competitor_event_flag", "proxy_sales"]]
#
# # 경쟁사 이벤트 여부 0 이상이면 다 1로
# weekly_df["competitor_event_flag"] = (weekly_df["competitor_event_flag"] > 0).astype(int)
#
# # 데이터 저장
# weekly_df.to_csv(rf"{data_path}\elasticnet_data_week_{brand}.csv", index=False, encoding="utf-8-sig")


##################################################
######       ElasticNet 학습 및 성능 평가       #####
##################################################

# 실험을 위한 feature set 정의
base_feats = ["search_ad_spend_est", "live_ad_spend_est", "competitor_event_flag"]
lag_feats = ["search_ad_spend_lag3", "live_ad_spend_lag3", "competitor_event_flag_lag3"]
roll_feats = ["search_ad_spend_7d_sum", "live_ad_spend_7d_sum"]

feature_sets = {
    "baseline": base_feats,
    "lag_added": base_feats + lag_feats,
    "rolling_added": base_feats + roll_feats,
    "lag_rolling_added": base_feats + lag_feats + roll_feats
}

all_results = []  # 결과 저장용

# 각 feature set별로 ElasticNet 학습
for exp_name, feature_cols in feature_sets.items():
    print(f"\n\n==============================")
    print(f"▶ [ {exp_name} ] ")
    print("==============================")

    # feature, label 분리
    X = model_input_df[feature_cols]
    y = model_input_df["proxy_sales"]

    # 데이터 스케일링
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # train : test = 8 : 2
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # 데이터 크기 확인
    print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")

    # alpha: 정규화 강도, l1_ratio: L1(Lasso)/L2(Ridge) 비율
    model = ElasticNet(alpha=1.0, l1_ratio=0.5, random_state=42)

    # 모델 학습
    model.fit(X_train, y_train)

    # 성능 평가
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    # 계수 복원
    beta_real = model.coef_ / scaler.scale_
    intercept_real = model.intercept_ - np.sum(scaler.mean_ * model.coef_ / scaler.scale_)

    # feature별 결과 기록
    for i, f in enumerate(feature_cols):
        all_results.append({
            "experiment": exp_name,
            "feature": f,
            "beta_scaled": model.coef_[i],
            "beta_real": beta_real[i],
            "intercept": "",
            "R2": "",
            "RMSE": ""
        })

    # intercept, R2, RMSE 기록 (feature=None)
    all_results.append({
        "experiment": exp_name,
        "feature": "intercept",
        "beta_scaled": model.intercept_,
        "beta_real": intercept_real,
        "intercept": intercept_real,
        "R2": r2,
        "RMSE": rmse
    })

# -----------------------------
# DataFrame 생성 및 CSV 저장
# -----------------------------
results_df = pd.DataFrame(all_results)
results_df.to_csv(rf"elasticnet_results_experiments_{brand}.csv", index=False, encoding="utf-8-sig")

print("All training and results saving completed.")