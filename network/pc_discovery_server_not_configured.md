# PC의 ROS_DISCOVERY_SERVER 미설정으로 로봇 토픽 미출력

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu, ROS2 Jazzy |
| RMW | rmw_fastrtps_cpp (FastDDS) |
| 로봇 | TurtleBot4 (Jazzy, robot8 namespace) |
| 통신 방식 | Discovery Server (로봇 Onboard) |

---

## 문제 상황

PC에서 `ros2 topic list`를 실행하면 로봇 토픽(`/robot8/*`)이 전혀 출력되지 않음.  
로봇에 SSH 접속 후 동일 명령 실행하면 토픽 정상 출력.

```
# PC에서
$ ros2 topic list
/parameter_events
/rosout

# 로봇 SSH에서
$ ros2 topic list
/robot8/battery_state
/robot8/cmd_vel
...
```

---

## 원인

FastDDS **Discovery Server 모드**는 클라이언트가 서버 주소를 명시적으로 알아야 통신 가능.  
PC의 `/etc/turtlebot4_discovery/setup.bash`에 `ROS_DISCOVERY_SERVER` 줄이 **주석 처리**되어 있어, PC가 Discovery Server 위치를 모르는 상태였음.

```bash
# /etc/turtlebot4_discovery/setup.bash (문제 상태)
# export ROS_DISCOVERY_SERVER="<PC자신IP>:11811;"  ← 주석 + IP도 틀림
```

### Discovery Server 통신 구조 (왜 이런 일이 생기나)

```
[로봇 라즈베리파이]
  fast-discovery-server → 0.0.0.0:11811 에서 대기 (외부 접근 가능)
  로봇 내 ROS2 노드 → ROS_DISCOVERY_SERVER=127.0.0.1:11811 로 서버에 등록
                                    │
                               서버가 노드 목록 관리
                                    │
[PC] ─── ROS_DISCOVERY_SERVER=<로봇IP>:11811 ──► 서버에 접속 → 노드 목록 공유
```

Simple Discovery(멀티캐스트)와 달리 Discovery Server 모드는 "서버를 통해서만 노드를 발견"하는 구조.  
서버 주소(`ROS_DISCOVERY_SERVER`)가 없으면 PC는 로봇 노드를 전혀 인식하지 못함.

SSH 터미널에서 토픽이 보이는 이유: SSH는 로봇 내부에서 실행되므로 `127.0.0.1:11811`에 직접 접근 가능.

---

## 진단 순서

1. **PC 환경변수 확인** — `ROS_DISCOVERY_SERVER`가 비어 있으면 설정 자체가 안 된 것
   ```bash
   echo $ROS_DISCOVERY_SERVER
   ```

2. **로봇에서 Discovery Server 프로세스 확인**
   ```bash
   ps aux | grep fastdds
   # fast-discovery-server 가 0.0.0.0:11811 에 있어야 함
   ```

3. **로봇 환경변수 확인** — 로봇이 어떤 모드로 동작 중인지
   ```bash
   echo $ROS_DISCOVERY_SERVER   # 127.0.0.1:11811; 이 나오면 Discovery Server 모드
   echo $RMW_IMPLEMENTATION     # rmw_fastrtps_cpp 이어야 함
   echo $ROS_DOMAIN_ID
   ```

4. **로봇 IP 확인** — PC와 같은 서브넷 IP 선택
   ```bash
   hostname -I
   # 여러 IP가 나올 경우 PC의 서브넷(앞 3자리)과 일치하는 것 사용
   ```

5. **PC의 setup.bash 확인**
   ```bash
   cat /etc/turtlebot4_discovery/setup.bash
   # ROS_DISCOVERY_SERVER 줄이 주석이거나 없으면 원인 확정
   ```

---

## 해결 방법

`/etc/turtlebot4_discovery/setup.bash`에서 `ROS_DISCOVERY_SERVER` 줄을 활성화하고 로봇 IP로 수정.

```bash
# 수정 전 (주석 처리 + IP 틀림)
# export ROS_DISCOVERY_SERVER="<PC자신IP>:11811;"

# 수정 후 (주석 해제 + 로봇 IP)
export ROS_DISCOVERY_SERVER="<로봇IP>:11811"
```

> ⚠️ 앞뒤 세미콜론 없이 작성. 세미콜론 위치가 Server ID를 결정함 → [TUI_discovery_N_setup_bash.md](TUI_discovery_N_setup_bash.md)

수정 후 적용:
```bash
source /etc/turtlebot4_discovery/setup.bash
ros2 daemon stop && ros2 daemon start
ros2 topic list
```

---

## 참고

> 검증: `/etc/turtlebot4_discovery/setup.bash` 직접 확인 — `ROS_DISCOVERY_SERVER` 주석 처리 확인  
> 검증: 로봇 `ps aux | grep fastdds` — `fast-discovery-server` 프로세스 `0.0.0.0:11811` 실행 확인  
> 검증: 로봇 `echo $ROS_DISCOVERY_SERVER` — `127.0.0.1:11811;` 확인  
> 검증: https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html — Discovery Server 방식 및 PC 설정 절차 일치

- `hostname -I`로 IP가 여러 개 나올 때: PC의 서브넷과 일치하는 것 사용
- `ROS_SUPER_CLIENT`: setup.bash 내 `[ -t 0 ]` 조건으로 인터랙티브 터미널에서만 `True` → `ros2 topic list`가 모든 토픽을 보여줌. 비인터랙티브 환경(스크립트 등)에서는 `False`여서 일부 토픽만 보일 수 있음
- Discovery Server 개념 상세 → [fastdds_and_discovery_server.md](../concepts/fastdds_and_discovery_server.md)
- 싱글로봇 네트워크 전체 설정 → [turtlebot4_single_robot_network.md](../concepts/turtlebot4_single_robot_network.md)
