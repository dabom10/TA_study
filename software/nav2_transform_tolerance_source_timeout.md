# nav2 transform_tolerance / source_timeout 설정 오류

## 환경

- OS: Ubuntu 24.04
- ROS2: Jazzy
- 로봇: TurtleBot4 (RPLidar, namespace `/robot8`)
- 구성: PC(Nav2, RViz2) + 로봇 Pi(scan 발행) — 멀티 머신

## 문제 상황

Nav2 goal을 RViz2에서 주면 즉시 abort됨.

```
[collision_monitor-9] [WARN]: [scan]: Latest source and current collision monitor node
    timestamps differ on 1.238393 seconds. Ignoring the source.
[collision_monitor-9] [ERROR]: Failed to get "rplidar_link"->"base_link" frame transform:
    Lookup would require extrapolation into the future.
    Requested time 1778552011.205627 but the latest data is at time 1778552011.071017,
    when looking up transform from frame [odom] to frame [base_link]
[planner_server-3] [INFO]: Message Filter dropping message: frame 'rplidar_link'
    at time 1778552059.230 for reason 'the timestamp on the message is earlier than
    all the data in the transform cache'
```

## 원인

두 가지 원인이 복합적으로 작용.

### 원인 1 — transform_tolerance 부족

> 검증: `nav2_mppi_controller/src/path_handler.cpp` L39, L157 — `transform_tolerance`를 tf_buffer::transform() 호출 시 timeout으로 직접 전달  
> 검증: `nav2_behaviors/src/behavior_server.cpp` L70 — 동일  
> 검증: `nav2_costmap_2d/src/costmap_2d_ros.cpp` L131 — costmap 기본값 0.3s  
> 검증: `nav2_collision_monitor/src/collision_monitor_node.cpp` L265 — collision_monitor 기본값 0.1s

`transform_tolerance`는 TF lookup 시 허용하는 시간 오차다. 노드가 타임스탬프 T인 데이터를 처리할 때, TF 버퍼에서 시각 T의 변환을 찾지 못하면 `±transform_tolerance` 범위 내 가장 가까운 것을 사용한다. 범위를 벗어나면 "extrapolation into the future" 또는 "earlier than all data" 에러가 발생한다.

실제 측정값:
- PC ↔ 로봇 클럭 차이: **0.21s** (`date +%s.%N` 비교)
- `odom → base_link` TF lag: **0.13s** (에러 로그: 1778552011.205627 − 1778552011.071017)
- **최소 필요 tolerance: 0.21 + 0.13 = 0.34s**

기존 설정값이 모두 0.34s보다 작아서 TF lookup이 실패함:

| 위치 | 기존 값 | 최소 필요 |
|------|---------|-----------|
| MPPI controller (FollowPath) | 0.1s | 0.34s |
| behavior_server | 0.1s | 0.34s |
| collision_monitor | 0.2s | 0.34s |
| local_costmap (기본값 사용) | 0.3s | 0.34s |
| global_costmap (기본값 사용) | 0.3s | 0.34s |

### 원인 2 — source_timeout 부족

> 검증: `nav2_collision_monitor/src/source.cpp` L86-93 — `curr_time - source_time > source_timeout_` 이면 scan 무시하고 WARN 출력  
> 검증: `nav2_collision_monitor/src/collision_monitor_node.cpp` L244 — upstream 기본값 `2.0s`

`source_timeout`은 collision_monitor가 센서 데이터를 "유효"로 판단하는 최대 경과 시간이다. 센서 데이터의 타임스탬프와 collision_monitor의 현재 시각 차이가 이 값을 초과하면 해당 소스를 무시한다.

DDS 초기 연결 시 버퍼링된 scan 메시지가 지연 도착하면서 1.238s 차이 발생 → `source_timeout: 1.0`(< 1.238s) 초과 → scan 전체 무시 → costmap 업데이트 안 됨 → 경로 계획 실패.

## 해결 방법

`~/turtlebot4/turtlebot4_navigation/config/nav2.yaml` 수정:

### transform_tolerance (5곳)

측정값 기반 계산: `0.21(클럭차) + 0.13(TF lag) + 0.16(여유) = 0.5s`

```yaml
# MPPI controller (FollowPath 플러그인 내부)
FollowPath:
  transform_tolerance: 0.5   # 0.1 → 0.5

# behavior_server
behavior_server:
  ros__parameters:
    transform_tolerance: 0.5  # 0.1 → 0.5

# collision_monitor
collision_monitor:
  ros__parameters:
    transform_tolerance: 0.5  # 0.2 → 0.5

# local_costmap (기존 yaml에 없었음 → 기본값 0.3s 사용 중)
local_costmap:
  local_costmap:
    ros__parameters:
      transform_tolerance: 0.5  # 추가

# global_costmap (동일)
global_costmap:
  global_costmap:
    ros__parameters:
      transform_tolerance: 0.5  # 추가
```

### source_timeout

upstream 기본값(2.0s)으로 복원. DDS 초기 지연 및 클럭 차이 모두 커버.

```yaml
collision_monitor:
  ros__parameters:
    source_timeout: 2.0  # 1.0 → 2.0
```

## 진단 순서

```bash
# 1. 클럭 차이 측정 (로봇과 PC에서 각각 실행)
date +%s.%N

# 2. scan 수신 여부 확인
ros2 topic hz /robot8/scan

# 3. TF map→odom 존재 확인
ros2 run tf2_ros tf2_echo map odom

# 4. collision_monitor가 scan을 받는지 확인
ros2 topic echo /robot8/collision_monitor_state
```

## 참고

- Nav2 공식 문서: https://docs.nav2.org/configuration/packages/configuring-collision-monitor.html
- 소스 검증 파일:
  - `nav2_collision_monitor/src/source.cpp` — source_timeout 판정 로직
  - `nav2_collision_monitor/src/collision_monitor_node.cpp` — 파라미터 선언 및 기본값
  - `nav2_mppi_controller/src/path_handler.cpp` — transform_tolerance 사용 방식
  - `nav2_costmap_2d/src/costmap_2d_ros.cpp` — costmap 기본값 0.3s
