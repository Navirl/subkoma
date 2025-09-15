# MotionIntensity スコア計算フロー

```mermaid
flowchart TD
    A["フレーム t のキーポイント<br/>p_i(t) = (x_i(t), y_i(t))<br/>i = 1..N"] --> B["キャラクタースケール<br/>S(t) = bbox対角長"]
    
    B --> C["正規化変位計算"]
    C --> C1["各キーポイントi:<br/>d_i(t) = ||p_i(t) - p_i(t-1)|| / S(t)"]
    C1 --> C2["平均変位:<br/>D(t) = (1/N) Σ d_i(t)"]
    
    B --> D["速度計算"]
    D --> D1["各キーポイントi:<br/>v_i(t) = d_i(t) / Δt"]
    D1 --> D2["平均速度:<br/>V(t) = (1/N) Σ v_i(t)"]
    
    D2 --> E["加速度計算"]
    E --> E1["各キーポイントi:<br/>a_i(t) = (v_i(t) - v_i(t-1)) / Δt"]
    E1 --> E2["平均加速度:<br/>A(t) = (1/N) Σ a_i(t)"]
    
    B --> F["方向変化計算"]
    F --> F1["ベクトル:<br/>u_i(t) = p_i(t) - p_i(t-1)"]
    F1 --> F2["角度変化:<br/>θ_i(t) = arccos(u_i(t)·u_i(t-1) / (||u_i(t)|| ||u_i(t-1)|| + ε))"]
    F2 --> F3["正規化方向変化:<br/>Θ(t) = (1/N) Σ (θ_i(t) / π)"]
    
    B --> G["ポーズ変化計算"]
    G --> G1["関節角度差の平均<br/>P(t) = pose_change_normalized"]
    
    C2 --> H["正規化処理"]
    D2 --> H
    E2 --> H
    F3 --> H
    G1 --> H
    
    H --> H1["各量を0-1範囲に正規化:<br/>D̃(t), Ṽ(t), Ã(t), Θ̃(t), P̃(t)"]
    
    H1 --> I["重み付き和計算"]
    I --> I1["MotionIntensity(t) =<br/>wD × D̃(t) +<br/>wV × Ṽ(t) +<br/>wA × Ã(t) +<br/>wΘ × Θ̃(t) +<br/>wP × P̃(t)"]
    
    I1 --> J["デフォルト重み:<br/>wD=0.30, wV=0.25, wA=0.20<br/>wΘ=0.15, wP=0.10"]
    
    J --> K["MI(t) ∈ [0, 1"]]
    
    style A fill:#e1f5fe
    style I1 fill:#fff3e0
    style K fill:#fce4ec
    style H1 fill:#f3e5f5
```

## 数式詳細

### 1. 正規化変位
```
d_i(t) = ||p_i(t) - p_i(t-1)|| / S(t)
D(t) = (1/N) Σ d_i(t)
```

### 2. 速度
```
v_i(t) = d_i(t) / Δt
V(t) = (1/N) Σ v_i(t)
```

### 3. 加速度
```
a_i(t) = (v_i(t) - v_i(t-1)) / Δt
A(t) = (1/N) Σ a_i(t)
```

### 4. 方向変化
```
θ_i(t) = arccos((u_i(t)·u_i(t-1)) / (||u_i(t)|| ||u_i(t-1)|| + ε))
Θ(t) = (1/N) Σ (θ_i(t) / π)
```

### 5. 最終スコア
```
MI(t) = wD×D̃(t) + wV×Ṽ(t) + wA×Ã(t) + wΘ×Θ̃(t) + wP×P̃(t)
```
