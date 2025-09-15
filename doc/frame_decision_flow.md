# コマ打ち判定アルゴリズム

```mermaid
flowchart TD
    A["MI(t) スコア列"] --> B["平滑化処理<br/>EMA or 小窓平均"]
    
    B --> C["MI_smooth(t)"]
    
    C --> D{"初期状態?"}
    D -->|Yes| E["初期閾値判定"]
    D -->|No| F["ヒステリシス判定"]
    
    E --> E1{"MI >= 0.60?"}
    E1 -->|Yes| E2["状態: HIGH<br/>2コマ打ち"]
    E1 -->|No| E3{"MI >= 0.35?"}
    E3 -->|Yes| E4["状態: MID<br/>3コマ打ち"]
    E3 -->|No| E5["状態: LOW<br/>保持/タメ"]
    
    F --> F1{"現在状態"}
    F1 -->|HIGH| G["HIGH状態からの遷移"]
    F1 -->|MID| H["MID状態からの遷移"]
    F1 -->|LOW| I["LOW状態からの遷移"]
    
    G --> G1{"MI < 0.55?"}
    G1 -->|Yes| G2{"MI < 0.30?"}
    G1 -->|No| G3["HIGH維持"]
    G2 -->|Yes| G4["LOW遷移"]
    G2 -->|No| G5["MID遷移"]
    
    H --> H1{"MI >= 0.65?"}
    H1 -->|Yes| H2["HIGH遷移"]
    H1 -->|No| H3{"MI < 0.30?"}
    H3 -->|Yes| H4["LOW遷移"]
    H3 -->|No| H5["MID維持"]
    
    I --> I1{"MI >= 0.40?"}
    I1 -->|Yes| I2{"MI >= 0.65?"}
    I1 -->|No| I3["LOW維持"]
    I2 -->|Yes| I4["HIGH遷移"]
    I2 -->|No| I5["MID遷移"]
    
    E2 --> J["状態記録"]
    E4 --> J
    E5 --> J
    G3 --> J
    G4 --> J
    G5 --> J
    H2 --> J
    H4 --> J
    H5 --> J
    I3 --> J
    I4 --> J
    I5 --> J
    
    J --> K["最小区間長チェック<br/>min_duration = 0.08s"]
    
    K --> K1{"区間長 >= min_duration?"}
    K1 -->|Yes| L["状態確定"]
    K1 -->|No| M["前状態を維持"]
    
    L --> N["タメ/ツメ検出"]
    M --> N
    
    N --> N1["加速度A(t)による<br/>ツメ開始点検出"]
    N1 --> N2{"A(t) > threshold<br/>かつ前フレームが低速?"}
    N2 -->|Yes| N3["ツメ開始<br/>前フレームをタメ延長"]
    N2 -->|No| N4["通常処理"]
    
    N3 --> O["フレーム選択処理"]
    N4 --> O
    
    O --> O1{"状態別処理"}
    O1 -->|HIGH| P["2コマ打ち<br/>フレームを1/2間引き"]
    O1 -->|MID| Q["3コマ打ち<br/>フレームを1/3間引き"]
    O1 -->|LOW| R["保持<br/>全フレーム保持<br/>またはポーズ延長"]
    
    P --> S["最終出力フレーム列"]
    Q --> S
    R --> S
    
    style A fill:#e1f5fe
    style F fill:#fff3e0
    style N fill:#f3e5f5
    style S fill:#fce4ec
```

## ヒステリシス閾値設定

```mermaid
graph LR
    A["LOW: MI < 0.35"] -->|MI >= 0.40| B["MID: 0.35 <= MI < 0.60"]
    B -->|MI >= 0.65| C["HIGH: MI >= 0.60"]
    B -->|MI < 0.30| A
    C -->|MI < 0.55| B
    C -->|MI < 0.30| A
    
    style A fill:#e8f5e8
    style B fill:#fff3e0
    style C fill:#ffebee
```

## パラメータ設定

| パラメータ | デフォルト値 | 説明 |
|----------|-------------|------|
| 上位閾値 | 0.60 | HIGH状態への遷移閾値 |
| 下位閾値 | 0.35 | LOW状態への遷移閾値 |
| ヒステリシス幅 | ±0.05 | 状態遷移の余裕 |
| 最小区間長 | 0.08秒 | 状態維持最小時間 |
| 平滑化窓 | 3フレーム | MI値の平滑化窓サイズ |
