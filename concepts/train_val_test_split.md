# Train / Validation / Test 셋 차이

## 한 줄 요약

학습(train)은 가르치고, 검증(val)은 조율하고, 테스트(test)는 최종 평가한다.

---

## 왜 셋으로 나누는가

같은 데이터로 학습하고 평가하면 모델은 그 데이터에 **과적합(overfitting)** 되어 정확도가 부풀려진다. 실제 새 데이터에서는 성능이 훨씬 낮다. 역할을 분리해야 **진짜 일반화 성능**을 측정할 수 있다.

---

## 각 셋의 역할

| 셋 | 언제 쓰나 | 목적 |
|----|-----------|------|
| **Train** | 학습 중 매 에포크 | 모델 파라미터(가중치) 업데이트 |
| **Validation** | 학습 중간중간 (에포크 끝 등) | 하이퍼파라미터 조정, 조기 종료 기준 |
| **Test** | 학습이 완전히 끝난 뒤 단 한 번 | 최종 성능의 불편 추정(unbiased estimate) |

### Train 셋

- 모델이 직접 보는 데이터
- 손실 함수 역전파 → 가중치 갱신
- 가장 큰 비율 차지

### Validation 셋

- 모델이 학습에 **직접 쓰지는 않지만** 결과를 보며 의사결정에 영향을 준다
  - learning rate, batch size, 레이어 수, dropout 비율 등 하이퍼파라미터 튜닝
  - Early stopping: val loss가 더 이상 줄지 않으면 학습 중단
- **val셋에 반복적으로 맞추다 보면 간접적 data leakage 발생 가능** → test셋과 반드시 분리

### Test 셋

- 최종 배포 전 단 한 번만 사용
- 여기서 나온 지표가 실세계 성능의 대리 지표
- 여러 번 사용하거나 결과를 보고 모델을 수정하면 **test leakage** — 이 시점부터 test셋은 사실상 validation셋이 됨

---

## Data Leakage (데이터 누수)

| 유형 | 설명 |
|------|------|
| **Train↔Val 중복** | val 샘플이 train에 포함 → val 점수가 부풀려짐 |
| **Train↔Test 중복** | 가장 심각 — 최종 성능이 신뢰 불가 |
| **간접 leakage** | val 결과를 보고 하이퍼파라미터 반복 수정 → test 전까지는 괜찮지만 test도 여러 번 쓰면 누수 |
| **시계열 누수** | 미래 데이터가 과거 훈련셋에 포함 (시계열에서 랜덤 split 사용 시 발생) |

---

## 분할 비율

| 데이터 규모 | 전형적 비율 | 비고 |
|-------------|-------------|------|
| 일반적 | 70 / 15 / 15 | 가장 흔한 기본값 |
| 소규모 | 60 / 20 / 20 | val·test 통계 유의성 확보 |
| 대규모 (수백만~) | 98 / 1 / 1 | 1%도 수만 건이면 충분 |

> 검증: [Google ML Crash Course — Dividing Datasets](https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets) — 70/15/15 권장, 통계적 유의성 강조 — 일치  
> 검증: [v7labs — Train Validation Test Split](https://www.v7labs.com/blog/train-validation-test-split), [encord](https://encord.com/blog/train-val-test-split/) — 60~80/10~20/10~20 범위 — 일치

핵심: **비율보다 각 셋이 충분히 대표성 있는 크기인지가 더 중요하다.**

---

## 학습 루프에서의 흐름

```
에포크 시작
  └─ train 셋으로 순전파 + 역전파 → 가중치 업데이트
에포크 끝
  └─ val 셋으로 순전파만 → loss/metric 기록
       └─ val loss 개선 없으면 early stopping or lr 감소

학습 완료 후
  └─ test 셋으로 단 한 번 평가 → 최종 지표 보고
```

---

## 자주 혼동하는 포인트

**"val셋은 학습에 안 쓰이니까 test랑 같은 거 아닌가?"**

→ 아니다. val 결과를 보고 하이퍼파라미터를 수정하는 행위 자체가 val셋에 간접적으로 맞추는 것이다. test셋은 이 과정에서 완전히 격리되어야 한다.

**"test셋을 여러 번 써서 가장 좋은 모델을 고르면 안 되나?"**

→ 안 된다. 그 순간 test셋이 val셋 역할을 하게 되고, 진짜 일반화 성능은 알 수 없어진다. 모델 선택은 val셋으로만.

---

## 관련 기법

- **K-Fold Cross Validation**: 데이터가 적을 때 train/val을 K번 바꿔가며 평균 성능 측정. test셋은 여전히 별도 유지.
- **Stratified Split**: 클래스 불균형 데이터에서 각 셋의 클래스 비율을 원본과 동일하게 유지.
- **시계열 Split**: 랜덤 셔플 금지 — 과거로 미래를 예측하는 방향성 유지.
