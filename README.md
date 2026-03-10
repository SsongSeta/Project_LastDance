# Project_LastDance
데이터분석10기 8조 최종프로젝트

```mermaid
flowchart LR

A[Community Data<br>Reddit / YouTube]
B[Game Telemetry<br>Riot API]
C[Champion Metadata<br>Data Dragon]

A --> D[Data Processing]
B --> D
C --> D

D --> E[Feature Engineering]

E --> F[EDA]

F --> G[Win Probability Models]

G --> H[SHAP Explainability]

H --> I[Match Structure Analysis]

I --> J[Tableau Dashboard]
