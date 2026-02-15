```mermaid
flowchart LR
    A[Input: Kalshi API Data] --> B[STANDARDIZE]
    C[Input: Polymarket API Data] --> B
    B --> D[ANALYZE]
    D --> E[Output:<br>Streamlit Dashboard]
```
