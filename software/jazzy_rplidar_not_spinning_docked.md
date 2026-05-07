# Jazzy 업데이트 후 dock 상태에서 RPLIDAR 미회전

## 환경

- OS: Ubuntu 24.04 (호스트 PC), TurtleBot4 Raspberry Pi (Jazzy)
- ROS2: Jazzy
- 패키지: turtlebot4_node, rplidar_ros

## 상황

Humble에서는 dock 여부와 무관하게 계속 회전하고, 절전 모드에서만 정지했음.
Jazzy로 업데이트한 이후에는 dock 상태에서 자동 정지, undock 상태에서만 회전.

동작 차이가 궁금해서 원인 분석. 에러 아님.

## 원인

### power_saver=true: dock 상태 RPLIDAR 정지 (설계 의도)

> 검증: [turtlebot4_node/src/turtlebot4.cpp (jazzy branch)](https://github.com/turtlebot/turtlebot4/blob/jazzy/turtlebot4_node/src/turtlebot4.cpp) — 소스 코드 직접 확인

`power_saver` 파라미터 기본값이 `true`이며, `dock_status_callback`에서 RPLIDAR 제어를 담당.

```cpp
if (dock_status_msg->is_docked != is_docked_ && power_saver_) {
  if (dock_status_msg->is_docked) {
    oakd_stop_function_callback();
    rplidar_stop_function_callback();
  } else {
    oakd_start_function_callback();
    rplidar_start_function_callback();
  }
  is_docked_ = dock_status_msg->is_docked;
}
```

dock 상태에서 RPLIDAR를 정지하는 것은 효율적인 설계 선택: dock 중에는 위치 추정 외에 RPLIDAR로 할 수 있는 작업이 없기 때문.

**Humble과 Jazzy 간 동작 차이**

| | Humble 로봇 | Jazzy 로봇 |
|---|---|---|
| `power_saver` 코드 기본값 | `true` (소스 동일) | `true` (기본값) |
| dock 상태 RPLIDAR | 계속 회전 (dock 무관) | 즉시 중지 |
| undock 후 RPLIDAR | 계속 회전 유지 | undock 전환 시 시작 |
| 절전 모드 | 정지 | — (dock 시 정지로 대체) |

- 코드 기본값은 두 브랜치 모두 `true`로 동일
- Humble 로봇에서 dock 무관 계속 회전했던 것은 `/etc/turtlebot4/` config 파일에서 `power_saver: false`로 override되었거나 구버전 패키지 사용 가능성 있음 (직접 관찰, config 파일 미확인)
- turtlebot4_node 코드 자체는 Humble과 동일한 구조

> 검증: [직접 관찰] Humble 로봇 — dock/undock 무관 계속 회전, 절전 모드에서만 정지

> 검증: [humble/turtlebot4.cpp](https://raw.githubusercontent.com/turtlebot/turtlebot4/humble/turtlebot4_node/src/turtlebot4.cpp), [jazzy/turtlebot4.cpp](https://raw.githubusercontent.com/turtlebot/turtlebot4/jazzy/turtlebot4_node/src/turtlebot4.cpp) — `declare_parameter("power_saver", true)` 및 `dock_status_callback` 코드 양쪽 동일 확인

> 미검증: Humble 로봇 `/etc/turtlebot4/` config 실제 파일 내용, 설치된 turtlebot4_node 버전 — robot-specific

### RPLIDAR 시작 조건: 상태 전환 시점

RPLIDAR 시작은 dock → undock **상태 변화** 시점에만 발생. 노드 init 시에는 실행되지 않음.

→ 로봇이 dock 상태인 채로 turtlebot4_node가 기동되고 undock이 수행되지 않으면, RPLIDAR 시작 명령이 전달되지 않음.

## dock 상태 무관 nav to goal 확인

RPLIDAR가 undock 전환 시점에만 시작되므로, nav to goal 스크립트 시작 시 dock 상태이면 명시적으로 undock 해줘야 RPLIDAR가 시작됨.

```python
# dock 상태일 때만 undock → dock→undock 전환 → RPLIDAR 시작
# 이미 undocked이면 skip
if navigator.getDockedStatus():
    navigator.undock()
```

실행 흐름:
1. dock 상태 → `undock()` → RPLIDAR 시작 → `/scan` 발행
2. 이미 undocked → skip
3. `setInitialPose()` → `waitUntilNav2Active()` → `startToPose()`

이 패턴으로 시작 dock 상태와 무관하게 nav to goal 동작 확인.

## 참고

- Jazzy turtlebot4_node 동작 변경 관련 공식 문서: 해당 없음 — 코드 변경 자체가 없으므로 문서도 없음. 동작 차이는 `power_saver` 파라미터 및 config 값 차이에서 기인
