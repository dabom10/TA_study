# FastDDS 멀티캐스트 peer discovery 불능 — 시뮬레이션 로봇 미스폰

## 환경

- OS: Ubuntu 24.04
- ROS2: Jazzy
- RMW: rmw_fastrtps_cpp (기본)
- 패키지: `ros-jazzy-turtlebot4-simulator`, `ros-jazzy-ros-gz-sim 1.0.22`, Gazebo Harmonic 8.11.0

## 문제 상황

`ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py` 실행 시:

1. Gazebo 창은 열리고 warehouse world 로드됨
2. **로봇이 스폰되지 않음** — Gazebo에 로봇 미표시
3. **`ros2 node list` 빈 출력** — 45개 이상 프로세스가 실제로 실행 중임에도 불구하고

## 원인

**FastDDS(rmw_fastrtps_cpp) 멀티캐스트 peer discovery 불능**

같은 PC 내 프로세스 간 DDS 토픽 통신 자체가 작동하지 않아, `robot_state_publisher`가 `/robot_description` 토픽을 발행해도 `ros_gz_sim create`가 수신하지 못한다. 그 결과 로봇 스폰이 무한정 대기 상태가 된다.

**연쇄 실패 흐름:**

```
robot_state_publisher → /robot_description (transient_local) 발행
                              ↓
        [FastDDS peer discovery 불능 → 구독자가 publisher 미발견]
                              ↓
ros_gz_sim create → "Waiting messages on topic [robot_description]." (1초마다 반복)
                              ↓
              로봇 스폰 실패 → Gazebo 빈 화면
```

## 진단 순서

```bash
# 1. Gazebo Fuel 캐시 확인 (없으면 온라인 모델 다운로드 실패 가능성)
ls ~/.gz/fuel/fuel.gazebosim.org/openrobotics/models/ | grep -i warehouse
# → 캐시 있으면 이 원인 제외

# 2. ROS_DOMAIN_ID 확인 (모든 터미널이 동일한지)
echo $ROS_DOMAIN_ID
# → 0 이면 기본값. 터미널별로 다르면 node list 빈 출력 가능

# 3. 기본 DDS 통신 테스트 (핵심 진단)
ros2 topic pub /test_topic std_msgs/msg/String "data: hello" --once &
sleep 2
ros2 topic echo /test_topic std_msgs/msg/String --once --timeout 3
# → "Waiting for at least 1 matching subscription(s)..." 무한 반복이면 DDS discovery 불능 확정

# 4. launch 실행 후 로그 확인 (실제 에러 메시지 파악)
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py 2>&1 | grep -E "Waiting|ERROR|error|failed"
# → "[ros_gz_sim]: Waiting messages on topic [robot_description]." 반복이면 이 이슈
```

**create 바이너리 소스 분석 결과 (ros_gz_sim 1.0.22):**
- `-topic` 옵션 시 `rclcpp::QoS(1).transient_local()` QoS로 구독 (line 76 of create.cpp) → QoS 불일치 아님
- `robot_state_publisher` 도 `transient_local` 로 발행 → QoS 호환 문제 아님
- 결론: 코드 레벨 문제가 아니라 FastDDS peer discovery 자체 문제

## 해결 방법

### [미해결 — 내일 이어서 확인]

**후보 1: FastDDS 프로필로 localhost-only 강제 (가장 유력)**

```bash
# ~/.ros/fastdds_localhost.xml 생성
cat > ~/.ros/fastdds_localhost.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8" ?>
<profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
    <transport_descriptors>
        <transport_descriptor>
            <transport_id>LocalhostTransport</transport_id>
            <type>UDPv4</type>
            <interfaceWhiteList>
                <address>127.0.0.1</address>
            </interfaceWhiteList>
        </transport_descriptor>
    </transport_descriptors>
    <participant profile_name="localhost_profile" is_default_profile="true">
        <rtps>
            <userTransports>
                <transport_id>LocalhostTransport</transport_id>
            </userTransports>
            <useBuiltinTransports>false</useBuiltinTransports>
        </rtps>
    </participant>
</profiles>
EOF

export FASTRTPS_DEFAULT_PROFILES_FILE=~/.ros/fastdds_localhost.xml
# 이후 launch 재실행 → DDS 통신 테스트 선행
```

**후보 2: ROS_LOCALHOST_ONLY=1**

```bash
export ROS_LOCALHOST_ONLY=1
# 동일 환경에서 통신 테스트 후 launch 시도
```

**후보 3: CycloneDDS로 전환**

```bash
sudo apt install ros-jazzy-rmw-cyclonedds-cpp
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

> 현재 환경에 CycloneDDS 미설치 확인됨 — 설치 후 테스트 필요

### 내일 확인 순서

1. FastDDS XML 프로필 생성 → `FASTRTPS_DEFAULT_PROFILES_FILE` 설정
2. 기본 DDS 통신 테스트: `ros2 topic pub` + `ros2 topic echo` 성공 여부
3. 성공하면 → launch 재실행, 로봇 스폰 확인
4. 실패하면 → CycloneDDS 설치 후 `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` 테스트

## 참고

> 검증: `ros2 topic pub /test_topic ... --once` + `ros2 topic echo` — "Waiting for at least 1 matching subscription(s)..." 무한 반복으로 DDS 불능 확인  
> 검증: `ros_gz_sim 1.0.22` create.cpp:76 — `rclcpp::QoS(1).transient_local()` 사용 확인, QoS 불일치 아님  
> 검증: launch 로그 — `[ros_gz_sim]: Waiting messages on topic [robot_description].` 1초마다 반복, 종료 없음  
> 미검증: FastDDS XML 프로필 적용 후 통신 정상화 여부

- FastDDS 멀티캐스트 discovery는 네트워크 인터페이스 설정, 방화벽, 가상 네트워크(VMware/Docker) 등에 의해 방해받을 수 있음
- 이 이슈는 실제 로봇과 통신하는 경우가 아닌 **로컬 시뮬레이션 (단일 PC)** 에서 발생한 것
- Discovery Server(`ROS_DISCOVERY_SERVER`) 설정이 남아 있는 경우 Simple Discovery와 충돌할 수 있음 → `env | grep ROS` 로 확인
- 관련: [fastdds_and_discovery_server.md](../concepts/fastdds_and_discovery_server.md), [simple_discovery_ros_discovery_server_conflict.md](simple_discovery_ros_discovery_server_conflict.md)
