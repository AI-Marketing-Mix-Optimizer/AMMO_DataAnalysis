import pandas as pd

brand = 'D'  # 'B', 'D', 'L' *********************************************************************************************************************************

# CSV 읽기
searches_df = pd.read_csv(rf"D:\School\5-2\데이터\search_volume_data\search_volume_total.csv")
prod_code_df = pd.read_csv(rf"D:\School\5-2\데이터\shoppinglive_data\prod_code_{brand}.csv")
reviews_df = pd.read_csv(rf"D:\School\5-2\데이터\shoppinglive_data\product_review_{brand}.csv")
live_info_df = pd.read_csv(rf"D:\School\5-2\데이터\shoppinglive_data\live_info_{brand}.csv")

# 필요한 컬럼 선택
searches_df = searches_df[["brand", "date", "search_volume_abs"]]
prod_code_df = prod_code_df[["prod_code", "prod_name"]]
reviews_df = reviews_df[["상품코드", "날짜", "별점", "판매여부"]]
live_info_df = live_info_df[["live_code", "date", "duration_min", "viewer_count", "promotion_flag"]]

# 컬럼명 변경
reviews_df = reviews_df.rename(columns={"상품코드": "prod_code", "날짜": "date", "별점": "rating", "판매여부": "is_available"})

# 필요한 행 필터링
if brand == 'B':
    searches_df = searches_df[searches_df["brand"].str.contains("비에날씬", na=False)]  # 비에날씬 검색량만
    prod_code_df = prod_code_df[prod_code_df["prod_name"].str.contains("비에날씬", na=False)]  # 비에날씬 상품만
    reviews_df = reviews_df[reviews_df["prod_code"].isin(prod_code_df["prod_code"])]  # prod_code_df에 있는 상품코드만
elif brand == 'D':
    searches_df = searches_df[searches_df["brand"].str.contains("덴마크 유산균", na=False)]
    prod_code_df = prod_code_df[prod_code_df["prod_name"].str.contains("덴마크 유산균", na=False)]
    reviews_df = reviews_df[reviews_df["prod_code"].isin(prod_code_df["prod_code"])]
elif brand == 'L':
    searches_df = searches_df[searches_df["brand"].str.contains("락토핏", na=False)]
    prod_code_df = prod_code_df[prod_code_df["prod_name"].str.contains("락토핏", na=False)]
    reviews_df = reviews_df[reviews_df["prod_code"].isin(prod_code_df["prod_code"])]

# 날짜별 rating 평균 + 일별 리뷰 수 집계
reviews_df = reviews_df.groupby("date").agg(
    avg_rating=("rating", "mean"),        # 날짜별 평균 평점
    daily_review_count=("prod_code", "count")  # 날짜별 리뷰 수
).reset_index()

# 세 데이터프레임 합치기
merged_df = searches_df.merge(reviews_df, on="date", how="outer") \
                       .merge(live_info_df, on="date", how="outer")

# 날짜 오름차순 정렬
merged_df = merged_df.sort_values("date").reset_index(drop=True)

# 저장
merged_df.to_csv(rf"D:\School\5-2\데이터\proxy_sales_input_{brand}.csv", index=False, encoding="utf-8-sig")

print(merged_df.head())