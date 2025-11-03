# ----------------------------------------------------------------------
# 0. (최초 1회만 실행) Colab에 한글 폰트 설치
#
# ⚠️⚠️⚠️ 중요: 아래 3줄을 실행한 뒤, 상단 메뉴에서 [런타임] > [런타임 다시 시작]을 꼭 눌러주세요.
# ⚠️⚠️⚠️ 이 과정을 거치지 않으면 폰트가 절대 적용되지 않습니다!
# ----------------------------------------------------------------------
# !sudo apt-get install -y fonts-nanum
# !sudo fc-cache -fv
# !rm ~/.cache/matplotlib -rf

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ----------------------------------------------------------------------
# 1. 그래프 환경 설정 (한글 폰트 및 스타일 지정)
# ----------------------------------------------------------------------
# 런타임 다시 시작 후에 이 부분을 실행하면 한글 폰트가 적용됩니다.
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False # 마이너스 부호 깨짐 방지
sns.set_theme(style="whitegrid", font="NanumGothic")

# ----------------------------------------------------------------------
# 2. 데이터 불러오기 및 통합
#
# 각 분류에 해당하는 파일들을 읽어 하나의 데이터프레임으로 합칩니다.
# ----------------------------------------------------------------------

# --- 2-1. 전체 브랜드별 데이터 불러오기 ---
try:
    total_df = pd.read_csv('search_volume_total.csv')
    total_df['date'] = pd.to_datetime(total_df['date'])
    print("-> '전체' 데이터 불러오기 성공!")
except FileNotFoundError:
    total_df = None
    print("-> !!! 'search_volume_total.csv' 파일을 찾을 수 없습니다.")


# --- 2-2. 성별 데이터 불러오기 및 통합 ---
gender_files = {
    '남성': 'search_volume_male.csv',
    '여성': 'search_volume_female.csv'
}
gender_df_list = []
for gender, filename in gender_files.items():
    try:
        df = pd.read_csv(filename)
        df['gender'] = gender # '성별' 컬럼 추가
        df['date'] = pd.to_datetime(df['date'])
        gender_df_list.append(df)
        print(f"-> '{filename}' (성별) 데이터 불러오기 성공!")
    except FileNotFoundError:
        print(f"-> !!! '{filename}' 파일을 찾을 수 없습니다.")

if gender_df_list:
    gender_df = pd.concat(gender_df_list, ignore_index=True)
else:
    gender_df = None

# --- 2-3. 연령별 데이터 불러오기 및 통합 ---
age_files = {
    '0-18': 'search_volume_under_18.csv',
    '19-39': 'search_volume_19_39.csv',
    '40-59': 'search_volume_40_59.csv',
    '60-': 'search_volume_over_60.csv'
}
age_df_list = []
for age_group, filename in age_files.items():
    try:
        df = pd.read_csv(filename)
        df['age'] = age_group # '연령' 컬럼 추가
        df['date'] = pd.to_datetime(df['date'])
        age_df_list.append(df)
        print(f"-> '{filename}' (연령) 데이터 불러오기 성공!")
    except FileNotFoundError:
        print(f"-> !!! '{filename}' 파일을 찾을 수 없습니다.")

if age_df_list:
    age_df = pd.concat(age_df_list, ignore_index=True)
else:
    age_df = None

# ----------------------------------------------------------------------
# 3. 시각화 (다양한 스타일의 그래프 생성)
# ----------------------------------------------------------------------

print("\n[그래프 생성 시작]...")

# --- 스타일 1: 꺾은선 그래프 (시간에 따른 상세 추이 분석) ---
print("\n-> 스타일 1: 꺾은선 그래프 생성 중...")
if total_df is not None:
    plt.figure(figsize=(16, 8))
    sns.lineplot(data=total_df, x='date', y='search_volume', hue='brand')
    plt.title('전체 브랜드별 상대적 검색량 추이', fontsize=20, pad=15)
    plt.xlabel('날짜', fontsize=12); plt.ylabel('상대적 검색량', fontsize=12)
    plt.legend(title='브랜드'); plt.tight_layout()
    plt.savefig('trend_line_chart_total.png', dpi=300); plt.show()

if gender_df is not None:
    # 성별 데이터는 브랜드별로 그래프를 나누어 생성 (가독성 향상)
    g = sns.relplot(data=gender_df, x='date', y='search_volume', hue='gender', col='brand', kind='line', height=5, aspect=1.5)
    g.fig.suptitle('브랜드 및 성별 검색량 추이', y=1.03, fontsize=20)
    g.set_axis_labels("날짜", "상대적 검색량").set_titles("브랜드: {col_name}")
    plt.tight_layout(); plt.savefig('trend_line_chart_gender.png', dpi=300); plt.show()


# --- 스타일 2: 히트맵 (계절성 및 연간 트렌드 분석) ---
print("\n-> 스타일 2: 히트맵 생성 중...")
if total_df is not None:
    total_df['year'] = total_df['date'].dt.year
    total_df['month'] = total_df['date'].dt.month
    brands = total_df['brand'].unique()

    for brand_name in brands:
        plt.figure(figsize=(12, 8))
        brand_data = total_df[total_df['brand'] == brand_name]
        pivot_data = brand_data.pivot_table(index='year', columns='month', values='search_volume', aggfunc='mean')
        sns.heatmap(pivot_data, cmap='viridis', annot=True, fmt=".1f", linewidths=.5)
        plt.title(f'[{brand_name}] 월별/연도별 평균 검색량 (전체)', fontsize=18, pad=20)
        plt.xlabel('월', fontsize=12); plt.ylabel('연도', fontsize=12)
        plt.tight_layout(); plt.savefig(f'heatmap_total_{brand_name}.png', dpi=300); plt.show()


# --- ✨ 스타일 3: 100% 누적 영역형 그래프 (점유율 변화 분석) ---
print("\n-> 스타일 3: 100% 누적 영역형 그래프 생성 중...")

def plot_100_percent_stacked_area(df, group_col, filename_prefix):
    pivot_df = df.pivot_table(index='date', columns='brand', values='search_volume', aggfunc='sum').fillna(0)
    # 각 날짜의 합계가 0인 경우를 대비하여 0으로 나누는 것을 방지
    daily_total = pivot_df.sum(axis=1)
    percentage_df = pivot_df.div(daily_total, axis=0).fillna(0) * 100

    plt.figure(figsize=(16, 8))
    plt.stackplot(percentage_df.index, percentage_df.T, labels=percentage_df.columns)
    plt.title(f'브랜드별 검색량 점유율 변화 ({group_col})', fontsize=20, pad=15)
    plt.xlabel('날짜', fontsize=12)
    plt.ylabel('검색량 점유율 (%)', fontsize=12)
    plt.ylim(0, 100) # Y축을 0-100%로 고정
    plt.legend(title='브랜드', loc='upper left')
    plt.tight_layout()
    plt.savefig(f'{filename_prefix}.png', dpi=300)
    plt.show()

if total_df is not None:
    plot_100_percent_stacked_area(total_df, '전체', 'stacked_area_100p_total')

if gender_df is not None:
    for gender_name in gender_df['gender'].unique():
        gender_subset = gender_df[gender_df['gender'] == gender_name]
        plot_100_percent_stacked_area(gender_subset, gender_name, f'stacked_area_100p_{gender_name}')


# --- 스타일 4: 연령대별 브랜드 분석 (하나의 그래프에서 비교) ---
print("\n-> 스타일 4: 연령대별 브랜드 통합 분석 그래프 생성 중...")
if age_df is not None:
    # 연령대 순서 정렬을 위해 Categorical 타입으로 설정
    age_order = ['0-18', '19-39', '40-59', '60-']
    age_df['age'] = pd.Categorical(age_df['age'], categories=age_order, ordered=True)

    # 브랜드와 연령대별 평균 검색량 계산
    avg_search_by_age_brand = age_df.groupby(['age', 'brand'])['search_volume'].mean().reset_index()

    plt.figure(figsize=(16, 9))

    # 그룹 막대 그래프 생성
    ax = sns.barplot(
        data=avg_search_by_age_brand,
        x='age', # X축을 연령대로 변경
        y='search_volume',
        hue='brand', # 비교 대상을 브랜드로 변경
        palette='Set2'
    )

    # 각 막대의 폭을 조절하는 로직
    for container in ax.containers:
        # 각 막대의 폭을 90%로 설정 (기본값은 100%)
        plt.setp(container, width=0.2)

    # 각 막대 위에 값 표시
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f', label_type='edge', padding=3, fontsize=9)

    # Y축 상단 여백 추가
    if not avg_search_by_age_brand['search_volume'].empty:
        ax.set_ylim(top=avg_search_by_age_brand['search_volume'].max() * 1.15)

    plt.title('연령대별 브랜드 평균 검색량 비교', fontsize=20, pad=15)
    plt.xlabel('연령대', fontsize=12)
    plt.ylabel('평균 상대적 검색량', fontsize=12)
    plt.legend(title='브랜드')
    plt.tight_layout()
    plt.savefig('age_analysis_grouped_bar_by_age.png', dpi=300)
    plt.show()

print("\n[모든 그래프 생성 완료]")

