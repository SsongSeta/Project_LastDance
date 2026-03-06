import streamlit as st
import pandas as pd
import plotly.express as px
import os
import random

# ==========================================
# 0. 페이지 기본 설정 및 유틸리티 함수
# ==========================================
st.set_page_config(page_title="LoL 오토필 생존 가이드", page_icon="🎮", layout="wide")

# 포지션 한글화 매핑 딕셔너리
POS_KOR_MAP = {
    'TOP': '탑',
    'JUNGLE': '정글',
    'MIDDLE': '미드',
    'BOTTOM': '원딜',
    'UTILITY': '서폿'
}
# 역매핑 (한글 -> 영문)
KOR_POS_MAP = {v: k for k, v in POS_KOR_MAP.items()}

@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    match_path = os.path.join(current_dir, 'match_data_v4_light.parquet')
    champ_path = os.path.join(current_dir, 'champ_data_v4.parquet')
    user_path = os.path.join(current_dir, 'user_profile_v4_light.parquet')
    
    return pd.read_parquet(match_path), pd.read_parquet(champ_path), pd.read_parquet(user_path)

try:
    df_match, df_champ, user_profile_df = load_data()
except FileNotFoundError as e:
    st.error(f"데이터 파일을 찾을 수 없습니다: {e}")
    st.stop()

# PUUID -> 랜덤닉네임 변환 함수
@st.cache_data
def generate_nicknames(puuid_list):
    random.seed(42) # 항상 동일한 닉네임이 부여되도록 시드 고정
    adjs = ["GEN", "T1", "KT", "NS", "DNS", "BRO", "HLE", "DK", "BFX", "DRX", "SSG"]
    nouns = ["Kiin", "Canyon", "Chovy", "Ruler", "Duro", "Doran", "Oner", "Faker", "Peyz", "Keria", "Zeus", "Kanavi", "Zeka", "Gumayusi", "Delight",
            "Cuzz", "Bdd", "Ghost", "Smash", "Lucid", "Diable", "Kingen", "DuDu", "Pyosik", "Clozer", "deokdam", "Peter"]
    
    nick_map = {}
    for i, p in enumerate(puuid_list):
        nick_map[p] = f"{random.choice(adjs)} {random.choice(nouns)} #{i+1}"
    return nick_map

puuid_to_nick = generate_nicknames(user_profile_df['puuid'].unique())

# ==========================================
# 1. 추천 로직 V4 (사거리 3단계 분류 적용)
# ==========================================
def recommend_autofill_v4(target_puuid, target_position, df_match, df_champ, user_profile_df, 
                          banned_champs=[], team_needs='balanced', is_ranked=True, top_n=5):
    
    user_data = user_profile_df[user_profile_df['puuid'] == target_puuid].iloc[0]
    primary_cluster = user_data['primary_cluster_id']
    secondary_cluster = user_data['secondary_cluster_id']
    user_ad_pref = user_data['avg_preferred_attack']
    user_ap_pref = user_data['avg_preferred_magic']
    user_range_pref = user_data['avg_preferred_range']
    
    # [요청 1] 사거리 선호도 3단계 분류
    if user_range_pref < 250:
        user_range_type = 'melee'   # 근거리 선호
    elif user_range_pref > 400:
        user_range_type = 'ranged'  # 원거리 선호
    else:
        user_range_type = 'neutral' # 중립 (올라운더)
        
    played_champs_keys = df_match[df_match['puuid'] == target_puuid]['champ_match_key'].unique().tolist()
    
    position_meta = df_match[df_match['team_position'] == target_position]['champ_match_key'].value_counts()
    banned_keys = df_champ[df_champ['champion_name'].isin(banned_champs)]['champ_match_key'].tolist()
    
    valid_candidate_keys = [c for c in position_meta.head(30).index if c not in banned_keys]
    candidates_df = df_champ[df_champ['champ_match_key'].isin(valid_candidate_keys)].copy()
    
    candidates_df['score_prof'] = 0.0
    candidates_df['score_team'] = 0.0
    candidates_df['score_style'] = 0.0
    candidates_df['score_diff'] = 0.0
    candidates_df['total_score'] = 0.0
    candidates_df['recommend_reason'] = ""
    candidates_df['is_played'] = candidates_df['champ_match_key'].isin(played_champs_keys)
    
    for idx, row in candidates_df.iterrows():
        s_prof, s_team, s_style, s_diff, s_stat = 0, 0, 0, 0, 0
        reason = []
        
        # A. 숙련도
        if row['is_played']:
            s_prof += 30 if is_ranked else 10
        else:
            if is_ranked: s_prof -= 20
                
        # B. 팀 조합
        if team_needs == 'AP_needed' and row['info_magic'] >= 6:
            s_team += 20
            reason.append("아군 AP 보완")
        elif team_needs == 'AD_needed' and row['info_attack'] >= 6:
            s_team += 20
            reason.append("아군 AD 보완")
        else:
            s_stat += max(0, 10 - (abs(row['info_attack'] - user_ad_pref) + abs(row['info_magic'] - user_ap_pref)))
            
        # C. [요청 1 반영] 사거리 성향 보정 (중립 추가)
        is_champ_ranged = row['attackrange'] > 300
        champ_range_str = "원거리" if is_champ_ranged else "근거리"
        
        if user_range_type == 'neutral':
            s_stat += 5 # 올라운더에게는 약한 기본 가산점
            reason.append("잡식성")
        elif (user_range_type == 'melee' and not is_champ_ranged) or (user_range_type == 'ranged' and is_champ_ranged):
            s_stat += 10
            reason.append(f"{champ_range_str} 챔피언")
            
        # D. 스타일
        if row['cluster_id'] == primary_cluster:
            s_style += 20 if is_ranked else 40
            reason.append(f"주력 스타일 일치 ({row['cluster_name']})")
        elif row['cluster_id'] == secondary_cluster:
            s_style += 15 if is_ranked else 30
            reason.append(f"서브 스타일 일치 ({row['cluster_name']})")
            
        # E. 난이도
        if row['info_difficulty'] <= 4:
            s_diff += 20 if is_ranked else 40
            reason.append("쉬운 조작 난이도")
            
        candidates_df.at[idx, 'score_prof'] = s_prof
        candidates_df.at[idx, 'score_team'] = s_team
        candidates_df.at[idx, 'score_style'] = s_style
        candidates_df.at[idx, 'score_diff'] = s_diff
        candidates_df.at[idx, 'total_score'] = s_prof + s_team + s_style + s_diff + s_stat
        candidates_df.at[idx, 'recommend_reason'] = " / ".join(reason) if reason else "무난한 픽"
        
    # 정렬 및 탐험 픽 할당 로직
    if is_ranked:
        sorted_df = candidates_df.sort_values(by=['total_score', 'score_prof', 'score_diff', 'score_style', 'score_team', 'champion_name'], ascending=[False, False, False, False, False, True])
        final_recommendation = sorted_df.head(top_n)
    else:
        sorted_df = candidates_df.sort_values(by=['total_score', 'score_style', 'score_diff', 'champion_name'], ascending=[False, False, False, True])
        exploration_pool = sorted_df[(~sorted_df['is_played']) & (sorted_df['info_difficulty'] <= 5)]
        
        num_wildcards = min(2, len(exploration_pool))
        wildcards = exploration_pool.head(num_wildcards).copy()
        wildcards['recommend_reason'] = "💡 새로운 도전 / " + wildcards['recommend_reason']
        
        num_regulars = top_n - num_wildcards
        remaining_pool = sorted_df[~sorted_df['champ_match_key'].isin(wildcards['champ_match_key'])]
        regulars = remaining_pool.head(num_regulars).copy()
        
        final_recommendation = pd.concat([regulars, wildcards]).sort_values(by=['total_score', 'score_style', 'score_diff', 'champion_name'], ascending=[False, False, False, True])
            
    # [요청 5] 특성 표시를 위해 전체 컬럼을 다 반환하도록 수정 (기존: result_cols 필터링 삭제)
    return final_recommendation

# ==========================================
# 2. 사이드바 (사용자 입력)
# ==========================================
st.sidebar.header("시뮬레이션 설정")

# [요청 2] 랜덤 닉네임으로 유저 선택
user_options = list(puuid_to_nick.values())
selected_nick = st.sidebar.selectbox("대상 유저 선택", user_options)
# 선택한 닉네임을 다시 실제 puuid로 역추적
selected_puuid = [k for k, v in puuid_to_nick.items() if v == selected_nick][0]

# [요청 4] 포지션 한글화
selected_pos_kor = st.sidebar.selectbox("배정받은 포지션", list(POS_KOR_MAP.values()))
selected_pos_eng = KOR_POS_MAP[selected_pos_kor]

# 밴 카드 (챔피언 이름도 ko_KR을 불러왔다면 한글로 표시됨)
all_champs = sorted(df_champ['champion_name'].unique())
bans = st.sidebar.multiselect("🚫 밴 챔피언 (최대 10개)", all_champs, default=[], max_selections=10)

needs = st.sidebar.radio("아군 조합 상황", options=['balanced', 'AP_needed', 'AD_needed'],
                         format_func=lambda x: '무난함' if x == 'balanced' else ('AP 부족' if x == 'AP_needed' else 'AD 부족'))

is_ranked = st.sidebar.toggle("랭크 게임인가요?", value=True)

st.sidebar.markdown("---")
if st.sidebar.button("추천 챔피언 분석하기"):
    st.session_state['run'] = True

# ==========================================
# 3. 메인 화면 - 탭 구성
# ==========================================
st.title("당신만을 위한 챔피언 추천 시스템")

# [요청 5] 탭 기능 분리
tab_recom, tab_cluster = st.tabs(["맞춤형 챔피언 추천", "챔피언 특징 기반 클러스터"])

# ----------------- 추천 탭 -----------------
with tab_recom:
    if st.session_state.get('run'):
        st.subheader(f"[{selected_nick}] 님을 위한 '{selected_pos_kor}' 포지션 Top 5")
        
        with st.spinner('유저 성향과 메타를 분석하고 있습니다...'):
            result_df = recommend_autofill_v4(selected_puuid, selected_pos_eng, df_match, df_champ, user_profile_df, bans, needs, is_ranked)
            
            if isinstance(result_df, str):
                st.error(result_df)
            else:
                cols = st.columns(5)
                for rank, (idx, row) in enumerate(result_df.iterrows()):
                    with cols[rank]:
                        # [요청 6] 챔피언 공식 이미지 삽입 (데이터에 champion_id가 있어야 함. 없으면 영문명 우회 필요)
                        try:
                            champ_img_id = row['champion_id']
                        except KeyError:
                            # 만약 champion_id를 안 만드셨다면 임시로 작동하게 하는 방어 코드
                            champ_img_id = row['champ_match_key'].capitalize()
                            
                        img_url = f"https://ddragon.leagueoflegends.com/cdn/16.2.1/img/champion/{champ_img_id}.png"
                        st.image(img_url, use_container_width=True)
                        
                        st.markdown(f"**{rank+1}위: {row['champion_name']}**")
                        st.write(f"**총점:** {int(row['total_score'])}점")
                        
                        # [요청 5] 챔피언 특성 배지 생성
                        dmg_type = "🔮 AP" if row['info_magic'] > row['info_attack'] else "🗡️ AD"
                        range_type = "🏹 원거리" if row['attackrange'] > 300 else "🛡️ 근거리"
                        style_match = "✅ 스타일 일치" if row['score_style'] > 0 else "➖ 스타일 무관"
                        
                        diff_val = row['info_difficulty']
                        if diff_val <= 4: diff_str = "⭐ 쉬움"
                        elif diff_val <= 7: diff_str = "⭐⭐ 보통"
                        else: diff_str = "⭐⭐⭐ 어려움"
                        
                        # 깔끔한 캡션 형태로 특성 나열
                        st.caption(f"{dmg_type} | {range_type}")
                        st.caption(f"{style_match} | {diff_str}")
                        
                        # 기존 추천 사유
                        st.info(row['recommend_reason'])
    else:
        st.info("👈 좌측 사이드바에서 시뮬레이션 설정을 맞춘 후 '추천 챔피언 분석하기' 버튼을 눌러주세요.")

# ----------------- 군집화 데이터 탭 -----------------
with tab_cluster:
    st.subheader("챔피언 특징 클러스터링 매핑 (PCA)")
    df_champ['cluster_id'] = df_champ['cluster_id'].astype(str)
    
    fig = px.scatter(
        df_champ, 
        x='pca_x', 
        y='pca_y', 
        color='cluster_name', 
        hover_name='champion_name',
        hover_data=['info_attack', 'info_magic', 'info_difficulty', 'attackrange'],
        title="챔피언별 스탯 기반 전투 스타일 맵",
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("※ 머신러닝이 챔피언의 기본 스탯과 성장치를 분석하여 유사한 전투 스타일끼리 묶어낸 지도입니다.")