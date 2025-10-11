import pandas as pd
from datetime import datetime, timedelta

# CSV 파일 불러오기
df = pd.read_csv(r"D:\School\5-2\데이터\search_volume_data\search_volume_total_before.csv")

############################
### 예상 평균 CPC 컬럼 추가 ###
############################
# brand별 CPC 값 딕셔너리로 정의
cpc_dict = {"비에날씬": 93, "덴마크 유산균": 101, "락토핏": 122}

# brand 컬럼 기준으로 cpc_pred 컬럼 추가
df["cpc_pred"] = df["brand"].map(cpc_dict)


##################################
### 절대 검색량 추정 (단순 비례법) ###
##################################
df["date"] = pd.to_datetime(df["date"]) # date 컬럼 datetime으로 변환
yesterday = datetime.today() - timedelta(days=1)  # 어제 날짜
one_month_ago = yesterday - timedelta(days=30) # 한 달 전 날짜
df_last_month = df[(df["date"] >= one_month_ago) & (df["date"] <= yesterday)] # 한 달치 데이터 추출

# 한 달치 상대검색량 합계 (모든 키워드)
total_relative_searches = df_last_month["search_volume_relative"].sum()
print(total_relative_searches)

# 실제 월간 검색량 (모든 키워드)
actual_monthly_searches = 229475

# 절대검색량 = 각 row 상대검색량 * (실제 한 달치 전체 검색량 / 한 달치 상대검색량 합계)
scaling_factor = actual_monthly_searches / total_relative_searches
df["search_volume_abs"] = df["search_volume_relative"] * scaling_factor

# 예상 광고비 계산
df["ad_spend_est"] = df["search_volume_abs"] * df["cpc_pred"]

# 수정된 데이터프레임 저장
df.to_csv(r"D:\School\5-2\데이터\search_volume_data\search_volume_total.csv", index=False, encoding="utf-8-sig")

print(df.head())