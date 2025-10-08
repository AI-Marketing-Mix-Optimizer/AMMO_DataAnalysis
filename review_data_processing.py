import pandas as pd
import os

brand = 'L'  # 'B', 'D', 'L' *********************************************************************************************************************************

# 폴더 경로
folder_path = rf"D:\School\5-2\데이터\shoppinglive_data\reviews_data\reviews_{brand}P"

# 폴더 안 모든 CSV 파일 선택
csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

# 데이터프레임 리스트
df_list = []

# 각 CSV 파일 읽으면서 처리
for f in csv_files:
    df = pd.read_csv(os.path.join(folder_path, f))

    # 성별 변환: 여자 → 0, 남자 → 1
    if "구매자 성별" in df.columns:
        df["구매자 성별"] = df["구매자 성별"].map({"여성": 0, "남성": 1})
        df["구매자 성별"] = df["구매자 성별"].fillna(2).astype("int8")  # 결측치 2

        # 판매여부 변환: N → 0, Y → 1
    if "판매여부" in df.columns:
        df["판매여부"] = df["판매여부"].map({"N": 0, "Y": 1}).astype("int8")

    # 상품명, URL 컬럼 제거
    df.drop(columns=[c for c in ["상품명", "URL"] if c in df.columns], inplace=True)

    df_list.append(df)

# 모든 CSV 합치기
merged_df = pd.concat(df_list, ignore_index=True)

# CSV 저장
merged_df.to_csv(rf"D:\School\5-2\데이터\shoppinglive_data\product_review_{brand}.csv", index=False, encoding="utf-8-sig")

print("모든 CSV 합치기 완료")