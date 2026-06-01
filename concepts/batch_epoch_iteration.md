# Batch / Epoch / Iteration

모델 학습 시 데이터를 얼마나 묶어서, 몇 바퀴 돌릴지 정하는 핵심 하이퍼파라미터.

> 검증: [MachineLearningMastery — Difference Between a Batch and an Epoch](https://machinelearningmastery.com/difference-between-a-batch-and-an-epoch/) — 일치
> 검증: [Nebius — Epochs vs iterations in machine learning](https://nebius.com/blog/posts/epochs-vs-iterations-in-machine-learning) — 일치

## 한 줄 정의

| 용어 | 의미 |
|------|------|
| **Batch (배치)** | 가중치를 한 번 업데이트하기 전에 처리하는 **샘플 묶음** |
| **Epoch (에폭)** | 전체 학습 데이터를 **한 바퀴 다 도는 것** |
| **Iteration (이터레이션)** | 배치 1개를 처리하고 가중치를 1회 업데이트하는 **한 스텝** |

## 관계

데이터 1000장, batch size 100인 경우:

```
1 epoch       = 데이터 1000장 전부 1회 통과
1 batch       = 100장 묶음
1 iteration   = 배치 1개 처리 + 가중치 1회 업데이트

1 epoch 안의 iteration 수 = 1000 ÷ 100 = 10번
```

핵심:
- **batch** = "한 번 업데이트하는 단위"
- **epoch** = "데이터를 통째로 몇 번 반복하느냐"
- **iteration 수/epoch = 전체 샘플 수 ÷ batch size**

## YOLO(Ultralytics)에서의 인자

`yolo train` 실행 시:

| 인자 | 의미 |
|------|------|
| `epochs` | 데이터셋을 몇 바퀴 돌릴지 (예: `epochs=100`) |
| `batch` | 한 번에 몇 장 처리할지 (예: `batch=16`) |

- `epochs` ↑ → 같은 데이터를 더 여러 번 학습 (과도하면 과적합)
- `batch` ↑ → GPU 메모리(VRAM)를 더 쓰지만 학습이 안정적·빠름, 부족하면 OOM 에러

> 미검증: YOLO `batch=-1` 자동 배치 설정 등 Ultralytics 고유 동작 — 위 검색 범위 밖, 공식 문서 별도 확인 필요

## 관련 노트

- [train_val_test_split.md](train_val_test_split.md) — 학습 데이터 분할
- [cpu_core_gpu_concepts.md](cpu_core_gpu_concepts.md) — GPU/VRAM과 batch size 관계
