# Jazzy 업데이트 후 dock 상태에서 RPLIDAR 미회전

## 환경

- OS: Ubuntu 24.04 (호스트 PC), TurtleBot4 Raspberry Pi (Jazzy)
- ROS2: Jazzy
- 패키지: turtlebot4_node, rplidar_ros

## 문제 상황

Humble → Jazzy 업데이트 이후, 네비게이션 실행 시 `/scan` 토픽 미발행 → localization(AMCL) 동작 불가.

실제 원인은 두 가지가 겹쳐서 발생:
1. Jazzy에서 `power_saver` 기본값이 `true` → dock 상태에서 RPLIDAR 자동 정지 (설계 의도)
2. 네비게이션 스크립트의 조건 버그 → undock이 수행되지 않아 로봇이 dock 상태 유지

## 원인

### power_saver=true: dock 상태 RPLIDAR 정지 (설계 의도)

> 검증: [turtlebot4_node/src/turtlebot4.cpp (jazzy branch)](https://github.com/turtlebot/turtlebot4/blob/jazzy/turtlebot4_node/src/turtlebot4.cpp) — 소스 코드 직접 확인

`power_saver` 파라미터 기본값이 `true`이며, `dock_status_callback`에서 RPLIDAR 제어를 담당.

```cpp
if (dock_status_msg->is_docked != is_docked_ && power_saver_) {
  if (dock_status_msg->is_docked) {
    rplidar_stop_function_callback();   // dock 시 RPLIDAR 정지
  } else {
    rplidar_start_function_callback();  // undock 시 RPLIDAR 시작
  }
}
```

dock 상태에서 RPLIDAR를 정지하는 것은 효율적인 설계 선택: dock 중에는 위치 추정 외에 RPLIDAR로 할 수 있는 작업이 없기 때문.

**Humble과 Jazzy 간 동작 차이의 원인: `power_saver` 파라미터 값**

| | Humble 로봇 | Jazzy 로봇 |
|---|---|---|
| `power_saver` 값 | `false` (구버전 기본값) | `true` (기본값) |
| dock 상태 RPLIDAR | 회전 지속, `/scan` 발행 | 즉시 중지 |
| undock 후 RPLIDAR | 항상 동작 중 | undock 전환 시 시작 |

- `power_saver: false`이면 `dock_status_callback` 조건(`&& power_saver_`)이 false → RPLIDAR 제어 없음
- turtlebot4_node 코드 자체는 Humble과 동일한 구조, Jazzy에서 변경된 것 없음

> 검증: [humble/turtlebot4.cpp](https://raw.githubusercontent.com/turtlebot/turtlebot4/humble/turtlebot4_node/src/turtlebot4.cpp), [jazzy/turtlebot4.cpp](https://raw.githubusercontent.com/turtlebot/turtlebot4/jazzy/turtlebot4_node/src/turtlebot4.cpp) — `dock_status_callback` 코드 동일 확인

> 미검증: Humble 로봇 `/etc/turtlebot4/` config 실제 파일 내용 — 웹으로 확인 불가 (robot-specific)

### RPLIDAR 시작 조건: 상태 전환 시점

RPLIDAR 시작은 dock → undock **상태 변화** 시점에만 발생. 노드 init 시에는 실행되지 않음.

→ 로봇이 dock 상태인 채로 turtlebot4_node가 기동되고 undock이 수행되지 않으면, RPLIDAR 시작 명령이 전달되지 않음.

### 네비게이션 스크립트 조건 버그

```python
# 버그: is_docked==False일 때 undock() 호출 → dock 상태 로봇은 그대로
if not navigator.getDockedStatus():
    navigator.undock()
```

`not`이 붙어 있어 실제로는 이미 undock된 상태에서 undock()을 호출하고, dock 상태에서는 아무것도 하지 않음.  
결과적으로 로봇이 dock 상태 유지 → RPLIDAR 미시작.

## 진단 순서

```bash
# 1. dock 상태 확인
ros2 topic echo /robot8/dock_status --once

# 2. RPLIDAR 토픽 확인
ros2 topic hz /robot8/scan

# 3. turtlebot4_node 상태 확인
ros2 node info /robot8/turtlebot4_node
```

## 해결 방법

`3_1_a_nav_to_pose.py`의 조건 버그 수정:

```python
# 수정 전 (버그)
if not navigator.getDockedStatus():
    navigator.undock()

# 수정 후: dock 상태일 때만 undock → dock→undock 전환 → RPLIDAR 시작
if navigator.getDockedStatus():
    navigator.undock()
```

이후 실행 흐름:
1. dock 상태 → `undock()` → RPLIDAR 시작 → `/scan` 발행
2. 이미 undocked → skip
3. `setInitialPose()` → `waitUntilNav2Active()` → `startToPose()`

## 참고

- 동일 증상(Humble, SLAM 도중 정지): [turtlebot4_rplidar_stopped_no_scan.md](turtlebot4_rplidar_stopped_no_scan.md)
- Jazzy turtlebot4_node 동작 변경 관련 공식 문서: 해당 없음 — 코드 변경 자체가 없으므로 문서도 없음. 동작 차이는 `power_saver` 파라미터 값 차이에서 기인
