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

# ✨ 디자인 수정 ✨ (그래프 전체 스타일)
# style: "whitegrid", "darkgrid", "white", "ticks" 등으로 변경 가능합니다.
# font: 위에서 설정한 'NanumGothic'을 그대로 사용합니다.
sns.set_theme(style="whitegrid", font="NanumGothic")

# ----------------------------------------------------------------------
# 2. 데이터 불러오기
# ----------------------------------------------------------------------
# Colab 왼편의 파일 탐색기에 CSV 파일 3개를 업로드했는지 확인해주세요.
file_paths = {
    'B': 'B_Live_Comment_updated.csv',
    'D': 'D_Live_Comment.csv',
    'L': 'L_Live_Comment_updated.csv'
}

data_frames = {}
print("데이터 파일을 불러옵니다...")
for category, path in file_paths.items():
    try:
        data_frames[category] = pd.read_csv(path)
        print(f"-> '{path}' 파일 불러오기 성공!")
    except FileNotFoundError:
        print(f"-> !!! 에러: '{path}' 파일을 찾을 수 없습니다. 파일이 업로드되었는지 확인해주세요.")
        data_frames[category] = pd.DataFrame(columns=['broadcast_id', 'total_duration(sec)'])

# ----------------------------------------------------------------------
# 3. 카테고리별 지표 계산
# ----------------------------------------------------------------------
summary_data = []
for cat in ['B', 'D', 'L']:
    df = data_frames[cat]
    num_videos = df['broadcast_id'].nunique()

    # ✅ 추가: 총 댓글 수 계산
    total_comments = len(df)

    if num_videos > 0:
        unique_videos = df.drop_duplicates(subset=['broadcast_id'])
        avg_duration = unique_videos['total_duration(sec)'].mean()
        avg_comment = total_comments / num_videos
    else:
        avg_duration = 0
        avg_comment = 0

    avg_duration = 0 if pd.isna(avg_duration) else avg_duration
    avg_comment = 0 if pd.isna(avg_comment) else avg_comment

    # ✅ 수정: summary_data에 총 댓글 수 추가
    summary_data.append([cat, num_videos, avg_duration, avg_comment, total_comments])

# ✅ 수정: DataFrame 컬럼에 '총 댓글 수' 추가
summary_df = pd.DataFrame(summary_data, columns=['카테고리', '총 영상 개수', '평균 영상 시간(초)', '평균 댓글 수', '총 댓글 수'])
print("\n[계산된 요약 데이터]")
print(summary_df)
print("-" * 30)

# ----------------------------------------------------------------------
# 4. 시각화 (그래프 4개를 각각 생성 및 저장)
# ----------------------------------------------------------------------
custom_palette = {"B": "#87CEEB", "D": "#FFB6C1", "L": "#98FB98"}

# --- 그래프 1: 총 영상 개수 ---
plt.figure(figsize=(10, 7))
# ✨ 디자인 수정 ✨ (막대 가로 폭)
# width 값을 조절하여 막대의 두께를 변경합니다. (기본값: 0.8)
ax1 = sns.barplot(x='카테고리', y='총 영상 개수', data=summary_df, palette=custom_palette, width=0.5)
ax1.set_title('브랜드별 총 영상 개수', fontsize=18, pad=15)
ax1.set_xlabel('')
ax1.set_ylabel('개수', fontsize=12)

# Y축 범위를 데이터 최대값보다 10% 높게 설정하여 라벨 공간 확보
ax1.set_ylim(0, summary_df['총 영상 개수'].max() * 1.1)

# 막대 위에 값 표시 (수동으로 위치 지정하여 더 안정적)
for p in ax1.patches:
    height = p.get_height()
    ax1.text(p.get_x() + p.get_width() / 2., height + 0.5, f'{height:.0f}개', ha='center', va='bottom', fontsize=12)

plt.savefig('total_videos_chart.png', dpi=300, bbox_inches='tight')
plt.show()


# --- 그래프 2: 평균 영상 시간 ---
plt.figure(figsize=(10, 7))
# ✨ 디자인 수정 ✨ (막대 가로 폭)
ax2 = sns.barplot(x='카테고리', y='평균 영상 시간(초)', data=summary_df, palette=custom_palette, width=0.5)
ax2.set_title('브랜드별 평균 영상 시간', fontsize=18, pad=15)
ax2.set_xlabel('')
ax2.set_ylabel('평균 시간 (초)', fontsize=12)
ax2.set_ylim(0, summary_df['평균 영상 시간(초)'].max() * 1.1)

for p in ax2.patches:
    height = p.get_height()
    ax2.text(p.get_x() + p.get_width() / 2., height + 0.5, f'{height:.1f}초', ha='center', va='bottom', fontsize=12)

plt.savefig('avg_duration_chart.png', dpi=300, bbox_inches='tight')
plt.show()


# --- 그래프 3: 평균 댓글 수 ---
plt.figure(figsize=(10, 7))
# ✨ 디자인 수정 ✨ (막대 가로 폭)
ax3 = sns.barplot(x='카테고리', y='평균 댓글 수', data=summary_df, palette=custom_palette, width=0.5)
ax3.set_title('브랜드별 영상 하나의 평균 댓글 수', fontsize=18, pad=15)
ax3.set_xlabel('')
ax3.set_ylabel('평균 댓글 수', fontsize=12)
ax3.set_ylim(0, summary_df['평균 댓글 수'].max() * 1.1)

for p in ax3.patches:
    height = p.get_height()
    ax3.text(p.get_x() + p.get_width() / 2., height + 0.5, f'{height:.1f}개', ha='center', va='bottom', fontsize=12)

plt.savefig('avg_comments_chart.png', dpi=300, bbox_inches='tight')
plt.show()

# --- ✅ 추가된 그래프 4: 총 댓글 수 ---
plt.figure(figsize=(10, 7))
# ✨ 디자인 수정 ✨ (막대 가로 폭)
ax4 = sns.barplot(x='카테고리', y='총 댓글 수', data=summary_df, palette=custom_palette, width=0.5)
ax4.set_title('브랜드별 총 댓글 수', fontsize=18, pad=15)
ax4.set_xlabel('')
ax4.set_ylabel('총 댓글 수', fontsize=12)
ax4.set_ylim(0, summary_df['총 댓글 수'].max() * 1.1)

for p in ax4.patches:
    height = p.get_height()
    ax4.text(p.get_x() + p.get_width() / 2., height + 0.5, f'{height:.0f}개', ha='center', va='bottom', fontsize=12)

plt.savefig('total_comments_chart.png', dpi=300, bbox_inches='tight')
plt.show()

