# TurtleBot4 TUI 설정 완전 가이드

TurtleBot4의 설정 메뉴(`turtlebot4-setup`)에서 볼 수 있는 항목들과,
그 설정이 User PC의 `/etc/turtlebot4_discovery/setup.bash`에 어떻게 반영되는지를 정리한 문서.

---

## TUI란?

```bash
turtlebot4-setup   # 터미널에서 실행
```

터미널에서 실행하는 텍스트 기반 설정 메뉴.  
내부적으로 터틀봇의 설정 파일들을 수정해 주는 도구임.

---

## 전체 구조 요약

```
turtlebot4-setup
├── Discovery Server     ← ROS2 노드 탐색 방식 설정
├── Bash Setup           ← ROS2 환경변수 설정
├── ROS Setup            ← ROS 도메인, 네임스페이스 등
└── Apply Settings       ← 변경사항 저장 및 적용
```

---

## 1. Discovery Server 메뉴

### Discovery Server란?

ROS2 노드들이 서로를 찾는(탐색하는) 방식.  
기본 방식(Simple Discovery)은 브로드캐스트로 서로를 탐색하는데,
이건 네트워크 트래픽이 많고 불안정함.

**Discovery Server 방식**은 중앙 서버 하나를 지정해 두고,
모든 노드가 그 서버에 자신을 등록하고 조회하는 방식.
TurtleBot4는 기본적으로 이 방식을 사용함.

```
[User PC 노드]  ──등록/조회──▶  [Discovery Server (터틀봇 내부)]
[터틀봇 노드]   ──등록/조회──▶  [Discovery Server (터틀봇 내부)]
```

---

### TUI 항목 설명

```
Enabled                         [True]
Onboard Server - Port           [11811]
Onboard Server - Server ID      [0]
Offboard Server - IP            [192.168.1.2]
Offboard Server - Port          [11811]
Offboard Server - Server ID     [1]
```

#### Enabled
Discovery Server 기능 자체를 켜고 끄는 스위치.  
`True`면 아래 설정들이 의미 있음. `False`면 Simple Discovery로 동작.

---

#### Onboard Server

> **터틀봇 안에서 직접 실행되는 Discovery Server**

| 항목 | 설명 |
|------|------|
| `Onboard Server - Port` | 서버가 열리는 포트 번호. 기본값 `11811` |
| `Onboard Server - Server ID` | 이 서버의 ID 번호. 기본값 `0` |

터틀봇 내부에서 아래 명령어가 자동 실행됨:
```bash
fastdds discovery -i 0 -p 11811
#                 ↑       ↑
#            Server ID   Port
```

즉, **터틀봇이 ROS2 네트워크의 허브 역할**을 함.

---

#### Offboard Server

> **외부(터틀봇 밖)에 있는 추가 Discovery Server**  
> 보통은 쓰지 않음. 여러 로봇이 있거나 별도 서버를 운영할 때 사용.

| 항목 | 설명 |
|------|------|
| `Offboard Server - IP` | 외부 서버의 IP 주소 |
| `Offboard Server - Port` | 외부 서버의 포트 번호 |
| `Offboard Server - Server ID` | 외부 서버의 ID 번호 |

> ⚠️ TUI에 Offboard IP가 `192.168.1.2`로 표시되어 있어도,
> 이건 터틀봇 자체 IP이므로 "실질적으로 외부 서버 없음"과 동일한 상태일 수 있음.
> 현재 구성에서는 Onboard Server(ID 0)만 사용 중.

---

### setup.bash와의 관계

TUI의 Discovery Server 설정 → User PC의 `ROS_DISCOVERY_SERVER` 환경변수에 반영됨.

#### ROS_DISCOVERY_SERVER 형식

```
서버ID0주소 ; 서버ID1주소 ; 서버ID2주소 ...
```

세미콜론(`;`)이 구분자이며, **위치(순서)가 서버 ID**를 결정함.

| 값 | ID 0 | ID 1 |
|----|------|------|
| `192.168.1.2:11811` | 192.168.1.2:11811 | 없음 |
| `;192.168.1.2:11811` | 없음 | 192.168.1.2:11811 |
| `A:11811;B:11811` | A:11811 | B:11811 |

#### 현재 올바른 설정 (Onboard Server ID=0 사용 시)

```bash
# /etc/turtlebot4_discovery/setup.bash
export ROS_DISCOVERY_SERVER="192.168.1.2:11811"
#                             ↑터틀봇IP  ↑포트
# 세미콜론 없음 → ID 0 위치에 서버 지정 → 터틀봇 Onboard Server(ID 0)와 일치
```

#### 흔한 실수

```bash
# ❌ 잘못된 설정
export ROS_DISCOVERY_SERVER=";192.168.1.2:11811;"
# → ID 0 비어있음, ID 1에 터틀봇 지정
# → 터틀봇은 ID 0으로 실행 중이므로 연결 실패
# → ros2 topic list 해도 토픽이 안 뜸
```

---

## 2. Bash Setup 메뉴

터틀봇과 User PC의 ROS2 환경변수를 설정하는 곳.

```
ROBOT_NAMESPACE                    [/robot8]
ROS_DOMAIN_ID                      [1]
RMW_IMPLEMENTATION                 [rmw_fastrtps_cpp]
TURTLEBOT4_DIAGNOSTICS             [Enabled]
WORKSPACE_SETUP                    [/opt/ros/humble/setup.bash]
CYCLONEDDS_URI                     [/etc/turtlebot4/cyclonedds_rpi.xml]
FASTRTPS_DEFAULT_PROFILES_FILE     [/etc/turtlebot4/fastdds_rpi.xml]
```

---

### ROBOT_NAMESPACE

```
[/robot8]
```

터틀봇의 모든 토픽/서비스 앞에 붙는 네임스페이스.  
`/robot8`로 설정하면 토픽이 `/robot8/cmd_vel`, `/robot8/odom` 등으로 뜸.  
같은 네트워크에 여러 대의 터틀봇이 있을 때 구분하기 위해 사용.

setup.bash에는 직접 변수로 없고, 터틀봇 내부 설정 파일에 반영됨.

---

### ROS_DOMAIN_ID

```
[1]
```

같은 네트워크에서 ROS2 통신을 **그룹으로 격리**하는 ID.  
같은 Domain ID를 가진 노드끼리만 통신 가능.

```bash
# /etc/turtlebot4_discovery/setup.bash
export ROS_DOMAIN_ID=1
```

> ⚠️ 터틀봇과 User PC의 `ROS_DOMAIN_ID`가 다르면 **완전히 통신 불가**.  
> 기본값은 `0`. 여러 팀이 같은 공간에 있을 때 팀마다 다른 ID를 씀.

---

### RMW_IMPLEMENTATION

```
[rmw_fastrtps_cpp]
```

ROS2가 내부적으로 사용하는 통신 미들웨어(DDS) 구현체.

| 값 | 설명 |
|----|------|
| `rmw_fastrtps_cpp` | Fast DDS (eProsima). TurtleBot4 기본값. Discovery Server 기능 지원 |
| `rmw_cyclonedds_cpp` | CycloneDDS. 더 가볍지만 Discovery Server 미지원 |

```bash
# /etc/turtlebot4_discovery/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

> Discovery Server를 사용하려면 반드시 `rmw_fastrtps_cpp`여야 함.

---

### TURTLEBOT4_DIAGNOSTICS

```
[Enabled]
```

배터리, 센서 등 터틀봇 상태를 `/diagnostics` 토픽으로 발행할지 여부.  
setup.bash에 직접 반영되는 항목은 아님 (터틀봇 내부 서비스 설정).

---

### WORKSPACE_SETUP

```
[/opt/ros/humble/setup.bash]
```

ROS2 환경을 불러오는 기본 setup 파일 경로.  
커스텀 워크스페이스가 있으면 `/home/ubuntu/ros2_ws/install/setup.bash` 등으로 변경.

```bash
# /etc/turtlebot4_discovery/setup.bash
source /opt/ros/humble/setup.bash
```

---

### CYCLONEDDS_URI / FASTRTPS_DEFAULT_PROFILES_FILE

```
CYCLONEDDS_URI               [/etc/turtlebot4/cyclonedds_rpi.xml]
FASTRTPS_DEFAULT_PROFILES_FILE [/etc/turtlebot4/fastdds_rpi.xml]
```

각 DDS 구현체의 세부 설정 파일 경로.  
네트워크 인터페이스, 버퍼 크기 등 고급 설정을 XML로 정의함.  
보통 건드릴 필요 없음.

---

## 3. ROS_SUPER_CLIENT

TUI 메뉴에는 없지만 setup.bash에 존재하는 중요한 변수.

```bash
[ -t 0 ] && export ROS_SUPER_CLIENT=True || export ROS_SUPER_CLIENT=False
```

| 값 | 동작 |
|----|------|
| `True` | Discovery Server에 등록된 **모든 노드/토픽**을 볼 수 있음 |
| `False` | 자신과 직접 연결된 노드만 볼 수 있음 |

위 코드는 **인터랙티브 터미널이면 True, 아니면 False**로 자동 설정.  
`ros2 topic list`가 제대로 동작하려면 `True`여야 함.

---

## 4. 전체 대응표

| TUI 항목 | setup.bash 변수 | 예시 값 |
|----------|----------------|---------|
| Enabled = True | `ROS_DISCOVERY_SERVER` 설정 자체 | 변수가 존재하면 활성화 |
| Onboard Server ID | `ROS_DISCOVERY_SERVER`에서 해당 ID 위치 | ID 0 → 맨 앞 |
| Onboard Server Port | `ROS_DISCOVERY_SERVER`에서 포트 | `11811` |
| Offboard Server IP+Port+ID | 동일하게 `;` 뒤 위치에 기입 | ID 1 → `;IP:PORT` |
| ROS_DOMAIN_ID | `ROS_DOMAIN_ID` | `1` |
| RMW_IMPLEMENTATION | `RMW_IMPLEMENTATION` | `rmw_fastrtps_cpp` |
| WORKSPACE_SETUP | `source` 경로 | `/opt/ros/humble/setup.bash` |

---

## 5. 현재 정상 setup.bash 예시

```bash
# /etc/turtlebot4_discovery/setup.bash

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
[ -t 0 ] && export ROS_SUPER_CLIENT=True || export ROS_SUPER_CLIENT=False
export ROS_DOMAIN_ID=1
export ROS_DISCOVERY_SERVER="192.168.1.2:11811"
#                             ↑ 터틀봇 IP, 세미콜론 없이 → ID 0 서버
```

---

## 6. 설정 확인 체크리스트

```bash
# 1. 환경변수 확인
echo $ROS_DISCOVERY_SERVER    # 192.168.1.2:11811 이어야 함 (세미콜론 없이)
echo $ROS_DOMAIN_ID           # 터틀봇과 동일해야 함
echo $ROS_SUPER_CLIENT        # True여야 토픽 전체 보임
echo $RMW_IMPLEMENTATION      # rmw_fastrtps_cpp

# 2. Discovery Server 포트 접근 확인
nc -zv 192.168.1.2 11811      # 연결되면 정상

# 3. 터틀봇에서 서버 실행 확인
ssh ubuntu@192.168.1.2 "ps aux | grep fastdds"
# fastdds discovery -i 0 -p 11811 이 있어야 함

# 4. 토픽 확인
ros2 topic list               # /robot8/... 토픽들이 보여야 함
```
