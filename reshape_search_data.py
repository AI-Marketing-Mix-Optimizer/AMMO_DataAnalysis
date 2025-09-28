import pandas as pd

# 원본 CSV 읽기
df = pd.read_csv(r"D:\School\5-2\데이터\네이버검색량.csv")  # D:\School\5-2\데이터\네이버검색량_유산균추가.csv

# 결과 저장용 리스트
dfs = []

# 2개 컬럼씩 묶어서 처리 (날짜, 브랜드)
for i in range(0, df.shape[1], 2):
    date_col = df.columns[i]
    brand_col = df.columns[i + 1]
    brand_name = brand_col  # 브랜드 이름은 컬럼명 사용

    tmp = df[[date_col, brand_col]].copy()
    tmp.columns = ["date", "search_volume"]
    tmp["brand"] = brand_name
    dfs.append(tmp)

# 세로로 합치기
df_long = pd.concat(dfs, ignore_index=True)

# 날짜 datetime으로 변환
df_long["date"] = pd.to_datetime(df_long["date"])

# 컬럼 순서 재정렬
df_long = df_long[["brand", "search_volume", "date"]]

# 저장
df_long.to_csv(r"D:\School\5-2\데이터\네이버검색량_long.csv", index=False, encoding="utf-8-sig")

print(df_long.head)
