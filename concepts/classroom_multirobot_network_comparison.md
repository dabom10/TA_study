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

### 구조

각 TurtleBot의 라즈베리파이가 Onboard Discovery Server 역할. PC는 자신이 제어하는 TurtleBot의 Discovery Server에 직접 연결.

```
┌──────────────────────────────── AP1 영역 ────────────────────────────────┐
│                                                                           │
│   ┌─────────────────────────┐     ┌─────────────────────────┐            │
│   │   TurtleBot1            │     │   TurtleBot2            │            │
│   │   (Onboard DS #ID_A)    │     │   (Onboard DS #ID_B)    │            │
│   └────────────┬────────────┘     └────────────┬────────────┘            │
│                │                               │                         │
│        ┌───────┴───────┐               ┌───────┴───────┐                 │
│      [PC1]           [PC2]           [PC3]           [PC4]               │
│   ROS_DISCOVERY    ROS_DISCOVERY  ROS_DISCOVERY   ROS_DISCOVERY          │
│   SERVER=TB1_IP    SERVER=TB1_IP  SERVER=TB2_IP   SERVER=TB2_IP          │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

  [AP2 영역] TB3(DS), TB4(DS) + PC5~PC8  (동일 구조)
  [AP3 영역] TB5(DS), TB6(DS) + PC9~PC12 (동일 구조)
```

### PC 간 통신 경로

```
PC1 ──publish──► TurtleBot1 (DS) ──relay──► PC2 (subscribe)

토픽 흐름: PC1 → [TB1 Discovery Server] → PC2
           PC1이 TB1의 DS에 등록된 토픽을 발행하면,
           동일 DS에 연결된 PC2가 구독
```

### 설정 포인트

```bash
# PC1, PC2 (TurtleBot1 팀)
export ROS_DOMAIN_ID=<TB1과 동일>
export ROS_DISCOVERY_SERVER="<TB1_IP>:11811"   # Onboard ID=0 예시

# PC3, PC4 (TurtleBot2 팀)
export ROS_DOMAIN_ID=<TB2와 동일>
export ROS_DISCOVERY_SERVER="<TB2_IP>:11811"   # Onboard ID=0 예시
```

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

별도 Server PC를 AP 그룹 내 중앙 Discovery Server로 운영. TurtleBot 2대 + PC 4대 모두 Server PC를 바라봄.

```
┌──────────────────────────────── AP1 영역 ────────────────────────────────┐
│                                                                           │
│                        ┌─────────────────┐                               │
│                        │   Server PC     │                               │
│                        │ (Central DS)    │                               │
│                        └────────┬────────┘                               │
│              ┌──────────────────┼──────────────────┐                     │
│              │         ┌────────┴────────┐          │                     │
│              │         │                │          │                     │
│        ┌─────┴─────┐  [TB1]           [TB2]  ┌────┴──────┐              │
│      [PC1]       [PC2]                      [PC3]      [PC4]             │
│                                                                           │
│   모든 클라이언트의 ROS_DISCOVERY_SERVER = <ServerPC_IP>:11811            │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

  [AP2 영역] Server PC2 + TB3, TB4 + PC5~PC8  (동일 구조)
  [AP3 영역] Server PC3 + TB5, TB6 + PC9~PC12 (동일 구조)
```

### 토픽 흐름

```
PC1 ──publish──► Server PC (Central DS) ──relay──► TB1, TB2, PC2~PC4

nav2 실행 예시:
PC3에서 nav2 launch
  → PC3 토픽 → Server PC
  → Server PC → TB1, TB2 (명령 수신)
  → TB1, TB2 → Server PC (센서/상태 토픽)
  → Server PC → PC1, PC2, PC4 (구독자에게 전달)

트래픽이 Server PC에만 누적됨
```

### 설정 포인트

```bash
# PC1~PC4, TB1, TB2 모두 동일하게
export ROS_DOMAIN_ID=<그룹 공통 ID>
export ROS_DISCOVERY_SERVER="<ServerPC_IP>:11811"

# Server PC 자체 (Discovery Server 실행)
fastdds discovery -i 0 -p 11811
```

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
강의장 전체

  ┌──── AP1 영역 ────┐    ┌──── AP2 영역 ────┐    ┌──── AP3 영역 ────┐
  │  [Server PC1]   │    │  [Server PC2]   │    │  [Server PC3]   │
  │    DS(Central)  │    │    DS(Central)  │    │    DS(Central)  │
  │   /            \│    │   /            \│    │   /            \│
  │ [TB1]  [TB2]   │    │ [TB3]  [TB4]   │    │ [TB5]  [TB6]   │
  │[PC1~4]         │    │[PC5~8]         │    │[PC9~12]        │
  └─────────────────┘    └─────────────────┘    └─────────────────┘
         AP1                    AP2                    AP3
    (격리된 그룹)           (격리된 그룹)           (격리된 그룹)

  AP 경계 = 토픽 격리 경계
  AP 내부 = Server PC가 단일 DS로 통합 관리
```

---

## 다른 개념 파일과의 연결

- Discovery Server 기본 개념 → [turtlebot4_single_robot_network.md](turtlebot4_single_robot_network.md)
- Discovery Server ID / 세미콜론 위치 → [turtlebot4_single_robot_network.md](turtlebot4_single_robot_network.md)
- TurtleBot4 TUI Offboard Server IP 항목 → 방식 2 Server PC IP를 여기에 입력
- FastDDS vs CycloneDDS 선택 → [turtlebot4_lecture_5th_updates.md](turtlebot4_lecture_5th_updates.md)

---

## 의문점 / 나중에 파고들 것

- Server PC와 TurtleBot 간 Offboard/Onboard DS ID 매핑 방법 (TUI Offboard Server ID 설정)
- 방식 2에서 Server PC 장애 대비 이중화 가능 여부
- 방식 1에서 TB1↔TB2 멀티로봇 토픽 공유를 위한 브리지 구성 방법
- AP 경계를 넘는 6대 전체 통합 운영 시나리오 (필요한지 여부 포함)
