# ultralytics CPU→GPU 순차 추론 시 `Invalid CUDA 'device=0'` 에러

## 환경

- Ubuntu 24.04 / ROS2 Jazzy
- Python 3.12, venv (`--system-site-packages`)
- torch 2.12.0+cu130, ultralytics 8.4.56
- NVIDIA Driver 580 / CUDA 13.0 / RTX 4070 Laptop

## 문제 상황

같은 스크립트에서 `device='cpu'` 추론을 먼저 실행한 뒤 `device='cuda'` 추론을 호출하면 GPU 호출에서 에러 발생.

```python
results = model(frame, device='cpu')   # 성공
results = model(frame, device='cuda')  # ValueError
```

에러 메시지:

```
ValueError: Invalid CUDA 'device=0' requested. Use 'device=cpu' or pass valid CUDA device(s) ...
torch.cuda.is_available(): False
torch.cuda.device_count(): 1
os.environ['CUDA_VISIBLE_DEVICES']:
```

스크립트 실행 전 `torch.cuda.is_available()`는 `True`였음.

## 원인

ultralytics `select_device()` 가 `device='cpu'` 호출 시 `CUDA_VISIBLE_DEVICES=""` 로 강제 설정함.

`ultralytics/utils/torch_utils.py:212-215`:

```python
cpu = device == "cpu"
mps = device in {"mps", "mps:0"}
if cpu or mps:
    os.environ["CUDA_VISIBLE_DEVICES"] = ""  # force torch.cuda.is_available() = False
```

이후 torch가 CUDA 컨텍스트를 초기화하면서 "GPU 없음" 상태를 캐싱함. 환경변수를 다시 `'0'` 으로 복원해도 torch 내부 캐시는 갱신되지 않아 GPU 호출 실패.

> 검증: `/home/rokey/ros2_torch_env/lib/python3.12/site-packages/ultralytics/utils/torch_utils.py:212-215` — 일치

## 진단 순서

1. `torch.cuda.is_available()` 단독 확인 → `True` (venv torch 정상)
2. `import ultralytics` 직후 확인 → `True` (import 자체는 영향 없음)
3. `model(frame, device='cpu')` 실행 후 확인 → `False` (CPU 추론이 트리거)
4. ultralytics 소스에서 `CUDA_VISIBLE_DEVICES` 검색 → 215번 줄에서 빈 문자열 설정 확인

## 해결 방법

**GPU 추론을 먼저, CPU를 나중에 실행**하도록 순서 변경.

```python
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # 초기 GPU 고정
from ultralytics import YOLO

model = YOLO('yolov8n.pt')

# GPU 먼저
results = model(frame, device='cuda')

# CPU 나중
results = model(frame, device='cpu')
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # 이후 GPU 호출(track 등) 위해 복원
```

GPU 호출이 먼저 torch CUDA 컨텍스트를 초기화하면 GPU 목록이 정상적으로 잡히고, 이후 CPU 추론이 환경변수를 비워도 torch 캐시는 GPU 상태를 유지함.

## 참고

- ultralytics torch_utils.py select_device 동작
- [PyTorch CUDA semantics — Lazy initialization](https://pytorch.org/docs/stable/notes/cuda.html)
