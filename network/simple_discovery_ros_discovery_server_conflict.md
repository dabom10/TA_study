# Simple Discovery 설정 후 ros2 topic list 미출력

## 환경

- PC: Ubuntu, ROS 2 Jazzy, `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, `ROS_DOMAIN_ID=0`
- 로봇: TurtleBot4 (Raspberry Pi 4), ROS 2 Jazzy

## 문제 상황

Simple Discovery 가이드([simple_discovery.html](https://turtlebot.github.io/turtlebot4-user-manual/setup/simple_discovery.html)) 대로 PC 설정 완료 후 `ros2 topic list` 실행 시 아무것도 출력되지 않음.

- ping 정상
- multicast 정상 (`ros2 multicast send/receive` 양방향 확인)
- UFW 비활성
- 로봇 SSH 내부에서는 `/robot8/*` 토픽 정상 출력

## 원인

로봇의 `/etc/turtlebot4/setup.bash`에 아래 줄이 설정돼 있어 Simple Discovery가 아닌 **Discovery Server 모드**로 동작.

```bash
export ROS_DISCOVERY_SERVER="127.0.0.1:11811;"
```

discovery server가 로봇 localhost에만 열려 있어 PC에서 접근 불가. `ROS_SUPER_CLIENT=True`가 SSH 인터랙티브 터미널에만 적용돼 로봇 내부에서는 토픽이 보이는 것처럼 보임.

## 진단 순서

1. PC 환경변수 확인 → `RMW_IMPLEMENTATION`, `ROS_DOMAIN_ID` 정상
2. `ros2 multicast send/receive` 양방향 테스트 → 정상
3. 로봇 SSH 접속 후 `ros2 topic list` → 토픽 정상 출력 → PC ↔ 로봇 DDS 통신 문제 확인
4. 로봇 `printenv | grep -E "ROS|RMW|DOMAIN"` → `ROS_DISCOVERY_SERVER=127.0.0.1:11811` 발견
5. `/etc/turtlebot4/fastdds_rpi.xml` 확인 → Discovery Server 설정 없음, XML은 무관

## 해결 방법

로봇에서 `/etc/turtlebot4/setup.bash`의 `ROS_DISCOVERY_SERVER` 줄 삭제 후 재시작.

```bash
sudo nano /etc/turtlebot4/setup.bash
# 아래 줄 삭제:
# export ROS_DISCOVERY_SERVER="127.0.0.1:11811;"

sudo systemctl restart turtlebot4.service
# 또는
sudo reboot
```

## 참고

> 검증: https://turtlebot.github.io/turtlebot4-user-manual/setup/simple_discovery.html — 일치  
> 검증: 로봇 `/etc/turtlebot4/setup.bash` 직접 확인 — 원인 특정  
> 검증: 로봇 `/etc/turtlebot4/fastdds_rpi.xml` 직접 확인 — XML은 기본값, 무관

- Simple Discovery와 Discovery Server는 호환되지 않음 — 양쪽 RMW 모드가 일치해야 함
- TurtleBot4 Jazzy 기본 이미지는 Discovery Server 모드로 출하되는 경우 있음
