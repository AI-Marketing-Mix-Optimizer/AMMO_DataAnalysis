import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

brand = 'B'  # 'B', 'D', 'L' *********************************************************************************************************************************

##################################################
######       ElasticNet 학습 및 성능 평가       #####
##################################################
# 데이터셋 불러오기
data_path = r"data"
model_input_df = pd.read_csv(rf"{data_path}\elasticnet_data_{brand}.csv.csv")

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

# df 생성 및 CSV 저장
results_df = pd.DataFrame(all_results)
results_df.to_csv(rf"elasticnet_experiments_results_{brand}.csv", index=False, encoding="utf-8-sig")

print("All training and results saving completed.")