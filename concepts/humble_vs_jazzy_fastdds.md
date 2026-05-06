# Humble vs Jazzy — FastDDS 중심 비교

## 한 줄 요약

Jazzy는 FastDDS 버전을 올리고 Discovery Server v2를 완성시키면서, TurtleBot4 아키텍처도 Create3를 WiFi에서 분리하는 방향으로 단순화했다.

---

## FastDDS 버전 변화

| 항목 | Humble | Jazzy |
|------|--------|-------|
| FastDDS 버전 | 2.6.x | 2.14.x |
| 기본 RMW | `rmw_fastrtps_cpp` | `rmw_fastrtps_cpp` (동일) |
| Discovery Server | v2 초기 | v2 완성 |

> 검증: 로컬 `apt-cache show ros-jazzy-fastrtps` — `2.14.6` 확인  
> 검증: https://github.com/ros2/ros2/blob/jazzy/ros2.repos — `eProsima/Fast-DDS version: 2.14.x` 확인  
> 검증: https://docs.ros.org/en/humble/Concepts/Intermediate/About-Different-Middleware-Vendors.html — Humble 기본값 FastDDS 확인  
> 미검증: Humble의 정확한 FastDDS 버전 (현재 환경에 Humble 미설치, 2.6.x는 커뮤니티 통설)

**FastDDS 2.14.x에서 달라진 것:**

- **Discovery Server v2 스마트 필터링 완성**: 토픽을 기준으로 "이 두 노드가 통신할 필요가 있나"를 판단하여 불필요한 discovery 메시지를 차단. v1은 모든 노드 정보를 전부 주고받았음.
- 성능 및 안정성 개선 누적 (2.6 → 2.14, 8 마이너 버전 차이)

---

## Simple Discovery 동작 변화 — ROS_AUTOMATIC_DISCOVERY_RANGE

Jazzy에서 새로 생긴 환경변수.

```bash
# Jazzy 환경에서 기본 설정 (source /opt/ros/jazzy/setup.bash 시 자동 설정)
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
```

| 값 | 동작 |
|----|------|
| `SUBNET` | 같은 서브넷(라우터 내부) 전체에서 멀티캐스트 (Humble 기본 동작과 동일) |
| `LOCALHOST` | 같은 PC 내부끼리만 discovery |
| `OFF` | 자동 discovery 비활성화 (Discovery Server만 사용) |

**Humble과의 차이:**  
Humble에는 이 변수가 없었고, Simple Discovery는 항상 서브넷 전체 멀티캐스트였음.  
Jazzy는 범위를 명시적으로 제어할 수 있게 됐다.

> 검증: 로컬 `printenv | grep ROS` — 현재 Jazzy 환경에서 `ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET` 확인  
> 미검증: 각 값의 내부 동작 세부 — 공식 Jazzy discovery 문서 접근 실패 (404)

---

## TurtleBot4 아키텍처 변화

### Create3 네트워크 연결 방식

| 항목 | Humble | Jazzy |
|------|--------|-------|
| Create3 WiFi 연결 | 필수 (2.4GHz) | 금지 (오프라인) |
| Create3 ↔ RPi 통신 | WiFi + USB-C 모두 | USB-C (Ethernet over USB) 전용 |
| RPi WiFi 대역 | 2.4/5GHz 브리지 필요 | 5GHz 단독 가능 |

**Humble 시절 문제:**  
Create3가 2.4GHz만 지원하므로 AP가 2.4/5GHz를 같은 SSID로 브리지해야 했음.  
"Networks that provide 2.4 GHz and 5 GHz on the same SSID may not work properly with the Create3" 문제가 상존했음.

**Jazzy 해결책:**  
Create3를 WiFi에서 완전히 분리. RPi만 WiFi(5GHz 가능)에 연결하고,  
Create3 ↔ RPi는 USB-C(Ethernet over USB)로만 통신.

---

### create3_republisher 역할

```
[Humble]
  Create3 ──USB-C──► RPi ──(republisher 선택 설치)──► WiFi ──► PC
                          └────────────────────────────► WiFi ──► PC (직접도 가능)

[Jazzy]
  Create3 ──USB-C──► RPi ──(republisher 필수)──► WiFi ──► PC
```

| 항목 | Humble | Jazzy |
|------|--------|-------|
| `create3_republisher` 실행 | 선택 (수동 활성화) | 필수 (항상 실행) |
| Create3 토픽 재발행 | 선택적 | 의무적 |

Jazzy에서 Create3 토픽(`/battery_state`, `/odom` 등)은 항상 RPi를 거쳐 재발행되어 PC에 도달.  
`/robot8/battery_state` 같은 네임스페이스 토픽이 보이는 것이 이 구조 때문.

> 검증: https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html — "Jazzy version always uses the create3_republisher" 확인

---

### Namespace 설정 차이

| 항목 | Humble | Jazzy |
|------|--------|-------|
| Create3 앱 Namespace | 비워두거나 로봇명 | `/_do_not_use` 로 설정 |
| RPi Namespace | `/robot<N>` | `/robot<N>` (동일) |

Jazzy에서는 Create3의 WiFi ROS2 인터페이스를 비활성화하기 위해 Create3 웹 서버(192.168.10.1:8080)에서 namespace를 `/_do_not_use`로 설정.  
실제 토픽은 전부 RPi의 네임스페이스(`/robot8/...`)에서 발행.

> 검증: https://turtlebot.github.io/turtlebot4-user-manual/setup/simple_discovery.html — Jazzy에서 Create3 ROS2 Namespace를 `/_do_not_use`로 설정 확인

---

## Discovery Server 설정 — Humble vs Jazzy 비교

Discovery Server 설정 방식은 양쪽 모두 FastDDS + `ROS_DISCOVERY_SERVER`로 동일.  
단, Jazzy에서 `ROS_SUPER_CLIENT` 처리 방식이 더 명확해짐.

```bash
# PC setup.bash — Humble
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_SUPER_CLIENT=True
export ROS_DOMAIN_ID=0
export ROS_DISCOVERY_SERVER="<로봇IP>:11811"

# PC setup.bash — Jazzy
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
[ -t 0 ] && export ROS_SUPER_CLIENT=True || export ROS_SUPER_CLIENT=False  ← 조건부
export ROS_DOMAIN_ID=0
export ROS_DISCOVERY_SERVER="<로봇IP>:11811"
```

Jazzy에서 `ROS_SUPER_CLIENT`를 인터랙티브 터미널에서만 True로 설정하는 이유:  
스크립트나 런치파일 등 비인터랙티브 환경에서 Super Client로 돌면 불필요한 전체 discovery 정보를 수신하게 되어 오버헤드 발생.

> 검증: 로컬 `/etc/turtlebot4_discovery/setup.bash` — `[ -t 0 ]` 조건부 설정 확인  
> 검증: https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html — configure_discovery.sh jazzy 브랜치 별도 관리 확인

---

## 한눈에 보기

| 항목 | Humble | Jazzy | 비고 |
|------|--------|-------|------|
| FastDDS 버전 | 2.6.x | 2.14.x | DS v2 완성 |
| 기본 RMW | `rmw_fastrtps_cpp` | `rmw_fastrtps_cpp` | 동일 |
| ROS_AUTOMATIC_DISCOVERY_RANGE | 없음 | SUBNET (기본) | Simple Discovery 범위 제어 |
| Create3 WiFi | 필수 (2.4GHz) | 금지 | RPi 5GHz 단독 가능 |
| create3_republisher | 선택 | 필수 | 항상 실행 |
| Create3 namespace | 직접 설정 | `/_do_not_use` | WiFi ROS2 비활성화 |
| ROS_SUPER_CLIENT 처리 | 항상 True | 조건부 (인터랙티브만) | 오버헤드 감소 |

---

## 다른 파일과의 연결

- FastDDS Discovery Server 개념, Server ID, ROS_SUPER_CLIENT → [fastdds_and_discovery_server.md](fastdds_and_discovery_server.md)
- TurtleBot4 싱글로봇 네트워크 설정 → [turtlebot4_single_robot_network.md](turtlebot4_single_robot_network.md)
- Create3 ↔ RPi 물리 연결(Ethernet over USB) → [turtlebot4_lecture_5th_updates.md](turtlebot4_lecture_5th_updates.md)
