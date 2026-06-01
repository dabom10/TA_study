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

### 5. 락(Lock)과 데드락(Deadlock) (★ 메모 교정 포인트)

스레드들은 메모리를 **공유**하기 때문에(섹션 2), 두 스레드가 같은 데이터에 동시에 접근하면 문제가 생긴다. 그런데 **그 문제의 이름이 데드락은 아니다.**

| 문제 | 정의 | 해결 |
|------|------|------|
| **레이스 컨디션 (Race condition)** | 둘 이상이 공유 데이터에 **동시 접근** → 실행 순서에 따라 결과가 달라짐(망가짐) | 내가 쓰는 메모리를 **lock(잠금)** 하고 사용 |
| **데드락 (Deadlock)** | 서로 상대가 쥔 자원을 기다리며 **둘 다 멈춤**. A가 X를 쥔 채 Y를 기다리고, B가 Y를 쥔 채 X를 기다림 → 영원히 정지 | lock을 **조심해서** 써야 함 (잘못 쓰면 오히려 데드락 발생) |

> 메모 "메모리 동시 access → deadlock, 그래서 lock 필수"는 **순서가 뒤바뀜.**
> - 동시 access로 데이터가 깨지는 건 **레이스 컨디션** → 이걸 막으려고 **lock**을 건다. (여기까지 메모의 결론 "lock 필수"는 맞음)
> - **데드락은 오히려 lock을 잘못 써서** 생기는 별개 문제다. lock이 데드락을 막는 게 아니라, lock 사용이 데드락의 전제 조건.

**데드락의 4가지 필요조건 (Coffman conditions — 4개가 동시에 성립해야 발생):**
1. **상호 배제(Mutual Exclusion)**: 자원을 한 번에 한 명만 점유
2. **점유와 대기(Hold and Wait)**: 자원을 쥔 채로 다른 자원을 기다림
3. **비선점(No Preemption)**: 남이 쥔 자원을 강제로 뺏을 수 없음
4. **순환 대기(Circular Wait)**: 대기가 고리(A→B→A) 형태

→ 이 중 **하나만 깨면 데드락 예방**. (예: 항상 정해진 순서로만 lock을 잡으면 순환 대기가 안 생김)

> 검증: [JMU OpenCSF — Deadlock](https://w3.cs.jmu.edu/kirkpams/OpenCSF/Books/csf/html/Deadlock.html), [DesignGurus — Race Conditions/Deadlocks](https://designgurus.substack.com/p/mastering-multithreading-patterns) — 일치

---

### 6. 스레딩은 "코드"가 아니라 "OS"가 한다

| 옛날 (순차 프로그램) | 객체지향 이후 |
|----------------------|----------------|
| 프로그램 = **잘리지 않는 한 덩어리** | 프로그램 = class·method(함수) 단위로 **쪼갤 수 있는 조각들의 모음** |
| 통째로 실행 | 함수만 / 클래스만 / 전체를 골라 실행 가능 |

- 메모 정리: 객체지향(class·function)으로 짜면 프로그램이 **여러 piece**로 나뉘고, **내 로직이 필요로 하는 조각만** 골라 CPU(코어) 위에 얹어 실행 → 끝나면 내려놓음.
- ★ 핵심: **threading 기능은 내 코드 안이 아니라 OS(커널) 안에 있다.**
  - 코드/라이브러리는 "이 함수를 스레드로 돌려줘"라고 **요청**만 한다.
  - 실제로 **어느 코어의 큐에 넣고, 언제, 얼마나 실행할지 결정(스케줄링)**하는 건 OS 스케줄러.
  - 각 CPU(코어)마다 실행 대기줄(run queue)이 있고, 같은 스레드가 동시에 두 코어에 올라갈 수는 없다. 코어 간 부하가 쏠리면 OS가 load balancing.
- 그래서 메모 14번 "event마다 function을 CPU 위에 얹어 실행" = 코드가 스레드를 요청하면 OS가 그걸 노는 코어에 배치하는 그림. 같은 코어에 몰 이유가 없으니 빈 코어로 분산된다.

> 검증: [GeeksforGeeks — Thread Scheduling](https://www.geeksforgeeks.org/thread-scheduling/), [ScienceDirect — Thread Schedule](https://www.sciencedirect.com/topics/computer-science/thread-schedule) — 일치

---

### 7. 보충: IPC (프로세스 간 통신)

**IPC = Inter-Process Communication.** 프로세스들은 메모리가 **분리**돼 있어서(섹션 2) 그냥 변수로 데이터를 못 주고받는다. 그래서 별도 통로가 필요한데 그게 IPC.
(반대로 스레드는 메모리를 공유하니 IPC가 필요 없다 — 대신 lock으로 동기화.)

| 방식 | 특징 |
|------|------|
| **파이프(Pipe)** | 단방향 바이트 스트림. 익명 파이프는 부모-자식용, FIFO(named pipe)는 무관한 프로세스도 가능 |
| **메시지 큐(Message Queue)** | 메시지를 큐에 넣고 뺌. 비동기 — 양쪽이 동시에 안 떠 있어도 됨 |
| **공유 메모리(Shared Memory)** | 같은 물리 메모리를 여러 프로세스 주소공간에 매핑. **복사가 없어 가장 빠름.** 단 동기화는 별도(세마포어) |
| **소켓(Socket)** | 양방향 채널. 네트워크 너머도 가능(Unix domain socket은 한 호스트 내 빠른 버전) |
| **세마포어(Semaphore)** | 데이터 전달용이 아니라 **자원 접근 조율(동기화)**용. 공유 메모리 보호에 같이 씀 |

> ROS2의 노드 간 통신(DDS)도 본질적으로 IPC의 한 형태(주로 소켓/공유메모리 기반). 노드 = 보통 별개 프로세스.

> 검증: [GeeksforGeeks — IPC](https://www.geeksforgeeks.org/operating-systems/inter-process-communication-ipc/), [Medium — Understanding IPC](https://mohitdtumce.medium.com/understanding-interprocess-communication-ipc-pipes-message-queues-shared-memory-rpc-902f918fba58) — 일치

---

### 8. 보충: 데드락에 대처하는 4가지 방법

데드락은 발생하면 시스템이 멈추므로, OS/프로그램은 아래 중 하나로 대응한다.

| 방법 | 내용 | 비용 |
|------|------|------|
| **예방(Prevention)** | 4조건(섹션 5) 중 하나를 **구조적으로 불가능**하게 만듦. 예: lock을 항상 같은 순서로만 잡아 순환 대기 차단 | 설계 제약이 큼 |
| **회피(Avoidance)** | 자원 할당 전에 "이걸 주면 안전한가?"를 매번 계산. **뱅커스 알고리즘**이 대표 — 각 프로세스의 최대 요구량을 미리 알아야 하고, 안전 상태(safe state)로 남을 때만 할당 | 요청마다 계산 부담 |
| **탐지 후 복구(Detection & Recovery)** | 막지 않고 그냥 두다가, 주기적으로 자원 그래프에서 **사이클(순환)을 탐지** → 발견되면 프로세스 강제 종료/롤백 | 평소엔 가볍지만 터지면 비쌈 |
| **무시(Ostrich)** | 드물면 그냥 무시(재부팅). 일반 OS가 현실적으로 자주 택하는 길 | 거의 0 / 가끔 큰 사고 |

- 실무에서 멀티스레드 코드는 대부분 **예방(lock 순서 고정)**으로 푼다. 뱅커스 알고리즘은 이론·교과서용 비중이 큼.

> 검증: [TutorialsPoint — Deadlock Handling](https://www.tutorialspoint.com/operating_system/os_deadlock_handling.htm), [GeeksforGeeks — Detection & Recovery](https://www.geeksforgeeks.org/operating-systems/deadlock-detection-recovery/), [TutorialsPoint — Banker's Algorithm](https://www.tutorialspoint.com/operating_system/os_deadlock_avoidance_bankers_algorithm.htm) — 일치

#### lock 순서 고정은 "코드에서, 개발자가" 한다 (★ 자주 하는 오해)

- **OS가 주는 것**: lock 도구 자체(mutex). "잠가라/풀어라" 기능만.
- **개발자가 코드에 쓰는 것**: 어떤 lock을 **어떤 순서로** 잡을지. → OS는 순서에 관여 안 함. 그래서 데드락은 보통 OS 버그가 아니라 **내 코드의 버그**.

```python
import threading
lock_A = threading.Lock()
lock_B = threading.Lock()

# ❌ 데드락: 두 스레드가 lock을 잡는 순서가 엇갈림
def thread1():
    lock_A.acquire()   # A 먼저
    lock_B.acquire()   # 그다음 B
    ...
def thread2():
    lock_B.acquire()   # B 먼저  ← 순서 반대!
    lock_A.acquire()   # 그다음 A → 서로 상대 lock 대기 = 멈춤
    ...

# ✅ 예방: 모든 스레드가 "항상 A → B" 같은 순서로만 잡음
def thread1():
    lock_A.acquire(); lock_B.acquire()   # A → B
    ...
def thread2():
    lock_A.acquire(); lock_B.acquire()   # 여기도 A → B (통일)
    ...
```

- "A를 쥔 채 B 대기"와 "B를 쥔 채 A 대기"가 **동시에 생길 수 없게** 되어 ④ 순환 대기가 원천 차단됨.
- lock이 많으면 객체에 번호(`id`)를 매겨 **항상 작은 번호부터** 잡는 헬퍼로 순서를 강제하기도 함.
- Python은 `with lock_A, lock_B:` (context manager)로 쓰면 `release()` 누락 실수까지 방지.

> 검증: [Python docs — threading](https://docs.python.org/3/library/threading.html), [GeeksforGeeks — Locking without Deadlocks](https://www.geeksforgeeks.org/python-locking-without-deadlocks/) — 일치

---

## 다른 개념과의 연결
- [[thread_inline_vs_threaded]] — 이 문서가 "하드웨어(코어)" 레벨이라면, 그쪽은 "소프트웨어 흐름(스레드)" 레벨. 코어 위에 스레드가 올라간다.
- ROS2 Executor(SingleThreaded / MultiThreaded), 콜백 그룹 → 어떤 콜백을 어느 스레드에 올릴지 결정하는 부분. 메모 14번 "event마다 function을 CPU에 얹는다"가 이것.

## 의문점 / 나중에 파고들 것
- Python GIL이 ROS2 MultiThreadedExecutor에서 실제로 어떻게 동작하나? (CPU-bound vs I/O-bound 콜백 차이)
- 슈퍼컴퓨팅의 "분산 메모리 병렬(MPI)" vs "공유 메모리 병렬(OpenMP)" 구분
