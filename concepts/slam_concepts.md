# SLAM 개념 정리: 2D LiDAR Framework & OGM vs Costmap

## SLAM이란?

**Simultaneous Localization and Mapping** — 로봇이 미지의 환경에서 지도를 만들면서 동시에 자신의 위치를 추정하는 기술. 카메라, LiDAR, IMU 등 다양한 센서를 활용.

---

## 2D LiDAR SLAM Framework

![2D LiDAR SLAM Framework](lidar_framework.png)

| 구성 요소 | 역할 |
|-----------|------|
| **LiDAR** | 주변 환경의 거리 데이터 제공 (2D 스캔) |
| **Front-end Odometer** | 연속 스캔 간 매칭(Frame to frame matching)으로 pose 추정 → 로봇이 지금 어디 있는지 |
| **Loop Detection** | 과거 방문 위치와 현재 위치를 비교해 누적 오차 감지 |
| **Back-end Optimization** | Loop 정보를 바탕으로 전체 경로 최적화 (Kalman filter / Particle filter / Graph optimization) |
| **Global Grid Map** | 최적화된 pose로 OGM(Occupancy Grid Map) 생성 |

### 전체 흐름
```
LiDAR → Front-end → Back-end → Loop Detection → Global Grid Map
              │ (Pose info)        ↑ (Subgraph info)
              └────────────────────┘
```

- **메인 흐름**: Front-end → Back-end → Loop Detection → Global Grid Map
- **Front-end**는 Back-end로 가는 동시에, Pose information을 Loop Detection에도 전달
- **Back-end**는 Subgraph information을 Loop Detection에 전달
- **Loop Detection**이 Map optimization을 수행해 Global Grid Map 생성

---

## SLAM 구성 요소 심화: 각 정보 흐름의 의미

### Pose Information (Front-end → Loop Detection)

Front-end는 연속 스캔 간 scan matching으로 현재 pose(x, y, θ)를 추정한다.  
이 **Pose Information**을 Loop Detection에 보내는 이유: 탐색 범위를 좁히기 위해.  
현재 위치를 모르면 과거 전체 그래프를 탐색해야 하지만, 알면 "반경 Xm 이내 subgraph만" 검색 가능.

### Pose Graph & Subgraph (Back-end)

Back-end는 Front-end의 pose 시퀀스를 **Pose Graph**로 관리한다.

```
노드 = 각 시점의 로봇 pose
엣지 = 노드 간 상대 변환 + 불확실도 (odometry에서 획득)

[pose0] --odom→ [pose1] --odom→ [pose2] --odom→ [pose3]
```

이 그래프를 공간적으로 묶은 것이 **Subgraph** (로컬로 일관성 있는 지도 조각).  
**Subgraph Information**은 Loop Detection이 과거 위치를 검색할 때 쓰는 DB.

### Map Optimization (Loop Detection → Global Grid Map)

Loop Detection이 루프를 확인하면 **loop edge**가 pose graph에 추가된다.

```
[pose0] --odom→ [pose1] --odom→ ... --odom→ [pose10]
   └─────────────── loop edge ───────────────────┘
```

Graph Optimization(SLAM Toolbox: Ceres Solver + Levenberg-Marquardt)이  
모든 edge constraint를 최대한 만족하는 pose 집합을 계산 → 오차가 전체 경로에 분산.  
보정된 pose로 Global Grid Map(OGM)을 재구성.

```
최적화 전: 오차가 경로 끝에 집중
최적화 후: 오차가 전체에 분산 흡수 → 지도가 닫힘
```

> 검증: [Graph SLAM: Theory to Implementation](https://federicosarrocco.com/blog/graph-slam-tutorial), [LiDAR/Visual SLAM Backend with Loop Closure](https://www.mdpi.com/2072-4292/13/14/2720) — front-end/back-end 역할 분리, subgraph 개념 일치

---

## OGM (Occupancy Grid Map) vs Costmap

### OGM — 원본 지도

![Occupancy Grid Map 예시](ogm_example.png)

SLAM이 생성하는 **환경 사실 지도**. 각 셀을 세 가지 상태로 기록.

| 값 | 의미 |
|----|------|
| `0` | 비어있음 (free) |
| `100` | 점유됨 (occupied) — 벽/장애물 |
| `-1` | 미탐색 (unknown) |

### Costmap — 판단용 지도

![Costmap 예시](costmap_example.png)

OGM을 가져와서 **"로봇이 여기를 지나가면 얼마나 위험한가"** 를 0~254 숫자로 계산한 지도. Nav2 경로 계획에 직접 사용.

| 값 | 의미 |
|----|------|
| `0` | 안전 |
| `~50` | 낮은 위험 |
| `~128` | 주의 |
| `~200` | 위험 |
| `253` | 치명적 |
| `254` | 장애물 (lethal) |

**Inflation Layer**: 벽/장애물 셀 주변을 일정 반경으로 팽창시켜 로봇이 벽 근처로 붙지 않도록 비용을 부여. 로봇 반경(footprint)을 반영한 안전 마진.

### 한 줄 비교

| | OGM | Costmap |
|--|-----|---------|
| **목적** | 환경 사실 기록 | 경로 계획용 위험도 계산 |
| **생성 주체** | SLAM | Nav2 (costmap_2d) |
| **값 범위** | 0 / 100 / -1 | 0 ~ 254 |
| **Inflation** | 없음 | 있음 |

---

## SLAM 실행 → 맵 파일 생성 흐름

### 전체 흐름

```
1. SLAM 노드 실행
        ↓
2. 로봇 센서 데이터 수집

   [Create3 내부]
   바퀴 엔코더 + IMU → 펌웨어가 내부 계산
     → /robot8/odom 토픽 publish
     → tf (odom → base_link) publish  ← slam_toolbox가 여기서 읽음

   [slam_toolbox가 직접 구독하는 것]
   /robot8/scan  (LiDAR)  → 직접 subscribe
   tf (odom → base_link)  → TF tree에서 읽음

   ※ /odom, /imu 토픽은 slam_toolbox가 직접 구독하지 않음
        ↓
3. slam_toolbox가 /robot8/map 토픽에 OccupancyGrid publish
   (Transient Local QoS — 마지막 맵 보존)
        ↓
4. Undock → teleop으로 돌아다니며 맵 확장
   (이동할수록 미탐색 영역이 채워짐)
        ↓
5. map_saver_cli 실행 → /robot8/map 토픽 수신
        ↓
6. 파일 저장
   first_map.yaml  (메타데이터)
   first_map.pgm   (흑백 이미지)
```

### 각 단계 상세

#### 1단계: SLAM 노드 실행
```bash
ros2 launch turtlebot4_navigation slam.launch.py namespace:=/robot8
```
이 시점부터 `/robot8/map` 토픽 생성됨.

#### 2단계: slam_toolbox 내부 처리
```
/scan 수신
  → TF(odom → base_link)로 로봇의 현재 예측 위치 파악
  → 예측 위치 기반으로 scan matching → 정확한 위치 보정
  → 루프 클로저: 이미 지나간 곳 다시 방문 시 오차 누적 보정
  → OccupancyGrid 업데이트 후 /map 토픽 publish
  → 보정된 위치를 /pose 로 publish
  → map → odom 변환을 tf로 publish (오차 보정량 반영)
```

#### 4단계: teleop으로 맵 확장
```
처음: 로봇 주변만 탐색 (작은 맵)
이동 후: [회색 미탐색] → [흰/검 탐색 완료]
```

#### 5단계: map_saver_cli
```bash
ros2 run nav2_map_server map_saver_cli -f "first_map" \
  --ros-args -p map_subscribe_transient_local:=true -r __ns:=/robot8
```
- Transient Local QoS로 구독 → 이미 발행된 최신 맵도 수신 가능
- `/robot8/map` 한 번 받아서 파일로 변환

#### 6단계: 생성 파일

**`first_map.yaml`** — 맵 메타데이터
```yaml
image: first_map.pgm
resolution: 0.05           # 1픽셀 = 5cm
origin: [-1.23, -2.34, 0]  # 맵 원점 (실제 좌표)
occupied_thresh: 0.65      # 이 값 이상이면 장애물
free_thresh: 0.25          # 이 값 이하면 빈 공간
```

**`first_map.pgm`** — 실제 지도 이미지
```
흰색 = 빈 공간 (0)
검은색 = 장애물 (100)
회색 = 미탐색 (-1)
```
두 파일은 항상 같은 디렉토리에 있어야 함 (yaml이 pgm을 참조).

---

## 참고

- ROS2 Nav2: `nav2_costmap_2d` 패키지가 OGM을 받아 costmap 생성
- global costmap: 전체 지도 기반 장기 경로 계획
- local costmap: 센서 실시간 데이터 기반 장애물 회피

---

## slam_toolbox 노드-토픽 구조

### 개념 구조

```
slam.launch.py
  └─ sync=true(기본) → sync_slam_toolbox_node
     sync=false       → async_slam_toolbox_node
     (둘 다 노드명은 /slam_toolbox 으로 동일)
```

| | sync | async |
|--|------|-------|
| 방식 | 모든 스캔 순서대로 처리 | 여유 있을 때만 처리 |
| 우선순위 | 지도 정확도 | 실시간 성능 |
| 용도 | 오프라인/정밀 매핑 | 실시간 주행 중 매핑 |

> 검증: [slam_toolbox ROS2 Humble 문서](https://docs.ros.org/en/humble/p/slam_toolbox/)

### 노드 Pub/Sub

```
Subscribers:
  /robot8/scan:   sensor_msgs/msg/LaserScan       ← LiDAR 데이터
  /robot8/map:    nav_msgs/msg/OccupancyGrid       ← localization 모드 대비 (mapping 모드에선 유휴)

Publishers:
  /robot8/map:          nav_msgs/msg/OccupancyGrid
  /robot8/map_metadata: nav_msgs/msg/MapMetaData
  /robot8/pose:         geometry_msgs/msg/PoseWithCovarianceStamped
  /robot8/tf:           tf2_msgs/msg/TFMessage

Services:
  /robot8/slam_toolbox/save_map
  /robot8/slam_toolbox/serialize_map
  /robot8/slam_toolbox/pause_new_measurements
  /robot8/slam_toolbox/toggle_interactive_mode
```

**/map을 pub/sub 둘 다 하는 이유:** mapping 모드와 localization 모드를 같은 코드가 지원. mapping 모드에서는 /map subscription이 열려있지만 실제로 소비하지 않음.

> 검증: [Nav2 Mapping and Localization](https://docs.nav2.org/setup_guides/sensors/mapping_localization.html)

### OccupancyGrid 메시지 구조

```
float32 resolution   # 셀 하나의 크기 (m). 예: 0.05 = 5cm/셀
uint32 width, height
geometry_msgs/Pose origin  # 지도 (0,0)이 실제 세계 어느 좌표인지
int8[] data          # 1차원 배열 (index = y * width + x)
  0   → free / -1 → unknown / 1~100 → occupied (확률적 표현)
```

> 검증: [nav_msgs/msg/OccupancyGrid](https://docs.ros.org/en/ros2_packages/humble/api/nav_msgs/msg/OccupancyGrid.html) — "values are application dependent"

### 중복 노드 WARNING 원인

```
WARNING: Be aware that there are nodes in the graph that share an exact name
```

RPi가 wlan0(WiFi)와 usb0(USB ethernet) 두 인터페이스로 DDS 광고 → PC DDS가 같은 노드를 두 경로로 수신 → 중복 표시. 실제로 노드가 2개인 게 아니며 기능 문제 없음.

> 검증: [create3_docs DDS discussion](https://github.com/iRobotEducation/create3_docs/discussions/17)

### remappings가 필요한 이유

slam_toolbox 기본 토픽명은 전역 경로(`/scan`, `/map`).  
`PushRosNamespace(robot8)` + remappings → `/robot8/scan`, `/robot8/map`으로 변환.

### 핵심 디버깅 명령어

```bash
ros2 node list
ros2 node info /robot8/slam_toolbox      # 노드 기준: pub/sub/service 목록
ros2 topic info /robot8/map              # 토픽 기준: 누가 pub/sub 하나
ros2 topic echo /robot8/map --once
ros2 interface show nav_msgs/msg/OccupancyGrid
rqt_graph                                # 전체 노드-토픽 그래프
ros2 pkg prefix turtlebot4_navigation    # 패키지 설치 경로
```
