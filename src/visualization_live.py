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
# ----------------------------------------------------------------------
file_paths = {
    'B': 'B_liveinfo.csv',
    'D': 'D_liveinfo.csv',
    'L': 'L_liveinfo.csv'
}

all_data = []
print("데이터 파일을 불러옵니다...")
for category, path in file_paths.items():
    try:
        df = pd.read_csv(path)
        df['category'] = category
        all_data.append(df)
        print(f"-> '{path}' 파일 불러오기 성공!")
    except FileNotFoundError:
        print(f"-> !!! 에러: '{path}' 파일을 찾을 수 없습니다. 파일이 업로드되었는지 확인해주세요.")

combined_df = pd.concat(all_data, ignore_index=True)

# ----------------------------------------------------------------------
# 3. 데이터 전처리
# ----------------------------------------------------------------------
# 'date' 컬럼을 날짜 형식으로 변환
combined_df['date'] = pd.to_datetime(combined_df['date'])

# 'promotion_flag' 값을 더 이해하기 쉬운 텍스트로 변경합니다.
combined_df['promotion_status'] = combined_df['promotion_flag'].map({1: '프로모션 진행', 0: '프로모션 없음'})

# 'date'에서 요일 정보 추출 (안정적인 방식으로 변경)
# 영문 요일 이름을 먼저 추출한 뒤, 한글로 직접 변환합니다.
weekday_map = {
    'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
    'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
}
combined_df['weekday'] = combined_df['date'].dt.day_name().map(weekday_map)


print("\n데이터 전처리 완료. 총", len(combined_df), "개의 방송 데이터를 분석합니다.")

# ----------------------------------------------------------------------
# 4. 시각화 (2개의 그래프 생성)
# ----------------------------------------------------------------------

# --- 그래프 1: 프로모션 진행 여부에 따른 시청자 수 비교 ---
plt.figure(figsize=(12, 8))

# Boxplot을 사용하여 프로모션 유무에 따른 시청자 수 분포를 비교합니다.
ax1 = sns.boxplot(
    data=combined_df,
    x='promotion_status',
    y='viewer_count',
    hue='category', # 카테고리별로 색상을 다르게 표시
    palette={"B": "#87CEEB", "D": "#FFB6C1", "L": "#98FB98"} # 색상 지정
)

# Y축 단위를 더 읽기 쉽게 '만' 단위로 변경 (예: 100000 -> 10만)
ax1.yaxis.set_major_formatter(lambda x, pos: f'{int(x/10000)}만')

plt.title('프로모션 진행 여부에 따른 시청자 수 비교', fontsize=20, pad=15)
plt.xlabel('프로모션 진행 여부', fontsize=12)
plt.ylabel('시청자 수', fontsize=12)
plt.legend(title='카테고리')
plt.tight_layout()
plt.savefig('promotion_vs_viewers.png', dpi=300)
plt.show()


# --- 그래프 2: 요일 및 카테고리별 평균 시청자 수 ---
# 요일과 카테고리별로 평균 시청자 수 계산
weekday_avg_viewers = combined_df.groupby(['weekday', 'category'])['viewer_count'].mean().reset_index()

# 요일을 월요일부터 일요일 순으로 정렬
weekday_order = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
weekday_avg_viewers['weekday'] = pd.Categorical(weekday_avg_viewers['weekday'], categories=weekday_order, ordered=True)
weekday_avg_viewers = weekday_avg_viewers.sort_values('weekday')


plt.figure(figsize=(16, 9)) # 그룹 막대 그래프이므로 가로 폭을 더 넓게 조정

# Barplot을 사용하여 요일별, 카테고리별 평균 시청자 수를 보여줍니다.
ax2 = sns.barplot(
    data=weekday_avg_viewers,
    x='weekday',
    y='viewer_count',
    hue='category',
    palette={"B": "#87CEEB", "D": "#FFB6C1", "L": "#98FB98"} # 색상 지정
)

# Y축 단위를 더 읽기 쉽게 '만' 단위로 변경
ax2.yaxis.set_major_formatter(lambda x, pos: f'{int(x/10000)}만')

# 각 막대 위에 평균값 표시 (단위를 '만'으로 변환하여 표시)
for container in ax2.containers:
    ax2.bar_label(container, fmt=lambda x: f'{x/10000:.1f}만', label_type='edge', padding=3, fontsize=9)

# 라벨이 잘리지 않도록 Y축 상단에 여백 추가
ax2.set_ylim(top=ax2.get_ylim()[1] * 1.1)

plt.title('요일 및 카테고리별 평균 시청자 수', fontsize=22, pad=20)
plt.xlabel('요일', fontsize=14)
plt.ylabel('평균 시청자 수', fontsize=14)
plt.legend(title='카테고리')
plt.tight_layout()
plt.savefig('weekday_category_vs_viewers.png', dpi=300)
plt.show()

