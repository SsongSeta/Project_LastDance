# Project LastDance 
### League of Legends Win Structure Analysis

League of Legends 데이터를 기반으로  
**승리 기여 구조를 해석하고 유저 경험 개선 전략을 제안하는 데이터 분석 프로젝트**

---

## 🌐 Language

- 🇰🇷 [Korean](README.md)  
- 🇺🇸 [English](README_EN.md)

---

## 📊 Dashboard Preview

커뮤니티 인식과 실제 경기 데이터를 비교 분석하여  
승리 구조와 포지션별 기여를 Tableau로 시각화했습니다.

추천 시스템은 **Streamlit 기반 인터랙티브 대시보드**로 구현했습니다.

Tableau Dashboard  
https://public.tableau.com/app/profile/.32296278/viz/LoL_17732259346840/sheet0

<p align="center">
  <img src="images/커뮤니티인식분석.png" width="30%">
  <img src="images/실제승리구조분석.png" width="30%">
  <img src="images/포지션별기여구조분석.png" width="30%">
</p>

<p align="center">
  <img src="images/당신만을위한추천시스템1.png" width="30%">
  <img src="images/당신만을위한추천시스템2.png" width="30%">
  <img src="images/당신만을위한추천시스템3.png" width="30%">
</p>

---

## 🎯 Project Overview

리그 오브 레전드 커뮤니티에서는 다음과 같은 의견이 반복적으로 등장합니다.

"정글 차이로 게임이 터진다"  
"서폿은 기여가 잘 보이지 않는다"  
"라인전보다 시스템 영향이 더 큰 것 같다"

하지만 이러한 **유저 체감이 실제 경기 데이터와 일치하는지**는 명확하지 않습니다.

본 프로젝트는

**Community Perception → Match Data → Win Structure**

의 관계를 분석하여  
게임 승리를 설명하는 **구조적 요인**을 분석합니다.

---

## 🏗 Project Architecture

```mermaid
flowchart LR

subgraph Game_Data_Pipeline
A[Riot API] --> B[Match Data Collection]
B --> C[Feature Engineering]
C --> D[Machine Learning]
D --> E[SHAP Interpretation]
end

subgraph Community_Data_Pipeline
F[Reddit Crawling] --> G[Comment Processing]
H[YouTube API] --> G
G --> I[Translation]
I --> J[Community Perception Analysis]
end

E --> K[Win Structure Classification]
J --> K

K --> L[Tableau Dashboard]
K --> M[Streamlit Recommendation]
```

---

## 📦 데이터 소스 및 역할

| Source | Data Type | Role |
|---|---|---|
| Riot API | Quantitative | Match data, model training |
| Data Dragon | Metadata | Champion metadata |
| Reddit / YouTube | Qualitative | Community perception |

---

## 🔄 데이터 수집

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

Data Dragon을 활용하여 챔피언 메타데이터를 매칭했습니다.

포함 정보

- champion id
- champion name
- champion role
- champion stats

---

### Community Data

커뮤니티 인식 분석을 위해 댓글 데이터를 수집했습니다.

- Reddit (Web Crawling)
- YouTube (YouTube API)

---

### Translation

영어 댓글은 **Google Cloud Translation API**를 활용하여 번역했습니다.

---

## 📈 데이터 규모

수집 대상  
Riot API 기반 **15개 서버 랭크 유저 및 매치 데이터**

수집 범위  
**Season 15.1 ~ 16.2**

| Category | Raw Data | Sample |
|---|---|---|
| Users | 7.65M | 15K |
| Matches | 5.73M | 114K |

수집 지표

- match result
- player statistics
- objective events

---

## ⚙️ Feature Engineering

EDA 결과를 기반으로 **경기 승패를 설명하는 주요 Feature를 설계했습니다.**

### Player Performance Features

플레이어 성과 지표

- Gold Earned
- Damage Dealt
- Damage per Minute
- Gold per Minute
- Deaths
- Vision Score

---

### Team Level Features

팀 단위 경기 지표

- Total Team Gold
- Team Damage
- Team Kills
- Objective Control
- Tower Damage

---

### Timeline Features

경기 흐름을 반영하기 위한 지표

- Early Game Gold Difference
- Early Game Kill Difference
- Objective Timing
- Early Death Count

---

### Position Based Features

포지션 역할 차이를 반영한 지표

- Jungle Objective Participation
- Support Vision Contribution
- Carry Damage Share

---

### Match Context Features

경기 맥락을 설명하는 지표

- Game Duration
- Gold Difference
- Kill Difference
- Objective Difference

---

### Feature Selection

모델 학습 전 다음 과정을 통해 Feature를 정제했습니다.

- Correlation Analysis
- Feature Importance
- SHAP 기반 Feature 영향 분석

이를 통해 **모델 해석이 가능한 Feature 집합을 구축했습니다.**

---

## 🔍 Exploratory Data Analysis

EDA는 단순 데이터 요약이 아닌  
**모델 Feature 설계 및 구조 해석을 위한 단계**로 수행되었습니다.

### 주요 분석

1️⃣ Match Structure  
2️⃣ Position Performance  
3️⃣ Feature – Win Relationship  
4️⃣ Timeline Flow  
5️⃣ Performance Variance  
6️⃣ Player Behavior

---

## 🤖 머신러닝 모델

경기 승리 확률을 예측하기 위해 **Tree-based 모델**을 사용했습니다.

### Models

- XGBoost
- LightGBM

### Model Types

Early Game Model  
→ 초반 경기 상태 기반 승리 확률 예측

Full Game Model  
→ 전체 경기 데이터를 기반으로 승리 확률 예측

---

## 🧠 Model Explainability

모델 해석을 위해 **SHAP**을 사용했습니다.

분석 내용

- Feature Importance
- Win probability drivers
- Match outcome structure

---

## 🏆 Match Structure Classification

초반 상황과 경기 결과를 기반으로 경기를 분류했습니다.

| Type | Description |
|---|---|
| COMEBACK | Early disadvantage → Win |
| THROW | Early advantage → Loss |
| STOMP_WIN | Dominant win |
| STOMP_LOSS | Dominant loss |
| NEUTRAL | Balanced match |

---

## 📊 Tableau 대시보드

분석 결과는 Tableau로 시각화했습니다.

1️⃣ Community Perception  
2️⃣ Win Structure Analysis  
3️⃣ Position Contribution  

---

## 🛠 기술 스택

### Language
- Python

### Libraries
- pandas
- numpy
- scikit-learn
- xgboost
- lightgbm
- shap

### APIs
- Riot API
- YouTube API
- Google Translation API

### Visualization
- Tableau
- Streamlit

---

## 📁 Repository Structure

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
 │
 ├ .gitignore
 ├ LICENSE
 └ README.md
```

---

## 📌 Key Insight

이 프로젝트는

- 커뮤니티 인식 분석
- 실제 경기 데이터 분석
- 머신러닝 기반 승리 구조 해석

을 통합하여

**게임 승리를 설명하는 데이터 기반 구조 모델**을 제시합니다.
