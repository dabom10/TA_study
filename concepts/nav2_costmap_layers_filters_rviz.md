# Nav2 Costmap 레이어 · 필터 · RViz 색상

> 관련: [[nav2_localization_slam_config]] — costmap/inflation 파라미터 튜닝 실전 / [[slam_concepts]] — OGM vs Costmap 차이 / [[nav2_amcl_tf_tree]] — costmap이 쓰는 TF 프레임 / [[nav2_map_switching]] — 런타임 맵 교체

> 검증: `/opt/ros/jazzy/share/nav2_bringup/params/nav2_params.yaml` (L188~262) — plugin 구성 일치
> 검증: docs.nav2.org Costmap 2D / Inflation / Keepout·Speed·Binary Filter — 일치
> 검증: ros2/rviz `docs/FEATURES.md` (costmap color scheme) — 일치

---

## 한 줄 요약

Costmap = 지도 각 셀에 "지나가면 얼마나 위험한가"를 **0~254**로 칠한 격자.
이 값은 여러 **레이어 플러그인**이 아래→위로 합성해서 만들고, 그 위에 **필터**(keepout/speed/binary)가 마스크 기반 규칙을 덧씌운다. RViz는 이 값을 **색상**으로 보여준다.

---

## 1. Costmap cost 값 체계 (0~254/255)

> 검증: docs.nav2.org "Costmap 2D" — 일치

| 값 | 상수명 | 의미 |
|----|--------|------|
| **0** | FREE_SPACE | 자유 공간, 통과 가능 |
| **1~252** | (inflated) | 장애물에서 멀어질수록 감소하는 위험 비용 (포텐셜 필드) |
| **253** | INSCRIBED_INFLATED_OBSTACLE | 로봇 **내접원(inscribed radius)** 안. 중심이 여기 있으면 footprint가 장애물과 충돌 → 사실상 못 지나감 |
| **254** | LETHAL_OBSTACLE | 실제 장애물 셀. 충돌 확정 |
| **255** | NO_INFORMATION | 미지 영역 (한 번도 관측 안 된 곳) |

planner/controller는 이 값을 포텐셜 필드처럼 읽어 **비용이 낮은 경로**를 고른다.

---

## 2. 레이어 플러그인 (아래→위 합성)

`plugins:` 리스트에 적힌 **순서대로** 합성된다. 아래 레이어 위에 다음 레이어가 덮어쓴다.

TurtleBot4 기본 구성 (검증: nav2_params.yaml):
- **global_costmap**: `["static_layer", "obstacle_layer", "inflation_layer"]`
- **local_costmap**: `["voxel_layer", "inflation_layer"]`

### 2-1. StaticLayer (`nav2_costmap_2d::StaticLayer`)
- **저장된 지도**(SLAM/map_server의 OccupancyGrid)를 costmap에 그대로 반영.
- 벽·고정 구조물 같은 정적 환경의 바탕. 보통 global_costmap에만 둔다(local은 주변만 보므로).
- `/map` 토픽(또는 지정 topic) 구독.

### 2-2. ObstacleLayer (`nav2_costmap_2d::ObstacleLayer`)
- **2D 센서**(LaserScan/PointCloud)로 실시간 장애물을 marking(찍기)/clearing(지우기).
- ray-tracing으로 센서~장애물 사이는 비우고, 끝점은 장애물로 표시.
- 지도에 없는 동적 장애물(사람·박스 등) 대응.

### 2-3. VoxelLayer (`nav2_costmap_2d::VoxelLayer`)
- ObstacleLayer의 **3D 버전**. 높이(z)를 voxel(복셀)로 나눠 추적.
- 높이가 다른 장애물·턱을 구분하고, 3D 정보로 clearing이 더 정확.
- TurtleBot4 local_costmap 기본값. (RGBD/3D 데이터 활용)

### 2-4. InflationLayer (`nav2_costmap_2d::InflationLayer`)
- 장애물 주위로 **위험 비용을 부풀려** 로봇이 벽을 스치지 않게 함.
- 다른 레이어와 달리 새 장애물을 추가하는 게 아니라, **기존 장애물 주변에 그라데이션**을 깐다.

**핵심 파라미터** (검증: nav2_params.yaml — TB4 기본 `inflation_radius: 0.7`, `cost_scaling_factor: 3.0`):

| 파라미터 | 뜻 |
|----------|----|
| `inflation_radius` | 장애물에서 비용을 퍼뜨리는 **반경(m)**. 클수록 장애물을 넓게 피함 |
| `cost_scaling_factor` | 거리에 따라 비용이 **얼마나 가파르게 떨어지는가**. **클수록 빨리 0으로** 떨어짐(벽에 더 바싹 붙음), 작을수록 완만(넓게 회피) |

비용 계산식(개념):
```
cost = (253 - 1) · exp( -cost_scaling_factor · (장애물까지거리 - inscribed_radius) )
```
- 내접원 안(거리 ≤ inscribed_radius): **253**
- 그 밖 ~ inflation_radius: 지수 감소하는 1~252
- inflation_radius 밖: **0**

```
254┤█╲          ← LETHAL (벽)
253┤ █╲         ← INSCRIBED (내접원 안)
   ┤   ╲___     ← exp 감소 (cost_scaling_factor가 곡선 가파름 결정)
  0┤       ╲___ ← inflation_radius 밖은 0
   └──────────── 거리
```

> ⚠️ 흔한 오해: `cost_scaling_factor`가 **크면** 회피를 더 잘하는 게 아니라 **반대로** 비용이 빨리 사라져 벽에 가까이 붙는다.

---

## 3. Costmap Filters (keepout / speed / binary)

레이어와 별개로 **필터 마스크**(PGM/PNG/BMP 이미지 + YAML)를 읽어 특정 구역에 규칙을 입히는 플러그인.

### 공통 구조 (검증: docs.nav2.org Costmap Filter Info Server)
1. **Filter Mask 서버**(map_server): 마스크 이미지를 OccupancyGrid로 발행.
2. **Costmap Filter Info 서버**: `nav2_msgs/CostmapFilterInfo`로 변환 계수 발행.
   - 필터 공간값 `Fv = base + multiplier × mask_value`
3. **필터 플러그인**(costmap의 plugin/filter로 등록): 로봇 위치의 마스크값을 읽어 동작.

### 3-1. KeepoutFilter (`nav2_costmap_2d::KeepoutFilter`)
- 마스크 값으로 **출입 금지/선호 차선**을 만든다.
- **점유값(100)** → keep-out 존: 로봇이 못 들어감(costmap에 lethal로 찍힘).
- **1~99** → 가중 영역(preferred lane): 통과는 가능하나 planner가 가급적 피함(값 클수록 비선호).
- 용도: 위험구역 차단, 창고에서 정해진 통로만 다니게.

### 3-2. SpeedFilter (`nav2_costmap_2d::SpeedFilter`)
- 마스크 값을 **속도 제한**으로 변환. `speed_limit = mask × multiplier + base`.
- 마스크 `[1..100]` → 속도 제한값으로 선형 변환, `0`이면 제한 없음.
- 두 모드:
  - **percentage**: 최대 속도의 %  (예 base=100, multiplier=-1 → 마스크 50 = 50% 속도)
  - **absolute**: m/s 절대값
- 속도 제한을 `speed_limit` 토픽으로 발행 → controller_server가 받아 감속. (메시지 타입은 `nav2_msgs/SpeedLimit`, 단 fetch 발췌엔 토픽명만 명시됨)
- 용도: 사람 많은 구역·교차로 서행.

### 3-3. BinaryFilter (`nav2_costmap_2d::BinaryFilter`)
> 검증: docs.nav2.org "Binary Filter Parameters" — 동작·`std_msgs/Bool` 발행·`Fv=base+multiplier×mask` 일치
> 미검증(보강): 기본값 `flip_threshold 50.0`·`default_state false`·`binary_state` — WebSearch(소스 인용) 기반, 공식 페이지 발췌엔 기본값 미표기
- 로봇이 마스크 구역에 들어가면 **불리언 상태를 토글**. costmap 자체는 안 바꾸고 **신호만** 발행.
- `Fv = base + multiplier × mask_value`가 **`flip_threshold`(기본 50.0)** 보다 크면 상태 뒤집고, 작거나 같으면 복귀.
- `std_msgs/Bool`을 `binary_state`(기본) 토픽으로 발행. `default_state` 기본 `false`.
- 용도: 특정 구역 진입 시 라이트·청소기·알림 등 외부 동작 on/off.

---

## 4. RViz2에 뜨는 costmap 색상의 의미

> 검증: ros2/rviz `docs/FEATURES.md` (Map display "costmap" color scheme) — 일치

RViz의 **Map** 디스플레이에서 Topic을 `/global_costmap/costmap`(또는 local)로, **Color Scheme = `costmap`**으로 두면 아래 색으로 칠해진다.

주의: RViz가 받는 `/.../costmap` 토픽은 `nav_msgs/OccupancyGrid`라 값이 **0~100으로 스케일**된다(원본 0~254는 `/.../costmap_raw`의 `nav2_msgs/Costmap`). 그래서 색상 기준도 0~100이다:

| OccupancyGrid 값 | 색상 | 의미 (원본 cost 대응) |
|------|------|------|
| **0** | 검정 | FREE_SPACE (자유 공간) |
| **1~98** | 파랑→빨강 그라데이션 | inflated 비용. 빨강에 가까울수록 위험 |
| **99** | 청록(cyan) | INSCRIBED_INFLATED_OBSTACLE (253) — 내접원, 사실상 벽 |
| **100** | 보라(purple) | LETHAL_OBSTACLE (254) — 실제 장애물 |
| **-1** | 푸른빛 도는 회색 | NO_INFORMATION (255) — 미지 영역 |
| 101~127 (비정상) | 초록 | 잘못된 양수값 |
| 음수(비정상) | 빨강~노랑 | 잘못된 음수값 |

요약: **검정=빈 공간 / 파랑~빨강=가까워질수록 위험 / 청록=내접원 경계 / 보라=장애물 / 회색=미지**.

필터를 쓰면 keepout 마스크가 보라(장애물처럼), speed/keepout의 가중 영역이 파랑~빨강 그라데이션으로 costmap에 반영되어 보인다. 필터 마스크 자체도 별도 Map 디스플레이로 띄워 확인할 수 있다.

---

## 의문점 / 나중에 파고들 것
- `cost_scaling_factor` vs `inflation_radius`를 실제 RViz costmap에서 바꿔보며 그라데이션 변화 관찰 (→ [[nav2_localization_slam_config]] 실습 항목)
- 필터를 동시에 여러 개(keepout+speed) 쓸 때 plugin 순서와 마스크 관리
- local(voxel)과 global(obstacle)의 marking/clearing 동작 차이 실측
