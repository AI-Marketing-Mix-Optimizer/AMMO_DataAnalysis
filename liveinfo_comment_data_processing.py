import pandas as pd

brand = 'B'  # 'B', 'D', 'L' *********************************************************************************************************************************

# CSV 불러오기
df = pd.read_csv(rf"D:\School\5-2\{brand}_liveinfo.csv")
codes_df = pd.read_csv(rf"D:\School\5-2\데이터\shoppinglive_data\live_code_{brand}.csv")

# 기존 df 행 수 확인
print("Number of rows before merge : ", len(df))

# df 컬럼명 변경
df = df.rename(columns={"url": "live_url"})

# live_url 앞의 불필요한 부분 제거 (존재할 때만)
df["live_url"] = df["live_url"].str.replace(rf"^{brand}_", "", regex=True)

# /replays/ 뒤의 숫자만 추출해서 새로운 컬럼 생성
df["url_code"] = df["live_url"].str.extract(r'/replays/(\d+)')
codes_df["url_code"] = codes_df["live_url"].str.extract(r'/replays/(\d+)')

# codes_df 에서 필요한 컬럼만 선택
codes_df = codes_df[["url_code", "live_code"]]

# df 기준 병합
merged_df = pd.merge(df, codes_df, on="url_code", how="left")

# 원하는 컬럼 순서 지정
# desired_order = ["live_code", "time", "nickname", "comment", "total_duration(sec)","live_url"]
desired_order = ["live_code", "date", "start_time", "end_time", "duration_min","viewer_count", "promotion_flag", "promotion_text"]
merged_df = merged_df[desired_order]

# 병합 후 merged_df 행 수 확인
print("Number of rows after merge : ", len(merged_df))

# 결과 저장
merged_df.to_csv(rf"D:\School\5-2\데이터\shoppinglive_data\live_info_{brand}.csv", index=False, encoding="utf-8-sig")

print(merged_df.head(10))
