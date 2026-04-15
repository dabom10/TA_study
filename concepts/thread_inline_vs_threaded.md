# 싱글 스레드 vs 멀티 스레드 (Inline vs Threaded)

## 한 줄 요약
스레드는 프로그램 안에서 동시에 실행되는 흐름의 단위. Inline은 흐름 1개, Threaded는 흐름 2개 이상.

## 핵심 내용

### 스레드란?
프로그램(프로세스) 안에서 **동시에 실행되는 흐름**. 멀티 스레드는 하나의 프로세스 안에서 여러 흐름이 병렬 실행된다.

```
프로세스 (프로그램 1개)
├── 스레드 1 (메인)     ← 싱글 스레드는 이것만 존재
└── 스레드 2 (캡처용)  ← 멀티 스레드는 이게 추가됨
```

> 멀티 스레드 ≠ 멀티 프로세스. 같은 프로세스 안에서 흐름만 나뉘는 것.

---

### Inline = 싱글 스레드

```
메인 스레드 하나만 존재

[캡처] → [처리] → [표시] → [캡처] → [처리] → [표시] → ...
```

- 처리가 끝나야 다음 캡처로 넘어갈 수 있음
- 처리가 무거우면 전체 FPS가 낮아짐

---

### Threaded = 멀티 스레드

```
스레드 1 (캡처 전용)
[캡처] → [캡처] → [캡처] → [캡처] → ...  (shared_frame 계속 덮어씀)
           ↕ shared_frame (공유 변수)
스레드 2 (처리 전용, 메인)
[처리] → [표시]        → [처리] → [표시] → ...
```

- 캡처와 처리가 독립적으로 동시 실행
- 처리가 느려도 캡처는 멈추지 않음
- **주의:** 처리가 느리면 그동안 캡처된 프레임은 버려지고 최신 프레임만 사용됨 (큐가 아니라 단순 덮어쓰기이기 때문)

---

### 공유 변수와 lock

두 스레드가 같은 `shared_frame`에 동시 접근하면 깨진 프레임이 나올 수 있음 → `lock`으로 동시 접근 차단

```python
shared_frame = None
lock = threading.Lock()

# 스레드 1: 쓰기
with lock:
    shared_frame = frame.copy()

# 스레드 2 (메인): 읽기
with lock:
    frame = shared_frame.copy()
```

`with lock:` 블록 안은 한 번에 하나의 스레드만 진입 가능.

---

### 비교 표

| | Inline | Threaded |
|--|--|--|
| 흐름 수 | 1개 | 2개 |
| 캡처와 처리 | 순차 | 동시 |
| 처리가 느리면 | 캡처도 느려짐 | 캡처는 그대로, 중간 프레임 버려짐 |
| FPS | 낮음 | 높음 |
| 코드 복잡도 | 단순 | lock 등 동기화 필요 |

---

### 실험 코드 위치
`~/to_students/day2/2_1_c_capture_wc_thread.py`

- `run_inline()`: 싱글 스레드, 블러 10번 반복으로 무거운 처리 시뮬레이션
- `run_threaded()`: 멀티 스레드, `webcam_thread`가 캡처 전담
- 10초 동안 실행 후 평균 FPS 출력으로 성능 차이 직접 확인 가능

---

### 이후 연결 개념
`2_4_g_yolov8_obj_det.py`, `2_4_h_yolov8_obj_det_thread.py` — YOLO 추론을 별도 스레드로 분리하는 구조에 이 개념이 그대로 적용됨

## 다른 섹션과의 연결
- [ros2_communication_concepts.md](ros2_communication_concepts.md) — ROS2 spin/spin_once와 스레드 분리 패턴
- `2_4_g`, `2_4_h`: Queue(maxsize=1)로 최신 프레임 1개만 유지하는 동일 패턴

## 의문점 / 나중에 파고들 것
- Python GIL(Global Interpreter Lock)이 멀티 스레드 성능에 미치는 영향
- `Queue` vs `shared_frame` 덮어쓰기 방식의 트레이드오프
