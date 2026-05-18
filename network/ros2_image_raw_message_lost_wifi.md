# ros2 topic echo image_raw — A message was lost (WiFi 원격 수신)

## 환경

- OS: Ubuntu 24.04, ROS2 Jazzy
- RMW: rmw_fastrtps_cpp (PC·로봇 동일)
- 네트워크: WiFi (5GHz), PC ↔ TurtleBot4 원격 통신
- 카메라: OAK-D Pro (`depthai_ros`)
- sysctl 사전 적용: `ipfrag_high_thresh=134217728`, `ipfrag_time=3`

---

## 문제 상황

PC에서 `ros2 topic echo /robotN/oakd/rgb/image_raw` 실행 시 메시지 손실 반복:

```
A message was lost!!!
    total count change:13
    total count: 14
A message was lost!!!
    total count change:1
    total count: 15
```

- 로봇 로컬(`ubuntu@turtlebot4`)에서는 `ros2 topic hz` 결과 **30.982Hz 안정**
- PC에서 `ros2 topic hz` 실행 시 **"does not appear to be published yet"** 출력 (토픽 자체를 탐지 못함)
- PC CPU는 90% idle, 버퍼 설정도 정상 — 수신 측 자원 문제 아님
- `compressed` 토픽은 PC에서 정상 수신

---

## 원인

두 가지가 복합적으로 작용.

### 원인 1: DDS Simple Discovery 멀티캐스트 실패 (버스트 손실의 직접 원인)

FastDDS 기본 동작인 Simple Discovery는 멀티캐스트로 publisher를 탐지한다.  
WiFi AP는 클라이언트 간 멀티캐스트를 간헐적으로 억제하므로, AP가 멀티캐스트를 차단하는 순간 subscriber가 publisher를 잃었다가 복구 시 그동안 빠진 메시지를 한꺼번에 `lost`로 보고한다.

→ 13~14개씩 버스트로 손실되는 패턴, `topic hz`가 토픽을 아예 인식 못 하는 것이 이 원인의 증거.

> 검증: [ROS2 DDS tuning 공식 문서](https://docs.ros.org/en/rolling/How-To-Guides/DDS-tuning.html) — "Sending data over lossy (usually WiFi) connections becomes problematic when some IP fragments are dropped, possibly causing the kernel buffer on the receiving side to become full."

### 원인 2: raw image 대역폭 — WiFi+DDS의 구조적 한계

| 토픽 | 1프레임 크기 | 30fps 이론 대역폭 |
|------|------------|-----------------|
| `rgb/image_raw` (640×480 bgr8) | ~900 KB | ~216 Mbps |
| `rgb/image_raw/compressed` | ~30–50 KB | ~12 Mbps |

900KB 1프레임은 UDP 패킷 600개 이상으로 단편화된다. 단 1개만 손실돼도 프레임 전체가 드롭된다.  
→ Discovery 문제를 해결해도 raw 자체가 WiFi 전송에 취약하다.

---

## 진단 순서

1. **PC CPU 확인** (`top`, `mpstat`) → 90% idle, 메모리 여유 충분 → PC 자원 문제 아님
2. **로봇 vs PC 비교** → 로봇 로컬 30Hz 안정, PC만 손실 → 네트워크 레이어 문제
3. **sysctl 확인** (`ipfrag_high_thresh`, `ipfrag_time`) → 이미 ROS2 권장값 적용 중 → 버퍼 문제 아님
4. **손실 패턴 분석** → 1~14개 버스트, `topic hz` 인식 불가 → discovery 실패·재연결 패턴
5. **DDS 환경 확인** (`echo $RMW_IMPLEMENTATION`, `ros2 doctor --report`) → Simple Discovery 사용 중, DDS 프로파일 없음 확인

---

## 해결 방법

### 1단계: Discovery Server로 전환 (원인 1 해결)

멀티캐스트 대신 TCP 직접 연결로 discovery를 수행해 AP 멀티캐스트 억제 문제 우회.

**로봇에서 (SSH):**
```bash
turtlebot4-setup
# ROS Setup → Discovery Server → Enabled: True, Port: 11811, Server ID: 0
turtlebot4-source
ros2 daemon stop && ros2 daemon start
```

**PC에서:**
```bash
wget -qO - https://raw.githubusercontent.com/turtlebot/turtlebot4_setup/humble/turtlebot4_discovery/configure_discovery.sh | bash <(cat) </dev/tty
# 입력값: DOMAIN_ID=0, Server IP=<로봇IP>, Port=11811
source ~/.bashrc
ros2 daemon stop && ros2 daemon start
```

스크립트가 `/etc/turtlebot4_discovery/setup.bash`를 생성하고 `~/.bashrc`에서 source함.

```bash
# /etc/turtlebot4_discovery/setup.bash 내용
source /opt/ros/jazzy/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
[ -t 0 ] && export ROS_SUPER_CLIENT=True || export ROS_SUPER_CLIENT=False
export ROS_DOMAIN_ID=0
export ROS_DISCOVERY_SERVER="<로봇IP>:11811;"
```

> Discovery Server 개념 상세 → [fastdds_and_discovery_server.md](../concepts/fastdds_and_discovery_server.md)

### 2단계: compressed 토픽 사용 (원인 2 대응)

```bash
ros2 topic echo /robotN/oakd/rgb/image_raw/compressed
```

rqt_image_view, rviz2에서도 `/image_raw`를 선택 후 transport를 `compressed`로 변경하면 동일.

raw가 반드시 필요한 경우 로봇 쪽에서 해상도·fps를 낮추거나(OAK-D YAML 파라미터 수정),  
FastDDS XML 프로파일로 단편 크기를 MTU 이하로 고정하는 방법이 있으나 근본 해결은 아님.

---

## 결과

- Discovery Server 전환 후 버스트 손실 및 `topic hz` 인식 불가 현상 해소
- `compressed` 토픽은 PC에서 안정 수신
- `image_raw`는 Discovery 후에도 WiFi 대역폭 한계로 손실 지속 → compressed 사용 권장

---

## 참고

- [ROS2 DDS tuning 공식 문서](https://docs.ros.org/en/rolling/How-To-Guides/DDS-tuning.html)
- [TurtleBot4 User Manual — Discovery Server](https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html)
- [turtlebot4/issues/152](https://github.com/turtlebot/turtlebot4/issues/152) — 같은 증상 리포트
