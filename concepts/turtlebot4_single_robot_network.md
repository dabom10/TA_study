# TurtleBot4 싱글로봇 네트워크 설정

## 통신 구조

```
[PC] ──WiFi──► [라즈베리파이 (Discovery Server)]
                        │
                     USB-C
                        │
                   [Create3]
```

라즈베리파이가 Discovery Server 역할, PC가 클라이언트. Create3는 WiFi 직접 연결 불필요.

---

> Domain ID vs Discovery Server ID 역할 구분, 싱글→멀티 전환 시나리오 → [fastdds_and_discovery_server.md](fastdds_and_discovery_server.md)

---

## Discovery Server Onboard vs Offboard

| 항목 | 의미 | 싱글로봇 |
|------|------|---------|
| Onboard Server | 라즈베리파이 자체에서 실행되는 서버 | 필요 (항상 켜두기) |
| Offboard Server | 외부(User PC 등)에 있는 추가 서버 | **불필요** — IP 비워두기 |

> Offboard IP를 비우면 Port/Server ID는 신경 쓸 필요 없음

> Discovery Server를 끄면 Simple Discovery(브로드캐스트) 모드로 동작 → 트래픽 많고 불안정. **끄지 말 것.**

---

## ROS_DISCOVERY_SERVER 형식과 Server ID의 관계

```bash
"<로봇IP>:11811"         # ID 0 위치 → Onboard ID=0 과 매칭
";<로봇IP>:11811"        # ID 1 위치 → Onboard ID=1 과 매칭
";;<로봇IP>:11811"       # ID 2 위치 → Onboard ID=2 과 매칭
```

세미콜론 개수 = Server ID. PC가 찾는 ID와 라즈베리파이 Onboard Server ID가 **반드시 일치**해야 함.

---

## TUI 설정 방법

### 로봇 TUI 진입 (SSH 후)

```bash
ssh ubuntu@<로봇IP>
turtlebot4-setup
```

TUI 구조:
```
turtlebot4-setup
├── Bash Setup        → Namespace, Domain ID, RMW 설정
├── Discovery Server  → Enabled, Server ID, Port 설정
└── Apply Settings    → 저장 및 재시작
```

### 싱글로봇 기준 정상 설정값

| 항목 | 값 |
|------|-----|
| `ROBOT_NAMESPACE` | `/robot<번호>` |
| `ROS_DOMAIN_ID` | 로봇별 고유 ID |
| `RMW_IMPLEMENTATION` | `rmw_fastrtps_cpp` |
| Discovery `Enabled` | `True` |
| Discovery `Onboard Server ID` | 임의 (나중에 멀티로봇 전환 고려해서 고유하게) |
| Discovery `Onboard Port` | `11811` |
| Discovery `Offboard Server IP` | **반드시 비움** (싱글로봇) — IP 비우면 Offboard 설정 전체 무시 |

---

## PC setup.bash 형식

```bash
# /etc/turtlebot4_discovery/setup.bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
[ -t 0 ] && export ROS_SUPER_CLIENT=True || export ROS_SUPER_CLIENT=False
export ROS_DOMAIN_ID=<로봇과 동일>
export ROS_DISCOVERY_SERVER="<세미콜론 수=Onboard Server ID><로봇IP>:11811"
# 예) Onboard ID=0 → "<로봇IP>:11811"
# 예) Onboard ID=1 → ";<로봇IP>:11811"
# 예) Onboard ID=2 → ";;<로봇IP>:11811"
```

> ⚠️ 세미콜론 개수가 Onboard Server ID와 반드시 일치해야 함

수정 후:
```bash
source ~/.bashrc
ros2 daemon stop && ros2 daemon start
```

---

> LED 상태 전체 → [electrical/03_ui_pcba.md](../concepts/turtlebot4_manual/electrical/03_ui_pcba.md)

---

## 빠른 진단

`ros2 topic list`에 토픽이 안 뜰 때:

```bash
# 환경변수 확인
echo $ROS_DISCOVERY_SERVER   # "<IP>:11811" 형태, 세미콜론 위치 확인
echo $ROS_DOMAIN_ID          # 로봇과 동일한지
echo $ROS_SUPER_CLIENT       # True인지

# Discovery Server 포트 연결 확인
nc -zv <로봇IP> 11811        # "Connection refused" → 서버 미실행

# 로봇에서 fastdds 실행 중인지 확인
ssh ubuntu@<로봇IP> "ps aux | grep fastdds"
# fastdds discovery -i 0 -p 11811 있어야 함

# daemon 재시작
ros2 daemon stop && ros2 daemon start && ros2 topic list
```

| 증상 | 원인 | 해결 |
|------|------|------|
| 토픽 없음 | `ROS_DISCOVERY_SERVER` 세미콜론 위치 오류 | Onboard Server ID와 세미콜론 개수 맞추기 |
| 토픽 없음 | Domain ID 불일치 | 로봇 TUI와 PC setup.bash 동일하게 |
| 토픽 없음 | SSH 터미널에서 확인 | SSH는 로봇 로컬이라 당연히 뜸, PC에서 확인 |
| 토픽 일부만 | `ROS_SUPER_CLIENT=False` | 새 터미널 열고 source 재실행 |
