# Jazzy 업데이트 후 undock 상태에서 RPLIDAR 미회전

## 환경

- OS: Ubuntu 24.04 (호스트 PC), TurtleBot4 Raspberry Pi (Jazzy)
- ROS2: Jazzy
- 패키지: turtlebot4_node, rplidar_ros

## 문제 상황

Humble → Jazzy 업데이트 이후, 로봇이 undock 상태일 때 RPLIDAR가 회전하지 않음.
결과적으로 `/scan` 토픽 미발행 → localization(AMCL) 동작 불가.

## 원인

> 검증: [turtlebot4_node/src/turtlebot4.cpp (jazzy branch)](https://github.com/turtlebot/turtlebot4/blob/jazzy/turtlebot4_node/src/turtlebot4.cpp) — 소스 코드 직접 확인

`power_saver` 파라미터 기본값이 `true`이며, `dock_status_callback`에서 RPLIDAR 제어를 담당.

```cpp
// dock_status_callback 핵심 로직
if (dock_status_msg->is_docked != is_docked_ && power_saver_) {
  if (dock_status_msg->is_docked) {
    rplidar_stop_function_callback();
  } else {
    rplidar_start_function_callback();   // ← undock 전환 시점에만 실행
  }
}
```

**핵심:** RPLIDAR 시작은 dock → undock **상태 변화** 시점에만 발생.  
노드 초기화(init) 시에는 실행되지 않는다.

→ 로봇이 **이미 undock 상태**에서 `turtlebot4_node`가 기동되면:  
`is_docked_` 초기값과 실제 상태 간 변화가 없으므로 콜백이 RPLIDAR 시작 명령을 보내지 않음.

이 동작은 Humble과 동일한 코드 구조이며, Jazzy에서 새로 변경된 것이 아님.  
**undock 상태에서 재부팅하면** 재현되는 구조적 특성.

## 진단 순서

```bash
# 1. dock 상태 확인
ros2 topic echo /robot8/dock_status --once

# 2. RPLIDAR 토픽 확인 (scan이 발행되는지)
ros2 topic hz /robot8/scan

# 3. turtlebot4_node 상태 확인
ros2 node info /robot8/turtlebot4_node
```

## 해결 방법

`3_1_a_nav_to_pose.py`의 조건 버그 수정 — dock 상태일 때만 undock 호출:

```python
# 수정 전 (버그): 이미 undocked 상태에서 undock() 재호출, dock 상태는 그대로
if not navigator.getDockedStatus():
    navigator.undock()

# 수정 후: dock 상태일 때만 undock → dock→undock 전환 → RPLIDAR 시작
if navigator.getDockedStatus():
    navigator.undock()
```

이후 실행 흐름:
1. dock 상태 → `undock()` → RPLIDAR 시작 → `/scan` 발행
2. already undocked → skip (RPLIDAR 이미 동작 중 전제)
3. `setInitialPose()` → `waitUntilNav2Active()` → `startToPose()`

dock/undock 상태 무관하게 정상 동작.

## 참고

- 동일 증상(Humble, SLAM 도중 정지): [turtlebot4_rplidar_stopped_no_scan.md](turtlebot4_rplidar_stopped_no_scan.md)
- Jazzy turtlebot4_node 동작 변경 관련 공식 문서: 미확인
