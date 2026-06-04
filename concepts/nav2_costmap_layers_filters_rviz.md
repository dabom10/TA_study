# Nav2 Costmap 레이어 · 필터 · RViz 색상

> 관련: [[nav2_localization_slam_config]] — costmap/inflation 파라미터 튜닝 실전 / [[slam_concepts]] — OGM vs Costmap 차이 / [[nav2_amcl_tf_tree]] — costmap이 쓰는 TF 프레임 / [[nav2_map_switching]] — 런타임 맵 교체

> 검증: `/opt/ros/jazzy/share/nav2_bringup/params/nav2_params.yaml` (L188~262) — plugin 구성 일치
> 검증: `turtlebot4_navigation/config/nav2.yaml` — TB4 실제 layer 입력원·inflation 값
> 검증: `inflation_layer.hpp` `computeCost()` (ros-navigation/navigation2 main) — inflation 공식
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
- pgm/yaml 파일을 **직접 읽지 않고 `/map` 토픽을 구독**한다.

#### 왜 파일이 아니라 토픽인가
> 검증: nav2.yaml `static_layer: map_subscribe_transient_local: True`, `map_server: yaml_filename` — 일치

```
map.yaml + map.pgm ──[map_server가 디스크 로드]──> /map (nav_msgs/OccupancyGrid) ──[구독]──> StaticLayer
```
pgm/yaml을 읽는 노드는 **map_server 하나뿐**이고, 그게 OccupancyGrid로 변환해 `/map`을 발행한다. StaticLayer는 그 토픽만 본다. 이유:
1. **ROS2 분산 구조** — 맵 파일 경로를 모든 노드가 알 필요 없이 map_server 한 곳만 알면 됨.
2. **transient_local(latched) QoS** (`map_subscribe_transient_local: True`) — map_server가 한 번만 발행해도 늦게 뜬 costmap이 마지막 맵을 받음. 타이밍 어긋나도 안전.
3. **런타임 맵 교체가 공짜** — `load_map` 서비스로 새 `/map` 발행 → StaticLayer 자동 갱신 ([[nav2_map_switching]]).
4. **SLAM 모드와 통일** — slam_toolbox가 맵을 실시간 갱신하며 `/map` 발행해도 StaticLayer 코드는 동일. "미리 딴 정적 맵"은 그 한 경우일 뿐.

### 2-2. ObstacleLayer (`nav2_costmap_2d::ObstacleLayer`)
- **2D 센서**(LaserScan/PointCloud)로 실시간 장애물을 marking(찍기)/clearing(지우기).
- ray-tracing으로 센서~장애물 사이는 비우고, 끝점은 장애물로 표시.
- 지도에 없는 동적 장애물(사람·박스 등) 대응.

### 2-3. VoxelLayer (`nav2_costmap_2d::VoxelLayer`)
- ObstacleLayer의 **3D 버전**. 높이(z)를 voxel(복셀)로 나눠 추적(`z_voxels: 16`, `z_resolution: 0.05` → 0~0.8m를 16칸).
- 동작: 관측 포인트가 속한 (x,y,z) voxel을 marked → 2D costmap으로 **투영**(한 컬럼에 marked voxel이 `mark_threshold` 초과면 그 셀을 장애물로). clearing은 3D ray-trace.
- 잠재적으로 높이 다른 장애물·턱을 구분하지만, **이건 3D 포인트클라우드를 먹였을 때만 참**이다.

> ⚠️ TB4 기본 구성 정정 (검증: `turtlebot4_navigation/config/nav2.yaml` L151~167 — local voxel_layer, L197~206 — global obstacle_layer)
> ```yaml
> voxel_layer:
>   observation_sources: scan
>   scan: { topic: scan, data_type: "LaserScan" }   # ← PointCloud2 아님
> ```
> TB4 OOTB는 voxel_layer도 obstacle_layer도 **입력이 `/scan`(RPLIDAR 2D LaserScan) 하나뿐**이고 **depth camera(OAK-D)는 costmap에 안 들어간다.** LaserScan은 z가 라이다 한 높이뿐이라 16칸 중 한 층만 채워짐 → **사실상 순수 2D ObstacleLayer와 동일하게 동작**. "VoxelLayer라서 3D"는 자료구조상 잠재력일 뿐 현재는 미발휘.
>
> 실제 3D로 쓰려면 `observation_sources`에 PointCloud2 소스를 추가해야 한다:
> ```yaml
> observation_sources: scan pointcloud
> pointcloud: { topic: /oakd/points, data_type: "PointCloud2",
>               min_obstacle_height: 0.05, max_obstacle_height: 0.8 }
> ```
> 이때 비로소 테이블 상판·낮은 턱·라이다 평면 밖 돌출물 등 2D 라이다가 못 보는 것을 높이별로 인식해 costmap에 투영한다. `min/max_obstacle_height`로 장애물로 칠 높이 띠를 거른다.

### 2-4. InflationLayer (`nav2_costmap_2d::InflationLayer`)
- 장애물 주위로 **위험 비용을 부풀려** 로봇이 벽을 스치지 않게 함.
- 다른 레이어와 달리 새 장애물을 추가하는 게 아니라, **기존 장애물 주변에 그라데이션**을 깐다.

**핵심 파라미터** (검증: `turtlebot4_navigation/config/nav2.yaml` L148~150, L214~216 — TB4 실제값 `cost_scaling_factor: 4.0`, `inflation_radius: 0.45`):

| 파라미터 | 뜻 |
|----------|----|
| `inflation_radius` | 비용이 **존재하는 거리 한계(m)**. 이 밖은 무조건 0 — 위험구역의 **넓이** |
| `cost_scaling_factor` | 그 한계 안에서 비용이 **얼마나 빨리 식는가** — 위험구역의 **기울기/농도** |

비용 계산식 (검증: `inflation_layer.hpp` `computeCost()`, ros-navigation/navigation2 main — 일치):
```
거리 == 0            → 254 (LETHAL, 실제 장애물)
거리 ≤ inscribed     → 253 (INSCRIBED, footprint 충돌)
그 밖                → cost = (253-1) · exp( -cost_scaling_factor · (거리 - inscribed_radius) )
거리 > inflation_radius → 0
```
지수함수 `exp(-k·거리)`에서 **k가 곧 `cost_scaling_factor`**. k가 클수록 그래프가 가파르게 0으로 떨어진다.

```
253┤█
   │█╲                    factor 작음(완만): ─── 멀리까지 비용 남음 → 넓게 회피
   │█ ╲___
   │█     ╲────___
   │█  ╲       ╲────___
   │█   ╲___        ╲───___
   │█       ╲ factor 큼(가파름): 벽 옆만 비용 → 벽에 붙음
  0┤█________╲______________╲────
   └──┬──────────────────────┬──── 벽에서 거리
   inscribed_radius     inflation_radius
```

**숫자 예시** (TB4 `factor=4.0`, 내접반경 ≈0.175m 가정, `inflation_radius=0.45`). 같은 거리인데 factor만 다를 때 cost 비교:

| 벽에서 거리 | factor=2 (완만) | **factor=4 (TB4)** | factor=10 (가파름) |
|---|---|---|---|
| 0.20 m | 228 | 228 | 196 |
| 0.25 m | 217 | **187** | 119 |
| 0.30 m | 195 | **153** | 72 |
| 0.35 m | 178 | **125** | 44 |
| 0.45 m | 145 | **84** | 16 |

> 미검증(공식 대입 계산 예시): 위 표는 공식에 대입한 근사값. 내접반경은 로봇 반경≈0.175 가정이라 실제 footprint 설정에 따라 달라짐.

읽는 법: 벽에서 **0.35m 떨어진 같은 지점**인데 factor=2면 cost 178("아직 위험"→더 멀리 회피), factor=10이면 cost 44("거의 안전"→거리낌 없이 통과).

> ⚠️ 흔한 오해: `cost_scaling_factor`가 **크면** 회피를 더 잘하는 게 아니라 **반대로** 비용이 빨리 사라져 벽에 가까이 붙는다.

**둘은 독립**: `inflation_radius`를 넓혀도 `cost_scaling_factor`가 크면 벽에서 조금만 떨어져도 비용이 거의 0이라 효과가 약하다 → **항상 같이 봐야 함**.

**튜닝 감각**: 너무 크게(10+)면 좁은 문은 잘 지나가나 장애물에 위태롭게 붙고, 너무 작게(1)면 안정적이나 좁은 통로를 못 지나간다. TB4 기본 4.0은 중간 타협값.

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
