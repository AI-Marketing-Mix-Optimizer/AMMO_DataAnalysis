import pandas as pd

brand = 'L'  # 'B', 'D', 'L' *********************************************************************************************************************************

# CSV 불러오기
comments_df = pd.read_csv(rf"D:\School\5-2\데이터\shoppinglive_data\실시간 댓글\{brand}_Live_Comment.csv")
codes_df = pd.read_csv(rf"D:\School\5-2\데이터\shoppinglive_data\live_code_{brand}.csv")

# 기존 comments_df 행 수 확인
print("Number of rows before merge : ", len(comments_df))

# comments_df 컬럼명 변경
comments_df = comments_df.rename(columns={"video_url": "live_url"})

# live_url 앞의 불필요한 부분 제거
comments_df["live_url"] = comments_df["live_url"].str.replace(rf"^{brand}_", "", regex=True)

# codes_df 에서 필요한 컬럼만 선택
codes_df = codes_df[["live_url", "live_code"]]

# comments_df 기준 병합
merged_df = pd.merge(comments_df, codes_df, on="live_url", how="left")

# 원하는 컬럼 순서 지정
desired_order = ["live_code", "time", "nickname", "comment", "live_url"]
merged_df = merged_df[desired_order]

# 병합 후 merged_df 행 수 확인
print("Number of rows after merge : ", len(merged_df))

# 결과 저장
merged_df.to_csv(rf"D:\School\5-2\데이터\shoppinglive_data\live_comment_{brand}.csv", index=False, encoding="utf-8-sig")

print(merged_df.head(10))
