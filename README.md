# Project_LastDance 
### League of Legends Win Structure Analysis

League of Legends 데이터 기반으로 **승리 기여 구조 해석 및 유저 경험 개선 전략을 제안하는** 프로젝트입니다.





Python / Riot API / XGBoost / LightGBM / SHAP / Tableau

---

🇰🇷 한국어  -> README.md 

🇺🇸 English -> README_EN.md

---

## 대시보드 Preview

커뮤니티 인식과 실제 경기 데이터를 비교 분석하여 승리 구조와 포지션별 기여를 Tableau로 시각화하고

추천 시스템을 Streamlit으로 시각화하였습니다.

https://public.tableau.com/app/profile/.32296278/viz/LoL_17732259346840/sheet0

<p align="center">
  <img src="images/커뮤니티인식분석.png" width="30%">
  <img src="images/실제승리구조분석.png" width="30%">
  <img src="images/포지션별기여구조분석.png" width="30%">
  <img src="images/당신만을위한추천시스템1.png" width="30%">
  <img src="images/당신만을위한추천시스템2.png" width="30%">
  <img src="images/당신만을위한추천시스템3.png" width="30%">
</p>

---

## 프로젝트 개요

리그 오브 레전드 커뮤니티에서는 다음과 같은 의견이 반복적으로 등장합니다.

"정글 차이로 게임이 터진다"  
"서폿은 기여가 잘 보이지 않는다"  
"라인전보다 시스템 영향이 더 큰 것 같다"

하지만 이러한 **유저 체감이 실제 경기 데이터와 일치하는지**는 명확하지 않습니다.

이 프로젝트는

커뮤니티 인식 -> 실제 경기 데이터 -> 승리 구조

의 관계를 분석하여 **게임 승리를 설명하는 구조적 요인**을 분석합니다.

---

## 📊 데이터 소스 및 역할

| 데이터 소스 | 데이터 유형 | 역할 |
|---|---|---|
| 🎮 **Riot API** | 정량 데이터 | 핵심 분석 데이터<br>• 승리 구조 해석<br>• 머신러닝 모델 학습 |
| 🧩 **Data Dragon** | 정적 메타데이터 | 챔피언 정보 매핑<br>• 게임 메타 데이터 |
| 💬 **Reddit / YouTube** | 정성 데이터 | 커뮤니티 인식 분석<br>• 문제 제기 및 분석 방향 설정 |

---

## 프로젝트 아키텍처

```

[Game Data (Riot API)]

match-v5
timeline-v5
        │
        ▼
Match Event Data
        │
        ▼
Champion Metadata
(Data Dragon)
        │
        ▼
Feature Engineering
        │
        ▼
Exploratory Data Analysis
        │
        ▼
Machine Learning Models
=================================================================================================================================

[Community Data (Reddit / YouTube)]

Reddit (Web Crawling)
YouTube (Youtube API)
        │
        ▼
Comment Processing
Translation (Google Translation API)
        │
        ▼
Community Perception Analysis
=================================================================================================================================

[Machine Learning (XGBoost,LightGBM)]

Early Game Model
Full Game Model
        │
        ▼
Model Explainability

SHAP Analysis
        │
        ▼
Match Structure Classification

COMEBACK
THROW
STOMP
NEUTRAL
        │
        ▼
Tableau Dashboards

1. Community Perception
2. Win Structure Analysis
3. Position Contribution
```

---

## 데이터 수집

### Riot API

사용 API

- match-v5
- timeline-v5

수집 데이터

- match metadata
- participant statistics
- timeline events

---

### Champion Metadata

챔피언 데이터는 **Data Dragon**을 통해 수집했습니다.

포함 정보

- champion id
- champion name
- champion role
- champion stats

---

### Community Data

커뮤니티 인식을 분석하기 위해 댓글 데이터를 수집했습니다.

데이터 출처

- Reddit 댓글 (웹 크롤링)
- YouTube 댓글 (YouTube API)

---

### Translation

영어권 댓글 데이터는 **Google Cloud Translation API**를 통해 번역했습니다.

---

## Data 규모

수집 대상  
Riot API 기반 **15개 서버** 랭크 유저 및 매치 데이터

수집 범위  
**시즌 15.1 ~ 16.2**의 15개 서버 랭크 5:5 매치 데이터

데이터 규모  
**유저** 약 765만 명 → 0.2% 샘플 **약 15,000명**  
**매치** 약 573만 경기 → 2% 샘플 **약 114,000경기**

수집 지표  
매치 승패와 관련된 주요 플레이 및 오브젝트 지표

---

## 탐색적 데이터 분석 (EDA)

<br>

> 본 EDA는 단순한 데이터 요약이 아니라  
> **모델 Feature 설계 및 SHAP 해석을 위한 변수 구조 확정 단계**로 수행하였습니다.

<br>

## 🔎 EDA Overview

EDA는 다음 **6가지 관점**에서 진행되었습니다.

| 단계 | 분석 내용 |
|---|---|
| ① | 기본 매치 구조 파악 |
| ② | 포지션별 성과 스케일 분석 |
| ③ | 변수와 승리 간 관계 분석 |
| ④ | 타임라인 기반 경기 흐름 분석 |
| ⑤ | 성과 분산 및 리스크 구조 분석 |
| ⑥ | 유저 단위 플레이 구조 분석 |

---

# ① 🎮 기본 매치 구조 파악

## 목적
- 경기 메커니즘 이해
- 변수 스케일 기준 확보

## 주요 통계

| 지표 | 값 |
|---|---|
| 평균 경기 길이 | **30.34분** |
| 평균 최종 골드 | **11,713** |
| 평균 킬 수 | **32.13** |
| 최대 킬 수 | **105** |
| 최소 킬 수 | **1** |
| 평균 오브젝트 수 | **7.49** |

### 핵심 인사이트

- 경기 구조의 **기본 분포 확인**
- 변수 정규화 기준 확보

---

# ② 🧭 포지션별 스케일 차이 탐색

## 분석 목적
포지션 역할 차이를 반영한 **성과 구조 파악**

## 분석 지표

| 카테고리 | 지표 |
|---|---|
| 자원 | Gold, Gold per Minute |
| 전투 | Total Damage, Damage per Minute |
| 리스크 | Deaths |
| 시야 | Vision Score, Control Wards |
| 오브젝트 | Tower Damage |
| 지원 | Ally Shield, Ally Heal |

## 추가 분석

**Champion × Lane 구조**

목적

- 챔피언이 **주 라인이 아닌 포지션에서 플레이할 경우 성과 변화 확인**

### 인사이트

- 포지션별 성과 구조가 명확히 다름
- **포지션 단위 Feature 필요**

---

# ③ 📈 변수 — 승리 관계 분석

## 분석 방법

- Point-Biserial Correlation
- 승률 구간 분석
- 통계적 유의성 검증

## 분석 변수

- Gold Earned
- Deaths
- Vision Score
- Damage per Minute
- Vision per Minute

---

## 주요 결과

| 변수 | 관계 | 해석 |
|---|---|---|
| Gold | 양의 상관 | 골드 증가 → 승률 상승 |
| Deaths | 음의 상관 | 데스 증가 → 승률 감소 |
| Vision Score | 양의 상관 | 시야 확보 → 승리 확률 상승 |

### 구간 분석

**Deaths**

- 데스 증가 시 승률 급격히 감소

**Gold**

- 상위 분위수일수록 승률 증가

---

# ④ ⏱ 타임라인 기반 경기 구조

## 10분 열세 상황

**10분 시점 5데스 이상 팀 승률**

```
44.3%
```

➡ 초반 다수 데스는 강력한 패배 신호

---

## 열세 강도와 승률

| 골드 차이 | 승률 경향 |
|---|---|
| -1k ~ 0 | 비교적 안정 |
| -10k ~ -5k | 승률 급락 |

---

## 첫 오브젝트 효과

분석 결과

첫 오브젝트 획득이 **열세 복구 트리거가 아님**

열세 팀이 무리하게 오브젝트를 시도하면서  
추가 손실이 발생하는 경우가 관찰됨

---

## 역전 경기 구조

특징

- 10분 이전 → 완만
- 10~20분 → 변동성 증가
- 역전 → **중반 교전 누적 구조**

---

# ⑤ ⚠️ 성과 분산 및 리스크 구조

## 분석 지표

- CV (Coefficient of Variation)
- 90–10 Spread
- Extreme Rate

## 팀 단위 변동성

| 변수 | 변동성 |
|---|---|
| Total Damage | 가장 높음 |
| Deaths | 중간 |
| Vision Score | 중간 |
| Gold | 가장 낮음 |

### 해석

리스크 중심 변수는 **교전 지표 (Damage)**

Gold는 결과 변수 성격

---

## 포지션별 리스크

| 포지션 | 특징 |
|---|---|
| UTILITY | 높은 딜 변동성 |
| JUNGLE | 상대적으로 높은 리스크 |
| MID | 비교적 안정 |

### 핵심 구조

- Damage → 핵심 리스크 변수
- Gold → 안정적 누적 자원
- Deaths → 보조 리스크 변수

---

# ⑥ 👤 유저 단위 플레이 구조

## 분석 대상

- **5매치 이상 플레이 유저**

## 포지션 정의

| 구분 | 정의 |
|---|---|
| Main Position | 가장 많이 플레이한 포지션 |
| Sub Position | 두 번째 포지션 |

---

## 포지션 집중도 지표

- HHI (Herfindahl–Hirschman Index)
- Shannon Entropy

```python
df_pos['ratio'] = df_pos['play_count'] / df_pos['total_games']

df_pos['hhi_term'] = df_pos['ratio'] ** 2
df_pos['entropy_term'] = df_pos['ratio'] * np.log(df_pos['ratio'])

metrics_df = df_pos.groupby('puuid').agg(
    concentration_index=('hhi_term', 'sum'),
    diversity_index=('entropy_term', lambda x: -x.sum())
).reset_index()
```

---

## 플레이 그룹 정의

**Group A**

- Main / Sub 포지션 플레이

**Group B**

- 비주 포지션 플레이
- 포지션 스왑 포함

---

## 성과 비교 지표

- 승률
- KDA
- K / D / A
- 최종 골드
- 챔피언 피해량

통계 검정

- Chi-square test
- Welch's T-test

---

# 📌 EDA 핵심 결론

1️⃣ 경기 리스크 중심은 **교전 지표 (Damage)**  

2️⃣ Gold는 **안정적인 결과 변수**

3️⃣ 초반 다수 데스는 **구조적 패배 신호**

4️⃣ 역전은 **중반 교전 누적 구조**

5️⃣ 포지션 리스크는 **딜 지표에서 가장 명확히 나타남**

---

💡 본 EDA를 기반으로

- Feature Engineering
- Machine Learning Model
- SHAP 기반 모델 해석

이 진행되었습니다.

---

## 머신러닝 모델

경기 승리 확률을 예측하기 위해 **트리 기반 머신러닝 모델**을 사용했습니다.

사용 모델

- XGBoost
- LightGBM

모델 구성

Early Game Model  
-> 초반 게임 상태 기반 승리 확률 예측

Full Game Model  
-> 전체 경기 데이터를 기반으로 승리 확률 예측

---

## 모델 해석

모델 해석을 위해 **SHAP**을 사용했습니다.

분석 내용

- Feature Importance
- 승리 확률 영향
- 경기 구조 해석

---

## 경기 구조 분류

초반 상황과 최종 결과를 기반으로 경기를 분류했습니다.

COMEBACK  
THROW  
STOMP_WIN  
STOMP_LOSS  
NEUTRAL  

이를 통해

- 역전 경기 구조
- 초반 격차 영향
- 승리 패턴

을 분석했습니다.

---

## Tableau 대시보드

분석 결과는 Tableau로 시각화했습니다.

1. Community Perception Dashboard  
2. Win Structure Analysis Dashboard  
3. Position Contribution Dashboard  

---

## 기술 스택

**Language**
- Python

**Library**
- pandas
- numpy
- scikit-learn
- xgboost
- lightgbm
- shap
- matplotlib

**API**
- Riot API
- YouTube API
- Google Translation API

**Visualization**
- Tableau
- Streamlit

---

## Repository Structure

```
project
 ├ code
 │   ├ 01_Riot_API
 │   ├ 02_Comment
 │   ├ 03_Analysis_pipeline
 │   ├ 04_Streamlit_dashboard
 │   └ ETC
 │
 ├ images
 │   └ images
 │ 
 ├ .gitignore
 ├ MIT LICENSE
 └ README.md
```
