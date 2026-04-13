# 강의장 멀티로봇 네트워크 구성 방식 비교

## 한 줄 요약

AP 1개당 TurtleBot 2대 + PC 4대로 구성되는 멀티로봇 환경에서, Discovery Server를 각 TurtleBot에 두는 방식(방식 1)과 별도 Server PC에 집중시키는 방식(방식 2)의 차이.

---

## 전제 조건

- 강의장 TurtleBot 총 6대 → AP 3개 운영 (AP당 TurtleBot 2대)
- 2대씩 멀티로봇 팀 구성
- FastDDS Discovery Server 사용 (Simple Discovery 브로드캐스트 방지)
- AP의 역할: 라우팅보다 **TurtleBot 그룹 격리** 목적

| AP | TurtleBot |
|----|-----------|
| AP1 | TB1, TB2 |
| AP2 | TB3, TB4 |
| AP3 | TB5, TB6 |

---

## 방식 1 — TurtleBot Onboard Discovery Server (Server PC 없음)

> **TurtleBot4 공식 문서 기준 표준 방식**
> 출처: [TurtleBot4 User Manual - Discovery Server](https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html)

### 구조

각 TurtleBot의 라즈베리파이가 Onboard Discovery Server 역할. User PC는 모든 로봇의 Onboard Server에 Super Client로 연결.

```
                    [AP1]
                   /     \
          [TurtleBot1]   [TurtleBot2]
          (Onboard DS,   (Onboard DS,
            ID=0)          ID=1)
               ↑               ↑
               └───────┬───────┘
                   [User PC]
         ROS_DISCOVERY_SERVER=
         "TB1_IP:11811;TB2_IP:11811"
            ID=0          ID=1
```

로봇끼리 직접 통신하지 않음. User PC가 모든 서버에 Super Client로 연결해서 전체 토픽 파악.

### 공식 2로봇 설정 예시

| | Onboard Server ID | Offboard IP | 비고 |
|--|--|--|--|
| Robot1 | 0 | **비워둠** | Offboard IP 비우면 Offboard 설정 전체 무시 |
| Robot2 | 1 | **비워둠** | Offboard IP 비우면 Offboard 설정 전체 무시 |

```
User PC ROS_DISCOVERY_SERVER:
"<Robot1_IP>:11811;<Robot2_IP>:11811"
  ↑ ID=0              ↑ ID=1
```

### 설정 포인트

```bash
# Robot1 TUI:
#   Onboard Server ID = 0
#   Offboard IP = 비워둠  ← Offboard 설정 전체 무시됨

# Robot2 TUI:
#   Onboard Server ID = 1
#   Offboard IP = 비워둠

# User PC setup.bash:
export ROS_DOMAIN_ID=<로봇과 동일>
export ROS_DISCOVERY_SERVER="<TB1_IP>:11811;<TB2_IP>:11811"
#                              ID=0             ID=1
export ROS_SUPER_CLIENT=True
```

Onboard Server ID가 `ROS_DISCOVERY_SERVER`의 세미콜론 위치(=ID)와 일치해야 한다.

| Onboard Server ID | ROS_DISCOVERY_SERVER 형식 |
|---|---|
| 0 | `"IP:11811"` (세미콜론 없음) |
| 1 | `";IP:11811"` (세미콜론 1개) |
| 2 | `";;IP:11811"` (세미콜론 2개) |

### 특징

| 항목 | 내용 |
|------|------|
| Discovery Server 위치 | 각 TurtleBot 라즈베리파이 |
| 트래픽 집중점 | 각 TurtleBot (DS 역할 + 실제 센서/제어 처리 동시 수행) |
| 구성 복잡도 | 낮음 — 추가 장비 불필요 |
| nav2 실행 시 | 실행한 PC의 토픽이 TB → 모든 구독 PC로 퍼짐 → TB에 트래픽 누적 |
| TurtleBot 간 통신 | 같은 AP 내라도 DS가 분리되어 있어 추가 브리지 설정 필요 |

---

## 방식 2 — Server PC 중앙 Discovery Server

### 구조

별도 Server PC를 중앙 Discovery Server로 운영. AP는 TurtleBot에만 IP 부여. PC는 AP 미연결, Server PC를 통해 TB와 통신.

```
  [ IP 부여 ]

       [AP1]
      /     \
   [TB1]   [TB2]


  [ Discovery Server 연결 ]

        [Server PC (Central DS)]
       /    \      /   |   \   \
    [TB1] [TB2] [PC1][PC2][PC3][PC4]

  ROS_DISCOVERY_SERVER:
    TB1, TB2, PC1~PC4 모두 → Server PC IP (동일)
```

### 토픽 흐름

```
  [PC1] ──publish──► [Server PC (DS)] ──relay──► [TB1] [TB2] [PC2~4]

  nav2 실행 예시 (PC3에서 launch):

  [PC3] ──nav2 토픽──► [Server PC (DS)] ──► [TB1] (명령 수신)
                                        ──► [TB2] (명령 수신)
  [TB1] ──센서/상태──► [Server PC (DS)] ──► [PC1] [PC2] [PC4]
  [TB2] ──센서/상태──► [Server PC (DS)] ──► [PC1] [PC2] [PC4]

  트래픽 누적: Server PC에만 집중
```

### 설정 포인트

```bash
# PC1~PC4, TB1, TB2 모두 동일하게
export ROS_DOMAIN_ID=<그룹 공통 ID>
export ROS_DISCOVERY_SERVER="<ServerPC_IP>:11811"   # 세미콜론 없음 = ID 0 위치

# Server PC 자체 (Discovery Server 실행)
fastdds discovery -i 0 -p 11811                     # -i 0 = ID 0번 서버
```

**Offboard Server ID와 세미콜론의 관계:**  
`fastdds discovery -i 0`(서버)와 `ROS_DISCOVERY_SERVER="IP:11811"`(세미콜론 없음, 클라이언트)는 같은 기능이 아니라 **서로 대응해야 하는 쌍**이다.

| 서버 `-i` 값 | 클라이언트 세미콜론 | 연결 |
|---|---|---|
| `-i 0` | `"IP:11811"` (없음) | O |
| `-i 0` | `";IP:11811"` (1개) | X |
| `-i 1` | `";IP:11811"` (1개) | O |

### 특징

| 항목 | 내용 |
|------|------|
| Discovery Server 위치 | 별도 Server PC |
| 트래픽 집중점 | Server PC 1대 (TurtleBot은 제어/센서 처리에만 집중) |
| 구성 복잡도 | 중간 — Server PC 추가, 단일 설정값으로 통일 가능 |
| nav2 실행 시 | 어느 PC에서 실행해도 트래픽은 Server PC에만 쌓임 |
| TurtleBot 간 통신 | 동일 DS 공유 → TB1↔TB2 직접 토픽 교환 가능 |
| Server PC 장애 | 단일 장애점(SPOF) — Server PC 다운 시 전체 통신 중단 |

---

## 방식 비교 요약

```
                  방식 1 (Onboard DS)           방식 2 (Server PC DS)
                  ──────────────────────         ──────────────────────
추가 장비          없음                           Server PC 필요
트래픽 집중        TurtleBot 라즈베리파이          Server PC
TurtleBot 부하     높음 (DS + 제어 동시)          낮음 (제어만)
PC간 통신 경로     PC → TB(DS) → PC              PC → ServerPC(DS) → PC
멀티로봇 토픽 공유  DS 분리 → 설정 추가 필요       DS 공유 → 기본 지원
구성 단순성        단순 (장비 적음)               중간 (설정 일관성 높음)
SPOF               없음 (DS 분산)                있음 (Server PC)
```

---

## 전체 강의장 그림 (방식 2 기준)

```
       [AP1]              [AP2]              [AP3]
      /     \            /     \            /     \
   [TB1]  [TB2]       [TB3]  [TB4]       [TB5]  [TB6]

  [Server PC1 (DS)]  [Server PC2 (DS)]  [Server PC3 (DS)]
   /  \   / | \ \     /  \   / | \ \     /  \   / | \ \
 TB1 TB2 PC1~PC4    TB3 TB4 PC5~PC8    TB5 TB6 PC9~PC12

  AP 경계 = 토픽 격리 경계 (AP1 ↔ AP2 ↔ AP3 는 서로 통신 안 함)
```

---

## 다른 개념 파일과의 연결

- Discovery Server 기본 개념 → [turtlebot4_single_robot_network.md](turtlebot4_single_robot_network.md)
- Discovery Server ID / 세미콜론 위치 → [turtlebot4_single_robot_network.md](turtlebot4_single_robot_network.md)
- TurtleBot4 TUI Offboard Server IP 항목 → 방식 2 Server PC IP를 여기에 입력
- FastDDS vs CycloneDDS 선택 → [turtlebot4_lecture_5th_updates.md](turtlebot4_lecture_5th_updates.md)

---

## Onboard / Offboard 개념 정리

| 항목 | 의미 |
|------|------|
| Onboard Server | 이 로봇(Raspberry Pi)에서 실행되는 Discovery Server |
| Offboard Server | 다른 머신(User PC 등)에서 실행되는 외부 Discovery Server |
| Offboard IP | 비워두면 Offboard 설정 전체 무시 — Onboard Server만 사용 |

**싱글로봇**: Offboard IP 비워둠 → Onboard Server만 동작, User PC가 이 서버에 연결

**멀티로봇 (방식 1, 표준)**: 각 로봇 Offboard IP 비워둠 → 각자 Onboard Server만 동작, User PC가 모든 Onboard Server에 연결

**멀티로봇 (방식 2, 비표준)**: Offboard IP 설정 시 Onboard Server가 Offboard Server에 클라이언트로 접속. 로봇이 서버이면서 동시에 클라이언트 역할.

> 방식 2는 TurtleBot4 공식 문서에서 "초보자에게 비추천 (네트워크 과부하)" 경고 있음

---

## 의문점 / 나중에 파고들 것

- 방식 2에서 Server PC 장애 대비 이중화 가능 여부
- 방식 1에서 TB1↔TB2 멀티로봇 토픽 공유를 위한 브리지 구성 방법
- AP 경계를 넘는 6대 전체 통합 운영 시나리오 (필요한지 여부 포함)
