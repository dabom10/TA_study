# slam_toolbox 노드-토픽 관계 실습 검증

## 개념 구조

```
slam.launch.py
  └─ sync=true(기본) → sync_slam_toolbox_node 실행
     sync=false       → async_slam_toolbox_node 실행
     (둘 다 노드명은 /slam_toolbox 으로 동일)
          │
          ├─ Subscribe: /scan (LiDAR), /tf, /tf_static, /map (localization 모드용)
          └─ Publish:   /map, /map_metadata, /pose, /tf, 시각화 토픽들
```

---

## 실습 검증 결과

### Step 1-2: 런치 전후 노드 비교

**slam 런치 후 새로 생긴 노드:**
- `/robot8/slam_toolbox` ← 핵심 노드
- `/robot8/transform_listener_impl_63f374001b20` ← slam_toolbox 내부가 자동 생성한 TF 리스너

> **transform_listener_impl 자동 생성 이유**
> `TransformListener` 생성 시 `spin_thread=true`(기본값)로 인해
> /tf 토픽 구독 전용 내부 노드와 스레드가 자동으로 만들어짐.
> 출처: [geometry2 issue #361](https://github.com/ros2/geometry2/issues/361)

---

### Step 3: ros2 node info /robot8/slam_toolbox

```
Subscribers:
  /robot8/map:              nav_msgs/msg/OccupancyGrid   ← localization 모드 대비
  /robot8/scan:             sensor_msgs/msg/LaserScan    ← LiDAR 데이터 수신
  /robot8/slam_toolbox/feedback: visualization_msgs/...  ← rviz 인터랙션

Publishers:
  /robot8/map:              nav_msgs/msg/OccupancyGrid   ← 생성한 지도 발행
  /robot8/map_metadata:     nav_msgs/msg/MapMetaData
  /robot8/pose:             geometry_msgs/msg/PoseWithCovarianceStamped
  /robot8/tf:               tf2_msgs/msg/TFMessage
  /robot8/slam_toolbox/graph_visualization: MarkerArray
  /robot8/slam_toolbox/scan_visualization:  LaserScan

Service Servers (주요):
  /robot8/slam_toolbox/save_map
  /robot8/slam_toolbox/serialize_map
  /robot8/slam_toolbox/dynamic_map
  /robot8/slam_toolbox/pause_new_measurements
  /robot8/slam_toolbox/toggle_interactive_mode
```

---

### Step 4: ros2 topic info /robot8/map

```
Publisher count: 1     ← slam_toolbox
Subscription count: 1  ← slam_toolbox 자신 (rviz2 꺼져있을 때)
Subscription count: 2  ← slam_toolbox + rviz2 (rviz2 켜면)
```

> **확인 방법:**
> - `ros2 node info /노드명` → 노드 기준 (이 노드가 무엇을 pub/sub하나)
> - `ros2 topic info /토픽명` → 토픽 기준 (이 토픽을 누가 pub/sub하나)
> 두 명령어는 반대 방향으로 같은 관계를 보는 것

---

### Step 5: /map을 동시에 pub/sub하는 이유

slam_toolbox는 **모드에 따라** 다른 동작을 함:

| 모드 | /map Subscribe | /map Publish |
|------|---------------|-------------|
| Mapping 모드 | 사용 안 함 (열려있지만 유휴) | 새로 만든 지도 발행 |
| Localization 모드 | 기존 저장된 지도 수신 | 현재 상태 지도 발행 |

같은 노드 코드가 두 모드를 모두 지원하므로 subscription이 항상 열려있음.
rqt_graph에서 자기 자신에 화살표가 도는 것처럼 보이지만, mapping 모드에서는 실제로 자기 데이터를 자기가 소비하는 게 아님.

출처: [Nav2 Mapping and Localization](https://docs.nav2.org/setup_guides/sensors/mapping_localization.html)

---

### Step 6: OccupancyGrid 메시지 구조

```
float32 resolution   # 셀 하나의 크기 (m). 예: 0.05 = 5cm/셀
uint32 width         # 가로 셀 수
uint32 height        # 세로 셀 수
geometry_msgs/Pose origin  # 지도 (0,0)이 실제 세계 어느 좌표인지
int8[] data          # 1차원 배열로 저장된 2D 격자
```

**data 값 (기본값, application dependent):**
```
 0   → free (이동 가능)
-1   → unknown (미탐색)
 1   → occupied (장애물)
```

> nav_msgs 공식 문서에는 `0, 1, -1`이 기본값이나 "values are application dependent"로 명시.
> slam_toolbox 등 구현체에 따라 1-100 범위로 확률적으로 표현하기도 함.
> 출처: [nav_msgs/msg/OccupancyGrid](https://docs.ros.org/en/ros2_packages/humble/api/nav_msgs/msg/OccupancyGrid.html)

**셀 좌표 → 배열 인덱스:**
```
index = y * width + x
```

---

### Step 7: 중복 노드 원인 (ros2 node list WARNING)

```
WARNING: Be aware that there are nodes in the graph that share an exact name
```

**원인:** TurtleBot4 RPi가 다중 네트워크 인터페이스를 가짐
```
RPi
├── wlan0 (WiFi)
└── usb0  (USB ethernet → Create3)
```
RPi가 두 인터페이스로 DDS 광고 → PC DDS가 같은 노드를 두 경로로 수신 → 중복 표시

- PC 쪽 인터페이스 문제가 아님 (PC는 WiFi 하나만 활성)
- 실제로 노드가 2개 실행 중인 게 아님
- 기능에 문제없음

출처: [create3_docs DDS discussion](https://github.com/iRobotEducation/create3_docs/discussions/17)

---

### Step 8: 런치파일 분석

```python
# slam.launch.py 핵심 구조

Node(package='slam_toolbox',
     executable='sync_slam_toolbox_node',  # sync=true (기본값)
     name='slam_toolbox',
     condition=IfCondition(sync))

Node(package='slam_toolbox',
     executable='async_slam_toolbox_node', # sync=false
     name='slam_toolbox',
     condition=UnlessCondition(sync))

remappings = [
    ('/tf', 'tf'), ('/scan', 'scan'), ('/map', 'map'), ...
]
```

**sync vs async 차이:**

| | sync | async |
|--|------|-------|
| 방식 | 모든 스캔 순서대로 처리 | 여유 있을 때만 처리 |
| 우선순위 | 지도 정확도 | 실시간 성능 |
| 용도 | 오프라인/정밀 매핑 | 실시간 주행 중 매핑 |

출처: [slam_toolbox ROS2 Humble 문서](https://docs.ros.org/en/humble/p/slam_toolbox/)

**remappings가 필요한 이유:**
slam_toolbox 기본 토픽명은 전역 경로(`/scan`, `/map`).
`PushRosNamespace(robot8)` + remappings로 `/robot8/scan`, `/robot8/map`으로 변환.
→ `ros2 node info`에서 `/robot8/scan`으로 보인 이유.

---

## 핵심 명령어 정리

```bash
# 노드 목록
ros2 node list

# 노드 기준: 이 노드가 무엇을 pub/sub/service 하나
ros2 node info /robot8/slam_toolbox

# 토픽 기준: 이 토픽을 누가 pub/sub 하나
ros2 topic info /robot8/map

# 토픽 실제 데이터 확인
ros2 topic echo /robot8/map --once

# 메시지 타입 구조 확인
ros2 interface show nav_msgs/msg/OccupancyGrid

# 전체 노드-토픽 그래프 시각화
rqt_graph

# 패키지 설치 경로 찾기
ros2 pkg prefix turtlebot4_navigation
```
