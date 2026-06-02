# TurtleBot4 Navigation 설정 학습 정리 (localization / nav2 / slam)

> `turtlebot4_navigation` 패키지(**Humble**)의 위치추정 · SLAM · 자율주행 설정 총정리.
> 대상 파일: `config/localization.yaml`, `config/nav2.yaml`, `config/slam.yaml`

> 검증: `origin/humble:turtlebot4_navigation/config/localization.yaml` — 일치 (max/min_particles 2000/500, alpha 0.2, update_min_d/a 0.25/0.2, laser_model_type likelihood_field, recovery_alpha 0.0, tf_broadcast true, free/occupied_thresh 0.25/0.65, use_sim_time True)
> 검증: `origin/humble:turtlebot4_navigation/config/nav2.yaml` — 일치 (max_vel_x 0.26, max_vel_theta 1.0, sim_time 1.7, vx/vtheta_samples 20, PathDist/PathAlign/RotateToGoal.scale 32, GoalDist/GoalAlign.scale 24, BaseObstacle.scale 0.02, inflation_radius 0.45, cost_scaling_factor 4.0, robot_radius 0.175, local 3×3m, update_freq global 1.0/local 5.0, xy_goal_tolerance 0.25, progress_checker 0.5m/10s, NavfnPlanner use_astar false)
> 검증: `origin/humble:turtlebot4_navigation/config/slam.yaml` — 일치 (solver CeresSolver, mode mapping, resolution 0.05, max_laser_range 12.0, minimum_travel_distance/heading 0.0, use_scan_matching true, do_loop_closing true, loop_match_minimum_response_fine 0.45)
> 검증: `origin/humble:turtlebot4_navigation/launch/slam.launch.py` — 일치 (`sync` 인자 default_value='true' → sync_slam_toolbox_node가 기본)

> 관련 개념 파일(중복 작성 대신 링크):
> [[nav2_amcl_tf_tree]] — map·odom·base_link TF 트리, AMCL의 `map→odom` 발행 / [[slam_concepts]] — 2D LiDAR SLAM 프레임워크, OGM vs Costmap / [[loop_detection_and_closure]] — Loop Detection vs Closure 구분 / [[nav2_map_switching]] — 런타임 멀티맵 교체(`load_map`)

---

## 0. 전체 그림 — 세 단계, 세 쌍의 파일

내비게이션은 크게 **3단계**로 나뉘고, 각 단계마다 **launch(켜기) + yaml(설정)** 한 쌍이 있다.

```
① 지도 만들기   slam.launch.py         + slam.yaml          → slam_toolbox
② 위치추정      localization.launch.py + localization.yaml  → amcl + map_server
③ 경로계획·주행  (nav2 launch)          + nav2.yaml          → planner/controller/...
```

```
[처음 - 새 공간 탐색]
  slam_toolbox ─── 지도 그리며 주행 ───▶ map_saver로 .pgm 저장
                                              │
[이후 - 실제 운영]                            ▼
  amcl ◀──── 저장된 지도 로드 ──── map_server
    │ map→odom TF
    ▼
  nav2 (planner+controller+costmap) ──── 목표까지 자율주행
```

> ⚠️ **SLAM과 AMCL은 동시에 켜지 않는다.** 둘 다 `map→odom` TF를 발행하므로 충돌한다.
> (TF 트리 구조는 [[nav2_amcl_tf_tree]] 참고)

---

## 1. localization.yaml — 위치추정 (운영 단계)

### 노드 역할

| 노드 | 역할 |
|------|------|
| **amcl** | 저장된 지도 위에서 "내 위치" 추정. `map→odom` TF 발행 |
| **map_server** | 디스크의 지도(.pgm/.yaml)를 읽어 `/map`으로 발행 |
| **map_saver** | 현재 `/map`을 파일로 저장 (SLAM 후 지도 저장용) |

### AMCL 핵심 원리 (파티클 필터)

AMCL = **A**daptive **M**onte **C**arlo **L**ocalization. 위치를 하나로 정하지 않고
**수백~수천 개의 위치 후보(파티클)** 를 동시에 들고 다닌다.

한 사이클:
1. 로봇 이동 → 모든 파티클을 같이 이동 (+ 노이즈로 흩뿌림) ← `alpha1~5`
2. 라이다 스캔 도착 → 각 파티클에서 "스캔이 지도와 맞나" 채점 ← `z_*`
3. 리샘플링 → 점수 높은 파티클 복제, 낮은 건 삭제 → 진짜 위치로 수렴

> **RViz에 뜨는 화살표 구름이 곧 파티클.** 넓게 퍼지면 불확실, 한 점에 뭉치면 위치 확신.
> "2D Pose Estimate" 버튼 = 파티클을 그 위치로 모으는 동작.

### 꼭 아는 파라미터

| 파라미터 | 값 | 핵심 |
|----------|-----|------|
| `use_sim_time` | True | **실로봇은 반드시 False!** 안 바꾸면 TF 어긋나 위치추정 멈춤 (최대 실수) |
| `tf_broadcast` | true | `map→odom` 발행 스위치. 끄면 결과 전파 안 됨 |
| `max/min_particles` | 2000/500 | 파티클 수 = 정확도↔CPU 트레이드오프 |
| `alpha1~5` | 0.2 | 오도메트리 노이즈. 휠 불신도. 미끄러우면 키움 |
| `update_min_d/a` | 0.25m/0.2rad | 이만큼 움직여야 필터 갱신 |
| `laser_model_type` | likelihood_field | 빠르고 일반적(권장) vs beam(정밀·무거움) |
| `recovery_alpha_slow/fast` | 0.0 (끔) | 납치 복구. 켜려면 slow≈0.001, fast≈0.1 |

**센서 모델 가중치 z_*** : `z_hit: 0.5`(벽에 정확히 맞음) / `z_rand: 0.5`(노이즈) /
`z_short: 0.05`(동적 장애물) / `z_max: 0.05`(측정 실패). 사람 많으면 `z_short` 키움.

### map_saver 임계값 (점유격자 3색 분류)
- `free_thresh 0.25` 미만 → 자유공간(흰색)
- `occupied_thresh 0.65` 초과 → 장애물(검정)
- 그 사이 → 미지영역(회색)

---

## 2. nav2.yaml — 경로계획 · 주행

### 데이터 흐름

```
goal → bt_navigator(지휘자)
         │① 경로 짜줘
         ▼
       planner_server ◀── global_costmap (지도 전체, map 기준)
         │ 경로
         ▼
       smoother_server (각진 경로 부드럽게)
         │② 따라가
         ▼
       controller_server ◀── local_costmap (주변 3×3m, odom 기준)
         │ cmd_vel
         ▼
       velocity_smoother → 바퀴

   막히면 → behavior_server (회전/후진/대기) → 재계획
```

**한 문장 정리:**
- **planner** = 큰 그림 길찾기 (지도 전체, 가끔 = 내비 경로선)
- **controller** = 실제 핸들·엑셀 조작 (주변만, 20Hz = 운전자)
- **bt_navigator** = 둘을 언제 부를지 정하는 지휘자 (Behavior Tree)

### 코스트맵 (가장 핵심 개념)

지도 각 셀에 "지나가면 얼마나 위험한가"를 0~254로 칠한 것.
(OGM과 Costmap의 차이는 [[slam_concepts]] 참고)

| | global_costmap | local_costmap |
|---|---|---|
| 범위 | 지도 전체 | 주변 3×3m |
| 기준 | map | odom |
| 갱신 | 1Hz | 5Hz |
| 사용 | planner | controller |
| 장애물 레이어 | obstacle_layer | voxel_layer |

> 공통: `robot_radius: 0.175`, `resolution: 0.06`.

**레이어 합성** (아래→위): `static_layer`(저장 지도) → `obstacle/voxel_layer`(실시간 장애물) → `inflation_layer`(위험 그라데이션)

#### ★ 가장 많이 튜닝: inflation
- `inflation_radius: 0.45` = 장애물에서 위험을 퍼뜨리는 **반경**(어디까지).
  좁은 문 못 지나면 ↓, 벽에 너무 붙으면 ↑
- `cost_scaling_factor: 4.0` = 그 안에서 비용이 떨어지는 **기울기**(얼마나 급하게).
  크면 벽에 바짝 붙음, 작으면 멀찍이 돌음

```
cost
254┤█╲  ← 벽
   │  ╲___      ← 기울기 = cost_scaling_factor
  0┤      ╲____ ← inflation_radius 밖은 0
   └──────────▶ 벽으로부터 거리
```

### controller — DWB 지역 플래너

전역 경로를 받아 **실제 속도(cmd_vel)** 를 생성. 매 주기(`controller_frequency: 20.0` Hz):
1. 여러 속도 후보를 뿌림 (`vx_samples: 20` × `vtheta_samples: 20`)
2. 각 후보로 `sim_time: 1.7`초 앞을 시뮬레이션 → 미래 궤적
3. **critics(평가자)** 로 점수 매겨 최적 궤적 선택

**critics 가중치(.scale)가 로봇 성격 결정:**

| critic | scale | 역할 |
|--------|-------|------|
| PathDist | 32 | 전역경로에 가까이 붙기 (↓낮추면 경로 느슨하게 봄, 지름길) |
| PathAlign | 32 | 경로 방향 정렬 |
| GoalDist | 24 | 목표에 가까워지기 |
| GoalAlign | 24 | 목표 방향 정렬 |
| RotateToGoal | 32 | 도착 후 목표 방향 회전 |
| BaseObstacle | 0.02 | 장애물 회피 |

> 전체 critics 목록: `RotateToGoal, Oscillation, BaseObstacle, GoalAlign, PathAlign, PathDist, GoalDist`

**속도 한계 (TB4 물리값):** `max_vel_x: 0.26`, `max_vel_theta: 1.0`, `acc_lim_x: 2.5`.
차동구동이라 `_y`(횡방향)는 전부 0.

### goal/progress checker
- `xy_goal_tolerance: 0.25` = 목표 0.25m 안이면 도착. 안 멈추고 빙빙 돌면 키움
- `stateful: True` = 위치 도달을 **기억**하고 방향만 맞춤 (False면 매 순간 둘 다 만족해야 해서 빙빙 돌 수 있음)
- `progress_checker` = `movement_time_allowance: 10.0`초 안에 `required_movement_radius: 0.5`m 못 가면 "정체" → 복구 발동

### planner — NavFn
- `use_astar: false` → Dijkstra(최적) / true → A*(빠름)
- A*와 DWB는 **경쟁이 아니라 둘 다 사용.** A*=경로선, DWB=실제 조작. A*만으로는 못 움직임 (로봇 물리·실시간 장애물 모름)

### behavior_server — 복구 동작
`spin`(회전 재스캔) / `backup`(후진) / `wait`(동적 장애물 대기) / `drive_on_heading` / `assisted_teleop`

> 멀티맵 환경에서 런타임 맵 교체는 [[nav2_map_switching]] 참고.

---

## 3. slam.yaml — 지도 만들기 (SLAM)

### slam_toolbox란?
- ROS2의 대표 2D SLAM **외부 패키지** (Steve Macenski 개발).
- turtlebot이 직접 만든 게 아니라 **가져다 쓰는 라이브러리** (전기밥솥 비유).
- 라이다로 **지도를 그리면서 + 위치추정**. `map→odom` TF 발행.
- (SLAM 일반 원리·프론트엔드/백엔드 구조는 [[slam_concepts]] 참고)

### turtlebot 내 사용처 (`turtlebot4_navigation`)
```
package.xml          ← slam_toolbox 의존성 선언
launch/slam.launch.py ← slam_toolbox 노드 실행 (sync/async 선택)
config/slam.yaml      ← 설정값 주입
```

**sync vs async** (`slam.launch.py`의 `sync` 인자로 분기, 기본값 `true`):
| | sync_slam_toolbox_node (기본) | async_slam_toolbox_node |
|---|---|---|
| 처리 | 모든 스캔 빠짐없이 | 바쁘면 일부 건너뜀 |
| 품질/부하 | 정확·무거움 | 덜 정확·가벼움 |

### SLAM 핵심 원리 (포즈 그래프)

```
●────●────●────●  ← 지나온 위치(노드) + 각 위치의 스캔
   └ edge: 상대 이동
한 바퀴 돌면 → 루프 클로저로 누적오차 보정
```

- **노드** = 한 위치의 스캔 + 추정 위치
- **엣지** = 두 노드 간 상대 이동
- **솔버(Ceres)** = 그래프 전체를 최적화해 일관되게 폄 (이 블록은 기본값 그대로)
- (Loop Detection vs Loop Closure 용어 구분은 [[loop_detection_and_closure]] 참고)

### 두 핵심 메커니즘
1. **스캔 정합** (`use_scan_matching: true`) — 라이다를 겹쳐 맞춰 휠 드리프트 보정
2. **루프 클로저** (`do_loop_closing: true`) — 한 바퀴 돌아 출발점 인식 → 누적오차 한 방에 정렬

### 만질 만한 파라미터
| 파라미터 | 값 | 의미 |
|----------|-----|------|
| `mode` | mapping | mapping(새 지도) / localization(기존 지도 위 추정) |
| `resolution` | 0.05 | 격자 크기(m). 작을수록 정밀·메모리↑ |
| `max_laser_range` | 12.0 | 지도에 반영할 라이다 최대거리 |
| `minimum_travel_distance/heading` | 0.0 | 새 노드 추가 최소 이동/회전 |
| `loop_match_minimum_response_fine` | 0.45 | 루프 확정 임계값. 낮으면 오탐↑ |

---

## 4. AMCL vs SLAM — 왜 다른가 (핵심 통찰)

### 한 줄 요약
> 차이의 뿌리는 **지도를 "고정된 척도로 쓰느냐(AMCL)" vs "계속 갱신되는 구조로 쓰느냐(SLAM)"**.

### 종이 지도 vs 연필 노트 비유
- **AMCL = 종이 지도 든 사람**: 지도를 못 고침. 정확한 환경에서 최고지만, 새 가구가 생기면 헤맴.
- **SLAM = 연필로 그려가는 사람**: 새 구조를 계속 그려넣음. 변하는 환경에 적응하지만, 특징 적은 곳/초기값 없으면 약함.

| | AMCL (파티클) | slam_toolbox (그래프) |
|---|---|---|
| 추정 대상 | 위치 **만** | 위치 **+ 지도** |
| 지도 | 고정(읽기 전용) | 갱신 가능(elastic) |
| 고정 환경 | ✅ 매우 정확 | ✅ 정확 |
| 변하는 환경 | ❌ 적응 못 함 | ✅ 적응 |
| 완전 길 잃음(납치) | ✅ 강함 (파티클 전역 탐색) | ❌ 약함 (초기값 의존) |
| 불확실성 표현 | 다봉(여러 가설) | 단봉(하나의 해) |

**왜?**
- 파티클 필터엔 **지도에 써넣는 메커니즘이 없다.** 측정값은 채점에만 쓰고 버림 → 고정 지도 전용.
- 그래프는 **실제 스캔을 노드로 저장**하고 계속 추가 → 새 구조 자연 반영.

**왜 둘 다 필요?** 처음엔 SLAM으로 지도 그려 저장 → 이후엔 AMCL로 빠르고 안정적으로 운영.
(`.pgm` 표준 포맷 호환성, 전역 재추정 능력, 검증된 안정성 때문에 운영 단계는 AMCL이 관례)

> 참고: "파티클=고정, 그래프=갱신"이 절대 법칙은 아님. gmapping(FastSLAM)은 파티클 기반 SLAM.
> 정확히는 **"위치만 추정 vs 위치+지도 동시 추정"의 설계 선택**이 핵심.

---

## 5. 실로봇 전환 체크리스트
- [ ] 모든 yaml의 `use_sim_time: True → False`
- [ ] 라이다 토픽/프레임 이름 확인 (`scan`, `base_link` 등)
- [ ] `max_vel_x` 등 속도 한계가 실제 로봇 스펙과 맞는지
- [ ] `robot_radius`(0.175) / `inflation_radius`(0.45)가 실제 로봇 크기·환경에 맞는지

## 6. 추천 실험
1. RViz에서 AMCL 파티클 구름 켜고 수렴/확산 관찰. `min_particles`를 100으로 줄여보기
2. costmap 시각화 + `inflation_radius` 0.45→0.2, `cost_scaling_factor` 1↔10 변화 관찰
3. `PathDist.scale` 32→3으로 낮춰 경로 이탈 관찰
4. slam_toolbox로 직접 mapping → 한 바퀴 돌 때 **루프 클로저로 지도가 "탁" 정렬**되는 순간 목격
5. 만든 지도 저장 → AMCL localization으로 전환

---

## 출처
- 설정 파일 원문: `turtlebot/turtlebot4` 저장소 **humble** 브랜치 `turtlebot4_navigation/config/{localization,nav2,slam}.yaml`, `launch/slam.launch.py`
- Nav2 공식 문서: https://docs.nav2.org/
- slam_toolbox: https://github.com/SteveMacenski/slam_toolbox
