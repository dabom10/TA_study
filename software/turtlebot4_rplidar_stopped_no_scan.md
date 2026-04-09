# TurtleBot4 SLAM 실행 후 /scan 발행 없음 — RPLIDAR 자동 정지 상태

## 환경

- OS: Ubuntu 22.04 (호스트 PC), Ubuntu (TurtleBot4 Raspberry Pi)
- ROS2: Humble
- 로봇: TurtleBot4 Standard (namespace `/robot3`)
- 실행 명령: `ros2 launch turtlebot4_navigation slam.launch.py namespace:=/robot3`

## 문제 상황

- slam.launch.py 실행 시 slam_toolbox 노드 기동 로그는 출력됨
- `/robot3/map` 토픽이 생성되지 않음 (또는 생성돼도 데이터 없음)
- `ros2 topic info /robot3/scan` → `Publisher count: 0`
- `ros2 node list`에 robot3 노드들이 보이지 않는 경우도 있음

## 원인

### 주 원인: turtlebot4_node 센서 lifecycle 관리

`turtlebot4_node`는 배터리·도킹 상태에 따라 RPLIDAR와 OAKD를 자동으로 start/stop한다.

```
[turtlebot4_node-1] RPLIDAR stopped
[rplidar_composition-6] Ignoring stop_motor request because rplidar_node...
```

`rplidar_composition` 프로세스는 실행 중이지만 모터가 정지 상태라 스캔 데이터를 발행하지 않는다. 이 상태가 복구되지 않으면 `/robot3/scan` publisher count = 0이 된다.

| turtlebot4_node 상태 | RPLIDAR |
|---------------------|---------|
| 도킹 중 | 자동 stop |
| 언도킹 | 자동 start |
| 에러 상태 방치 | stop 후 복구 안 됨 |

### 부 원인: WiFi 환경 DDS discovery 불안정

`ros2 node list`에 robot3 노드가 보이지 않더라도 토픽 데이터는 흐를 수 있다.  
WiFi 멀티캐스트 환경에서 DDS participant 재등록이 안 되면 노드는 invisible, 토픽만 발견되는 현상이 발생한다.

## 진단 순서

1. scan 발행 여부 확인
   ```bash
   ros2 topic info /robot3/scan
   # Publisher count: 0 이면 RPLIDAR 정지 상태
   ```

2. robot3 bringup 서비스 상태 확인 (robot3에 SSH 접속 후)
   ```bash
   systemctl status turtlebot4
   # 로그에서 "RPLIDAR stopped" 메시지 확인
   ```

3. 도킹 상태 확인
   ```bash
   ros2 topic echo /robot3/dock_status
   ```

## 해결 방법

### 방법 1: turtlebot4 서비스 재시작 (robot3에서)

```bash
sudo systemctl restart turtlebot4
```

재시작 후 호스트 PC에서 확인:

```bash
ros2 topic hz /robot3/scan
```

### 방법 2: RPLIDAR 수동 start (robot3에서)

서비스 재시작 없이 모터만 켜기:

```bash
ros2 service call /robot3/start_motor std_srvs/srv/Empty
```

### 방법 3: 도킹 해제 후 실행

로봇이 도킹 중이면 언도킹 후 slam 실행.

## SLAM 실행 전 체크리스트

```bash
# 1. scan 데이터 발행 확인
ros2 topic hz /robot3/scan

# 2. TF 체인 확인 (slam_toolbox 필수 조건)
ros2 run tf2_ros tf2_echo robot3/odom robot3/base_link
```

두 항목 모두 정상이면 slam 실행.

## 참고

> 검증: `systemctl status turtlebot4` 로그 직접 확인 — 일치  
> 검증: `ros2 topic info /robot3/scan` Publisher count: 0 직접 확인 — 일치
