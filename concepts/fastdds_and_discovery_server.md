# FastDDS와 Discovery Server

## 한 줄 요약

ROS2는 DDS 표준 위에서 동작하고, FastDDS는 그 구현체 중 하나. Discovery Server는 노드 탐색 트래픽을 줄이는 중앙 등록 방식.

---

## DDS란

여러 벤더가 로봇 미들웨어를 각자 만들면 인터페이스가 달라서 같이 못 씀. 그래서 OMG(표준화 기구)가 **DDS(Data Distribution Service)** 라는 표준 규격을 정의함. "퍼블리셔/서브스크라이버가 어떻게 데이터를 주고받을지"를 규정한 명세서.

```
표준 규격 (DDS)
    └── 구현체들
         ├── FastDDS    (eProsima)       ← ROS2 Humble 기본값
         ├── CycloneDDS (Eclipse)
         ├── Connext DDS (RTI, 상용)
         └── GurumDDS   (구루네트웍스, 국내)
```

FastDDS = eProsima가 DDS 표준을 구현한 버전. ROS2 Humble에서 별도 설정 없으면 자동으로 사용.

> 검증: [ROS2 Middleware Vendors 공식 문서](https://docs.ros.org/en/humble/Concepts/Intermediate/About-Different-Middleware-Vendors.html) — FastDDS가 default, binary 배포판에 포함 확인

---

## RMW 추상화 레이어

ROS2 코드는 DDS 구현체가 뭔지 신경 쓰지 않음. **RMW(ROS Middleware interface)** 레이어가 중간에서 스위칭.

```
[ROS2 노드 코드]
      ↓
  [RMW 레이어]  ← 어떤 DDS 쓸지 여기서 결정
      ↓
  [FastDDS / CycloneDDS / ...]
```

`RMW_IMPLEMENTATION=rmw_fastrtps_cpp` 환경변수가 "RMW 레이어에 FastDDS 써라"고 지시.

---

## Discovery Server / Client / Super Client 역할

| 역할 | 동작 | 주요 사용처 |
|------|------|-------------|
| **Server** | 모든 클라이언트의 토픽·엔드포인트 정보를 수집·보관, 관련 노드끼리만 연결 정보 전달 | 독립 프로세스로 실행 (`fastdds discovery`) |
| **Client** | 자신이 쓰는/읽는 토픽만 서버에 등록, 자기와 관련된 노드 정보만 수신 | 일반 ROS2 노드 |
| **Super Client** | 서버에 연결하되 네트워크 전체 노드 정보를 전부 수신 | `ros2 topic list` 등 CLI 도구, daemon |

> `ROS_SUPER_CLIENT=true`로 설정하면 Super Client 모드. PC에서 `ros2 topic list`에 모든 토픽이 표시되려면 필요.

> 검증: [ROS2 Discovery Server 공식 문서](https://docs.ros.org/en/humble/Tutorials/Advanced/Discovery-Server/Discovery-Server.html) — "a kind of Client that connects to a Server, from which it receives all the available discovery information" 확인

---

## fastdds discovery 명령

```bash
fastdds discovery -i <ID> -l <IP> -p <PORT>
```

| 플래그 | 의미 | 기본값 |
|--------|------|--------|
| `-i` | Server ID (0-based). `ROS_DISCOVERY_SERVER`의 세미콜론 위치와 대응 | 필수 |
| `-l` | 수신 대기 IP | `0.0.0.0` (모든 인터페이스) |
| `-p` | 수신 대기 UDP 포트 | `11811` |
| `-b` | 백업 파일 생성 (서버 재시작 시 상태 복원) | 없음 |

```bash
# ID 0, 기본값으로 실행 (가장 흔한 형태)
fastdds discovery -i 0

# ID 1, 특정 IP·포트 지정
fastdds discovery -i 1 -l 127.0.0.1 -p 14520
```

`ROS_DISCOVERY_SERVER`와 `-i` 값의 대응:

```
fastdds discovery -i 0  →  ROS_DISCOVERY_SERVER="IP:11811"       (세미콜론 없음)
fastdds discovery -i 1  →  ROS_DISCOVERY_SERVER=";IP:11811"      (세미콜론 1개)
fastdds discovery -i 2  →  ROS_DISCOVERY_SERVER=";;IP:11811"     (세미콜론 2개)
```

> 검증: `fastdds discovery --help` (로컬 실행) — `-i`는 "zero based server position in ROS_DISCOVERY_SERVER" 확인

---

## ros2 daemon

ROS2 CLI 도구(`ros2 node list`, `ros2 topic list` 등)가 빠르게 응답할 수 있도록 ROS 그래프 정보를 캐싱하는 **백그라운드 프로세스**.

```bash
ros2 daemon start   # 수동 시작 (CLI 명령 실행 시 자동 시작됨)
ros2 daemon stop    # 중지
ros2 daemon status  # 상태 확인
```

**터미널 간 공유 여부**: daemon은 **터미널이 아닌 OS 프로세스 단위**로 동작.  
같은 `ROS_DOMAIN_ID`를 쓰는 터미널은 단일 daemon 프로세스를 공유한다.

```
터미널 A ──┐
터미널 B ──┼──→  [ros2-daemon PID XXXX, domain=N]
터미널 C ──┘
```

→ 어느 터미널에서 `ros2 daemon stop`을 실행해도 **같은 Domain ID를 쓰는 모든 터미널에 영향**.  
→ `ROS_DOMAIN_ID`가 다르면 별도 daemon 프로세스가 생성되어 서로 독립.  
→ stop 후 CLI 명령을 실행하면 daemon이 **자동 재시작**됨.

> 검증: `ps aux | grep ros2` (로컬 실행) — `python3 ros2cli.daemon.daemonize --ros-domain-id 8` 단일 프로세스 확인

---

## Simple Discovery vs Discovery Server

DDS에서 노드들이 서로를 찾는 과정을 **discovery**라고 함.

### Simple Discovery (기본값)

```
노드A 켜짐 → 네트워크 전체 브로드캐스트 → "나 켜졌어!"
           → 모든 노드가 수신 → 서로 정보 교환
```

로봇 6대 + PC 12대 환경에서 하나가 켜질 때마다 18개 전부에 패킷이 날아감. 토픽도 마구 퍼져서 트래픽 폭발.

### Discovery Server

```
노드A 켜짐 → Discovery Server에만 등록 → "나 켜졌어"
           → Server가 "TB1 관련 토픽 구독하는 애 있어?" 필터링
           → 필요한 노드끼리만 연결
```

> 검증: [ROS2 Discovery Server 공식 문서](https://docs.ros.org/en/humble/Tutorials/Advanced/Discovery-Server/Discovery-Server.html) — "nodes will only receive topic's discovery data if it has a writer or a reader for that topic" 확인

---

## 라우팅이란

네트워크에서 패킷을 목적지까지 **어느 경로로 보낼지 결정하는 것**. 집 공유기가 "이 패킷은 인터넷으로, 저 패킷은 프린터로" 분기시키는 게 라우팅.

강의장 AP가 "라우팅보다 격리 역할"인 이유: 원래 AP는 서브넷 간 패킷 전달(라우팅)도 할 수 있지만, 강의장에서는 그보다 **AP별로 TB 그룹을 물리적으로 분리**하는 게 목적.

```
AP1: TB1, TB2   ←(섞이지 않음)→   AP2: TB3, TB4
```

---

## 다른 개념 파일과의 연결

- FastDDS vs CycloneDDS 선택 이유 (RPi4 성능 한계) → [turtlebot4_lecture_5th_updates.md](turtlebot4_lecture_5th_updates.md)
- 강의장 네트워크 구성 (방식 1 vs 방식 2) → [classroom_multirobot_network_comparison.md](classroom_multirobot_network_comparison.md)
- Discovery Server ID / 세미콜론 설정 → [turtlebot4_single_robot_network.md](turtlebot4_single_robot_network.md)
