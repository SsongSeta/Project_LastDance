import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 0. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="LoL 오토필 생존 가이드", page_icon="🎮", layout="wide")

# ==========================================
# 1. V3 데이터 로드 및 캐싱 (절대 경로 적용)
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data():
    # 새로 저장한 V3 버전의 파일명으로 변경
    match_path = os.path.join(current_dir, 'match_data_v3_light.parquet')
    champ_path = os.path.join(current_dir, 'champ_data_v3.parquet')
    user_path = os.path.join(current_dir, 'user_profile_v3_light.parquet')
    
    df_match = pd.read_parquet(match_path) 
    df_champ = pd.read_parquet(champ_path)
    user_profile_df = pd.read_parquet(user_path)
    
    return df_match, df_champ, user_profile_df

try:
    df_match, df_champ, user_profile_df = load_data()
except FileNotFoundError as e:
    st.error(f"데이터 파일을 찾을 수 없습니다. 경로와 파일명을 확인해주세요: {e}")
    st.stop()

# =============================
# 0306 수정 함수 (일반/랭크 가중치 분리 반영)
# =============================
def recommend_autofill_v3(target_puuid, target_position, df_match, df_champ, user_profile_df, 
                          banned_champs=[], team_needs='balanced', is_ranked=True, top_n=5):
    """
    일반/랭크 게임에 따라 스코어링 가중치(숙련도 vs 난이도/스타일)가 동적으로 변하는 추천 시스템
    """
    
    # ---------------------------------------------------------
    # 1. 타겟 유저 프로필 및 숙련도 추출
    # ---------------------------------------------------------
    user_data = user_profile_df[user_profile_df['puuid'] == target_puuid]
    if user_data.empty:
        return "⚠️ 유저 프로필 데이터를 찾을 수 없습니다. (20게임 미만 유저)"
    
    user_data = user_data.iloc[0]
    primary_cluster = user_data['primary_cluster_id']
    secondary_cluster = user_data['secondary_cluster_id']
    user_ad_pref = user_data['avg_preferred_attack']
    user_ap_pref = user_data['avg_preferred_magic']
    user_range_pref = user_data['avg_preferred_range']
    
    played_champs_keys = df_match[df_match['puuid'] == target_puuid]['champ_match_key'].unique().tolist()
    
    # ---------------------------------------------------------
    # 2. 메타 풀(Meta Pool) & 밴(Ban) 필터링
    # ---------------------------------------------------------
    position_meta = df_match[df_match['team_position'] == target_position]['champ_match_key'].value_counts()
    banned_keys = df_champ[df_champ['champion_name'].isin(banned_champs)]['champ_match_key'].tolist()
    
    valid_candidate_keys = [c for c in position_meta.head(30).index if c not in banned_keys]
    candidates_df = df_champ[df_champ['champ_match_key'].isin(valid_candidate_keys)].copy()
    
    # ---------------------------------------------------------
    # 3. 스코어링 엔진 (동적 가중치 적용)
    # ---------------------------------------------------------
    candidates_df['score_prof'] = 0.0
    candidates_df['score_team'] = 0.0
    candidates_df['score_style'] = 0.0
    candidates_df['score_diff'] = 0.0
    candidates_df['total_score'] = 0.0
    candidates_df['recommend_reason'] = ""
    candidates_df['is_played'] = candidates_df['champ_match_key'].isin(played_champs_keys)
    
    is_user_ranged_pref = user_range_pref > 300 
    
    for idx, row in candidates_df.iterrows():
        s_prof, s_team, s_style, s_diff, s_stat = 0, 0, 0, 0, 0
        reason = []
        
        # A. 숙련도(Proficiency) 보정
        if row['is_played']:
            # [수정] 랭크면 30점, 일반게임이면 10점으로 축소
            s_prof += 30 if is_ranked else 10
            reason.append("⭐ 숙련도 있음")
        else:
            if is_ranked:
                s_prof -= 20
                reason.append("⚠️ 연습 필요")
                
        # B. 팀 조합(Team Needs) 보정
        if team_needs == 'AP_needed' and row['info_magic'] >= 6:
            s_team += 20
            reason.append("아군 AP 보완")
        elif team_needs == 'AD_needed' and row['info_attack'] >= 6:
            s_team += 20
            reason.append("아군 AD 보완")
        else:
            ad_diff = abs(row['info_attack'] - user_ad_pref)
            ap_diff = abs(row['info_magic'] - user_ap_pref)
            s_stat += max(0, 10 - (ad_diff + ap_diff))
            
        # C. 전투 사거리 성향 보정
        is_champ_ranged = row['attackrange'] > 300
        if is_user_ranged_pref == is_champ_ranged:
            s_stat += 10
            range_type = "원거리" if is_champ_ranged else "근접 전투"
            reason.append(f"선호하는 {range_type} 포지션")
            
        # D. 클러스터(스타일) 보정
        if row['cluster_id'] == primary_cluster:
            # [수정] 랭크면 20점, 일반게임이면 40점으로 대폭 상향
            s_style += 20 if is_ranked else 40
            reason.append("1순위 플레이 스타일 일치")
        elif row['cluster_id'] == secondary_cluster:
            # [수정] 랭크면 15점, 일반게임이면 30점으로 대폭 상향
            s_style += 15 if is_ranked else 30
            reason.append("2순위 플레이 스타일 일치")
            
        # E. 난이도 보정 (국밥 필터)
        if row['info_difficulty'] <= 4:
            # [수정] 랭크면 20점, 일반게임이면 40점으로 대폭 상향
            s_diff += 20 if is_ranked else 40
            reason.append("쉬운 난이도")
            
        total = s_prof + s_team + s_style + s_diff + s_stat
        
        candidates_df.at[idx, 'score_prof'] = s_prof
        candidates_df.at[idx, 'score_team'] = s_team
        candidates_df.at[idx, 'score_style'] = s_style
        candidates_df.at[idx, 'score_diff'] = s_diff
        candidates_df.at[idx, 'total_score'] = total
        candidates_df.at[idx, 'recommend_reason'] = " / ".join(reason) if reason else "무난한 픽"
        
    # ---------------------------------------------------------
    # 4. 정렬(Tie-breaking) 및 탐험(Exploration) 로직
    # ---------------------------------------------------------
    if is_ranked:
        # [랭크 게임] 동점 시: 총점 > 숙련도 > 난이도 > 스타일 > 팀 조합 > 알파벳순
        sorted_df = candidates_df.sort_values(
            by=['total_score', 'score_prof', 'score_diff', 'score_style', 'score_team', 'champion_name'],
            ascending=[False, False, False, False, False, True]
        )
        final_recommendation = sorted_df.head(top_n)
    else:
        # [일반 게임] 동점 시: 총점 > 스타일 > 난이도 > 알파벳순
        sorted_df = candidates_df.sort_values(
            by=['total_score', 'score_style', 'score_diff', 'champion_name'],
            ascending=[False, False, False, True]
        )
        
        # 탐험 챔피언 풀 (안 해봤고, 난이도 5 이하)
        exploration_pool = sorted_df[
            (~sorted_df['is_played']) & 
            (sorted_df['info_difficulty'] <= 5)
        ]
        
        # 탐험 챔피언 최대 2개 추출
        num_wildcards = min(2, len(exploration_pool))
        wildcards = exploration_pool.sample(num_wildcards).copy()
        wildcards['recommend_reason'] = "💡 새로운 도전 / " + wildcards['recommend_reason']
        
        # [수정됨] 나머지 자리는 탐험 픽으로 뽑힌 챔피언을 제외하고, 남은 후보 중 점수 높은 순으로 무조건 채움
        num_regulars = top_n - num_wildcards
        remaining_pool = sorted_df[~sorted_df['champ_match_key'].isin(wildcards['champ_match_key'])]
        regulars = remaining_pool.head(num_regulars).copy()
        
        # 합친 후, 지정된 '일반 게임 룰' 기준으로 최종 정렬
        final_recommendation = pd.concat([regulars, wildcards]).sort_values(
            by=['total_score', 'score_style', 'score_diff', 'champion_name'],
            ascending=[False, False, False, True]
        )
            
    result_cols = ['champion_name', 'total_score', 'recommend_reason']
    return final_recommendation[result_cols]

# ==========================================
# 2. 사이드바 (사용자 입력)
# ==========================================
st.sidebar.header("시뮬레이션 설정")

user_list = user_profile_df['puuid'].unique().tolist()
selected_user = st.sidebar.selectbox("대상 유저 선택 (PUUID)", user_list)

selected_pos = st.sidebar.selectbox("배정받은 포지션", ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'])

all_champs = sorted(df_champ['champion_name'].unique())
# [수정됨] max_selections=10 을 통해 최대 밴 개수를 랭크 게임과 동일하게 제한
bans = st.sidebar.multiselect("🚫 밴 챔피언 (최대 10개)", all_champs, default=[], max_selections=10)

needs = st.sidebar.radio("아군 조합 상황", 
                         options=['balanced', 'AP_needed', 'AD_needed'],
                         format_func=lambda x: '무난함 (밸런스)' if x == 'balanced' else ('AP 부족' if x == 'AP_needed' else 'AD 부족'))

is_ranked = st.sidebar.toggle("랭크 게임인가요?", value=True)

st.sidebar.markdown("---")
if st.sidebar.button("추천 챔피언 분석하기"):
    st.session_state['run'] = True

# ==========================================
# 3. 메인 화면 - 클러스터링 시각화 (근거 자료)
# ==========================================
st.title("오토필 챔피언 추천 시스템")
st.markdown("챔피언 성향 분석과 유저의 과거 전적을 결합하여 최적의 픽을 제안합니다.")

st.subheader("챔피언 성향 클러스터링 매핑 (PCA)")

# Plotly를 활용한 반응형 스캐터 플롯 생성
df_champ['cluster_id'] = df_champ['cluster_id'].astype(str) # 색상을 카테고리별로 나누기 위해 문자형 변환

fig = px.scatter(
    df_champ, 
    x='pca_x', 
    y='pca_y', 
    color='cluster_id', 
    hover_name='champion_name', # 마우스를 올리면 챔피언 이름이 보임! (스트림릿의 핵심 장점)
    hover_data=['info_attack', 'info_magic', 'info_difficulty', 'attackrange'],
    title="챔피언별 스탯 기반 전투 스타일 맵",
    color_discrete_sequence=px.colors.qualitative.Set1
)
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. 메인 화면 - 추천 시스템 시뮬레이션 결과
# ==========================================
if st.session_state.get('run'):
    st.markdown("---")
    st.subheader(f"'{selected_pos}' 포지션 맞춤 추천 챔피언 Top 5")
    
    with st.spinner('유저 성향과 메타 분석중...'):
        result_df = recommend_autofill_v3(selected_user, selected_pos, df_match, df_champ, user_profile_df, bans, needs, is_ranked)
        
        if isinstance(result_df, str):
            st.error(result_df) # 에러 메시지 출력
        else:
            cols = st.columns(5)
            for rank, (original_idx, row) in enumerate(result_df.iterrows()):
                current_rank = rank + 1 
                
                with cols[rank]:
                    st.info(f"**{current_rank}위: {row['champion_name']}**")
                    st.metric(label="추천 점수", value=f"{int(row['total_score'])}점")
                    st.caption(f"{row['recommend_reason']}")
        
        st.success("분석 완료!")