import pandas as pd
from datetime import datetime, timedelta

###############################################
#### 1. 원본 CSV 불러오기 및 세로형(long) 변환 ####
###############################################
df = pd.read_csv(r"D:\검색량_전체.csv")

dfs = []

# 2개 컬럼씩 묶어서 (날짜, 브랜드 검색량) 변환
for i in range(0, df.shape[1], 2):
    date_col = df.columns[i]
    brand_col = df.columns[i + 1]
    brand_name = brand_col  # 브랜드 이름은 컬럼명 그대로 사용

    tmp = df[[date_col, brand_col]].copy()
    tmp.columns = ["date", "search_volume_relative"]
    tmp["brand"] = brand_name
    dfs.append(tmp)

# 세로로 합치기
df_long = pd.concat(dfs, ignore_index=True)

# 날짜 변환
df_long["date"] = pd.to_datetime(df_long["date"])


#######################################
##### 2. 브랜드별 예상 CPC 컬럼 추가 #####
#######################################
cpc_dict = {"비에날씬": 93, "덴마크 유산균": 101, "락토핏": 122}
df_long["cpc_pred"] = df_long["brand"].map(cpc_dict)


#########################################
####### 3. 절대 검색량 및 광고비 추정 #######
#########################################
# 한 달치 데이터 필터링 (어제 기준 최근 30일)
yesterday = datetime.today() - timedelta(days=1)
one_month_ago = yesterday - timedelta(days=30)
df_last_month = df_long[(df_long["date"] >= one_month_ago) & (df_long["date"] <= yesterday)]  # 한달치 데이터 추출

# 한달치 상대검색량 합계 (모든 키워드)
total_relative_searches = df_last_month["search_volume_relative"].sum()
print(f"최근 한 달간 상대검색량 합계: {total_relative_searches}")

# 실제 월간 검색량 (모든 키워드 합계, 기준값)
actual_monthly_searches = 229475

# 스케일링 비율
scaling_factor = actual_monthly_searches / total_relative_searches

# 절대 검색량 및 광고비 계산
df_long["search_volume_abs"] = df_long["search_volume_relative"] * scaling_factor
df_long["ad_spend_est"] = df_long["search_volume_abs"] * df_long["cpc_pred"]

#########################################
########### 4. 최종 데이터 저장 ###########
#########################################
save_path = r"D:\School\5-2\데이터\search_volume_data\search_volume_total.csv"
df_long.to_csv(save_path, index=False, encoding="utf-8-sig")

print(f"저장 완료: {save_path}")
print(df_long.head())
