# CPU / Core / GPU / 병렬·동시성 개념

## 한 줄 요약
**CPU**는 연산을 담당하는 칩, **core(코어)**는 그 칩 안의 실제 계산 유닛, **GPU**는 작고 느린 코어를 수천 개 모아 같은 작업을 한꺼번에 처리하는 칩. threading/parallel은 이 코어들을 놀지 않게 쓰는 소프트웨어 전략.

> 검증: [Liquid Web — CPU Cores vs Threads](https://www.liquidweb.com/blog/difference-cpu-cores-thread/), [AWS — GPU vs CPU](https://aws.amazon.com/compare/the-difference-between-gpus-cpus/), [Splunk — CPU vs GPU](https://www.splunk.com/en_us/blog/learn/cpu-vs-gpu.html), [AnalyticsVidhya — Multithreading vs Multiprocessing](https://www.analyticsvidhya.com/blog/2023/07/multithreading-vs-multiprocessing/) — 일치

---

## 핵심 내용

### 1. 하드웨어 계층 (위에서 아래로)

```
컴퓨터
└── CPU (칩 1~2개, "두뇌")
    ├── Core 0   ← 실제로 계산하는 독립 유닛
    ├── Core 1
    ├── ...
    └── Core N   (소비자용 보통 4~16개, 서버 64개 이상)
```

- **CPU (Central Processing Unit)**: 컴퓨터의 범용 연산 칩. 메인보드에 꽂히는 그 칩 1개.
- **Core (코어)**: CPU 칩 안에 들어있는 **실제 계산 단위**. 코어 1개 = 한 번에 작업 1개를 처리하는 독립 처리기.
  - 옛날엔 CPU 1개 = 코어 1개 → 모든 게 일렬(순차).
  - 지금은 CPU 1개 안에 코어 여러 개(멀티코어) → 동시에 여러 작업.
- **Hyper-Threading (논리 스레드)**: 코어 1개가 자기 자원(캐시·레지스터·실행유닛)을 둘로 쪼개 **스레드 2개를 동시 실행**하는 것처럼 보이게 하는 인텔 기술. 그래서 "8코어 16스레드" 같은 표기가 나옴. 물리 코어가 2배 되는 건 아님.

> 검증: [Guru99 — CPU Core/Multicore/Thread](https://www.guru99.com/cpu-core-multicore-thread.html), [Liquid Web](https://www.liquidweb.com/blog/difference-cpu-cores-thread/) — 일치

---

### 2. 메모리 공유 관계 (★ 메모 교정 포인트)

| 단위 | 메모리 공유? |
|------|------------|
| **같은 CPU의 코어들** | 메인 메모리(RAM) **공유**, 보통 L3 캐시도 공유. 단 L1/L2 캐시는 코어별 개별 |
| **같은 프로세스의 스레드들** | 프로세스의 메모리 공간을 **공유** (그래서 가볍고 데이터 주고받기 쉬움) |
| **서로 다른 프로세스들** | 메모리 **분리**. 데이터 주고받으려면 IPC(프로세스 간 통신) 필요 |

> 메모에 "core는 memory 공유 안 함"이라고 적혀 있는데, **이건 정확히는 틀림.**
> 한 CPU 안의 코어들은 RAM을 같이 쓴다. "메모리를 안 나눠 쓰는 것"은 **코어가 아니라 프로세스**(멀티프로세싱)이거나, 아예 떨어진 컴퓨터끼리 하는 **분산 메모리(distributed memory) 병렬 처리**의 이야기.

---

### 3. CPU vs GPU

|  | **CPU** | **GPU** |
|--|---------|---------|
| 코어 수 | 적음 (2~64개) | 수백~수천 개 (RTX 4090 = 16,384 CUDA 코어) |
| 코어 1개 성능 | 강함, 빠름 | 약함, 느림 |
| 잘하는 것 | 다양하고 복잡한 작업, 순차·분기 많은 로직, 낮은 지연(latency) | 같은 연산을 대량으로 동시에 (그래픽 렌더링, 행렬연산, AI 학습) |
| 비유 | 만능 일꾼 몇 명 | 단순 작업만 하는 일꾼 수천 명 |

- 핵심: **GPU 코어는 CPU 코어보다 느리지만, 수천 개가 동시에 같은 작업**을 하면 "쪼갤 수 있는 큰 문제"는 훨씬 빨리 끝난다.
- 그래서 영상·AI처럼 "똑같은 계산을 데이터만 바꿔 엄청 많이" 하는 일은 GPU, 복잡한 판단·제어 로직은 CPU.

> 검증: [AWS — GPU vs CPU](https://aws.amazon.com/compare/the-difference-between-gpus-cpus/), [Splunk](https://www.splunk.com/en_us/blog/learn/cpu-vs-gpu.html), [DigitalOcean — Parallel Computing GPU vs CPU](https://www.digitalocean.com/community/tutorials/parallel-computing-gpu-vs-cpu-with-cuda) — 일치

---

### 4. 소프트웨어 전략: 멀티스레딩 vs 멀티프로세싱 vs 병렬 vs 동시성

| 용어 | 의미 | 메모리 |
|------|------|--------|
| **멀티스레딩 (Multithreading)** | 한 프로세스 안에서 흐름(스레드) 여러 개 | **공유** |
| **멀티프로세싱 (Multiprocessing)** | 프로세스 여러 개를 동시에 | **분리** (IPC 필요) |
| **병렬성 (Parallelism)** | 여러 코어에서 **진짜 동시에** 실행 | 공유(스레드)일 수도, 분리(프로세스/분산)일 수도 |
| **동시성 (Concurrency)** | 코어 하나에서 작업들을 빠르게 번갈아 → "동시처럼 보이게". 한 작업이 디스크/네트워크 기다리는 idle 시간에 다른 작업을 끼워넣음 | - |

- 메모의 "비는 공간(idle)을 다른 process로 채운다 / CPU가 쉬지 않게 한다"(10~12번) → 정확히는 **동시성(concurrency)** 개념. I/O 대기로 노는 시간을 다른 일로 메우는 것.
- 메모의 "토탈 시간을 줄인다"(parallel) → 여러 코어에서 **동시 실행하는 병렬성(parallelism)** 개념.
- 메모 6번 "threading은 멀티프로세싱의 한 버전" → 정확히는 **둘은 별개 모델.** 스레딩=메모리 공유, 멀티프로세싱=메모리 분리.

> ⚠️ 주의: **코어가 1개뿐이면 멀티스레딩을 해도 진짜 병렬이 안 되어 속도 이득이 거의 없다.** 진짜 동시 실행은 코어가 여러 개일 때만 가능.
> (Python은 추가로 GIL 때문에 CPU 위주 작업은 멀티스레딩으로 병렬화가 안 됨 → 그땐 멀티프로세싱을 씀. ROS2 콜백 구조와 직접 연결되는 부분이라 별도로 파고들 가치 있음.)

> 검증: [AnalyticsVidhya](https://www.analyticsvidhya.com/blog/2023/07/multithreading-vs-multiprocessing/) — 일치

---

## 다른 개념과의 연결
- [[thread_inline_vs_threaded]] — 이 문서가 "하드웨어(코어)" 레벨이라면, 그쪽은 "소프트웨어 흐름(스레드)" 레벨. 코어 위에 스레드가 올라간다.
- ROS2 Executor(SingleThreaded / MultiThreaded), 콜백 그룹 → 어떤 콜백을 어느 스레드에 올릴지 결정하는 부분. 메모 14번 "event마다 function을 CPU에 얹는다"가 이것.

## 의문점 / 나중에 파고들 것
- Python GIL이 ROS2 MultiThreadedExecutor에서 실제로 어떻게 동작하나? (CPU-bound vs I/O-bound 콜백 차이)
- 슈퍼컴퓨팅의 "분산 메모리 병렬(MPI)" vs "공유 메모리 병렬(OpenMP)" 구분
