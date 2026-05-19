# ROS2 Gazebo 시뮬레이션 DDS 설정 — Discovery Server vs Localhost 분리

## 한 줄 요약

실물 TurtleBot4용으로 설정된 PC에서 Gazebo 시뮬레이션을 돌리려면, Discovery Server 환경변수를 unset하고 `ROS_LOCALHOST_ONLY=1`로 격리해야 한다.

---

## 배경 — 왜 충돌하는가

TurtleBot4 실물 연결 환경에서 PC의 `~/.bashrc`(또는 `/etc/turtlebot4_discovery/setup.bash`)에는 다음이 설정된다:

```bash
export ROS_DISCOVERY_SERVER="<ROBOT_IP>:11811;"
export ROS_SUPER_CLIENT=True
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

이 상태로 Gazebo 시뮬레이션을 실행하면 FastDDS가 **Discovery Server 모드**로 동작한다. 시뮬레이터 노드들이 `<ROBOT_IP>:11811`에 존재하지 않는 Discovery Server에 연결을 시도하다가 타임아웃→재시도를 반복하며 다음 증상이 나타난다.

### 증상

| 증상 | 원인 |
|------|------|
| `ros2 topic list` hang (응답 없음) | ROS daemon이 존재하지 않는 DS에 연결 시도 중 |
| Gazebo 노드들이 서로를 못 찾음 | controller_manager가 spawner를 discovery 못 해 lock 실패 |
| `ros2_control` spawner 타임아웃 | 같은 PC 내 노드끼리 DS 경유 탐색 → DS 없으면 불가 |
| 로봇 spawn 실패 반복 | 위 원인의 연쇄 결과 |

---

## 핵심 개념

### 1. Discovery Server 모드 — 중앙 서버 등록 방식

```
노드 A 켜짐 ──► Discovery Server(IP:11811)에 endpoint 등록
              ◄── "B 노드도 같은 토픽 써, 연결해" 라고 서버가 알려줌
              ──► B와 직접 연결 (데이터는 DS를 거치지 않음)
```

- FastDDS가 중앙 서버에 **모든 endpoint를 등록**한다.
- 서버가 없으면 discovery 자체가 불가 → 노드들이 서로를 볼 수 없다.
- `ROS_DISCOVERY_SERVER="<ROBOT_IP>:11811"` 설정 시 그 IP의 서버로 연결을 시도한다.
- 로봇 보드(Raspberry Pi)에 FastDDS Discovery Server가 실행 중이어야만 동작한다.

> 검증: [FastDDS Discovery Server 공식 문서](https://fast-dds.docs.eprosima.com/en/latest/fastdds/discovery/discovery_server.html) — "all Participants must connect to a server in the network" 확인

### 2. Simple Discovery 모드 — 직접 peer 탐색

```
노드 A 켜짐 ──► 멀티캐스트 브로드캐스트 "나 켜졌어!"
              ◄── 같은 네트워크의 모든 노드가 수신하여 직접 연결
```

- 별도 서버 없이 멀티캐스트/유니캐스트로 **직접 peer를 탐색**한다.
- 같은 PC 내 노드끼리는 loopback 또는 로컬 멀티캐스트로 탐색 가능 → 시뮬용으로 적합.
- 단, `ROS_DISCOVERY_SERVER`가 설정되어 있으면 Simple Discovery로 전환되지 않는다.

### 3. `ROS_LOCALHOST_ONLY=1`

- FastDDS 통신을 `127.0.0.1`(loopback) 인터페이스로만 제한한다.
- 같은 PC 내 노드끼리만 통신하므로 외부 네트워크 트래픽이 완전히 차단된다.
- 시뮬레이션 세션에서 실물 로봇 토픽이 섞이지 않도록 격리하는 핵심 설정.

> 검증: [ROS2 환경변수 공식 문서](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Domain-ID.html) — `ROS_LOCALHOST_ONLY` → DDS를 localhost 인터페이스로만 제한 확인

### 4. `ROS_SUPER_CLIENT=True`

- Discovery Server 전용 클라이언트 모드.
- 서버에 연결하여 **네트워크 전체의 discovery 정보를 전부 수신**한다 (일반 Client는 자기 토픽 관련 정보만 수신).
- `ros2 topic list` 같은 CLI 도구가 모든 토픽을 표시하려면 필요하다.
- **서버(로봇)가 없으면 아무것도 볼 수 없다** — 시뮬에서 이 설정이 남아 있으면 CLI 도구가 hang하는 직접 원인.

> 검증: [ROS2 Discovery Server 공식 문서](https://docs.ros.org/en/humble/Tutorials/Advanced/Discovery-Server/Discovery-Server.html) — "Super Client is a kind of Client that connects to a Server, from which it receives all the available discovery information" 확인

---

## 해결 방법

### 방법 A — `~/.bashrc`에 unset 추가 (세션 전역 적용)

`source /etc/turtlebot4_discovery/setup.bash` 바로 다음 줄에 추가:

```bash
# ~/.bashrc 에서 setup.bash source 이후에 추가
source /etc/turtlebot4_discovery/setup.bash
unset ROS_DISCOVERY_SERVER        # 시뮬용: DS(실물 로봇 전용) 비활성화
export ROS_LOCALHOST_ONLY=1       # DDS를 127.0.0.1로 제한
```

**주의**: 이 방법은 **모든 터미널 세션**에 적용된다. 이후 실물 로봇에 연결하려면 해당 터미널에서 수동으로 `export ROS_DISCOVERY_SERVER="<ROBOT_IP>:11811"` 해야 한다.

### 방법 B — launch 명령 실행 시 env로 격리 (권장)

실물 로봇 환경변수를 건드리지 않고 시뮬 실행 시에만 오버라이드:

```bash
env -u ROS_DISCOVERY_SERVER \
    -u ROS_SUPER_CLIENT \
    -u ROS_AUTOMATIC_DISCOVERY_RANGE \
    ROS_LOCALHOST_ONLY=1 \
    ROS_DOMAIN_ID=0 \
    RMW_IMPLEMENTATION=rmw_fastrtps_cpp \
    bash -c 'source /opt/ros/jazzy/setup.bash && ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py'
```

`-u` 플래그는 해당 환경변수를 서브셸에서 unset한다.

---

## 진단 흐름

```
[증상] ros2 topic list가 응답 없음 / Gazebo 노드 spawn 실패
  │
  ├─► env | grep ROS_DISCOVERY_SERVER 로 설정 확인
  │         값이 있으면 → Discovery Server 모드가 활성화된 상태
  │
  ├─► ping <ROBOT_IP> 로 서버 접근 가능 여부 확인
  │         응답 없으면 → DS에 연결 불가 → 모든 discovery hang
  │
  └─► 해결: unset ROS_DISCOVERY_SERVER && export ROS_LOCALHOST_ONLY=1
            ros2 daemon stop && ros2 daemon start  (캐시 초기화)
            다시 ros2 topic list 실행
```

---

## 실물 로봇 세션과 시뮬 세션을 같이 쓸 때 주의사항

두 모드는 **서로 통신이 불가**하다. 같은 PC에서 동시에 쓰려면 반드시 격리해야 한다.

| 항목 | 실물 로봇 세션 | 시뮬 세션 |
|------|--------------|-----------|
| `ROS_DISCOVERY_SERVER` | `<ROBOT_IP>:11811` | unset |
| `ROS_LOCALHOST_ONLY` | unset (또는 0) | 1 |
| `ROS_DOMAIN_ID` | 로봇과 동일한 값 | 독립된 값 (예: 0) |
| DDS discovery 방식 | Discovery Server | Simple Discovery |

**두 모드가 통신 불가인 이유**: Discovery Server 모드와 Simple Discovery 모드는 DDS 레이어에서 서로 다른 discovery 프로토콜을 사용한다. `ROS_DOMAIN_ID`가 같아도 discovery 프로토콜이 다르면 서로의 노드를 볼 수 없다.

**권장 운용 방식**:

- 터미널을 역할별로 분리한다. 실물 로봇용 터미널과 시뮬용 터미널을 따로 열고, 시뮬용 터미널에서는 launch 전에 `unset ROS_DISCOVERY_SERVER && export ROS_LOCALHOST_ONLY=1 && ros2 daemon stop` 을 실행한다.
- 또는 방법 B처럼 `env -u` 를 사용해 launch 명령 단위로 격리한다.

---

## 연결된 개념 파일

- Discovery Server 원리, Super Client, RMW 레이어 → [fastdds_and_discovery_server.md](fastdds_and_discovery_server.md)
- Humble vs Jazzy FastDDS 버전 차이 → [humble_vs_jazzy_fastdds.md](humble_vs_jazzy_fastdds.md)
- 실물 로봇 네트워크 설정 전체 (setup.bash, TUI) → [turtlebot4_single_robot_network.md](turtlebot4_single_robot_network.md)
- FastDDS 멀티캐스트 peer discovery 실패 에러 (직전 증상) → [../network/fastdds_local_discovery_failure.md](../network/fastdds_local_discovery_failure.md)
