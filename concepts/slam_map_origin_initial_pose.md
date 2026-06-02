# SLAM 맵 원점 · initial pose · map→odom 방향

## 한 줄 요약
SLAM/localization의 map 원점은 "매핑을 시작한 그 지점"이고, TF 화살표 `map→odom→base_link`는 위치를 묻는 방향이 아니라 "부모는 하나" 규칙이 강제한 매달림 구조다.

> TF 트리 구조·AMCL 입자필터 동작·코드(TF2 Buffer 등)는 중복 작성하지 않고 [nav2_amcl_tf_tree.md](nav2_amcl_tf_tree.md) 참고.

---

## 1. map의 초기 원점 = SLAM 시작 위치

- SLAM을 켜는 **그 순간 로봇이 있던 위치·방향이 곧 map 원점 (0,0,0)**이 된다.
  절대 좌표가 아니라 "매핑 시작점 기준 상대 좌표계".
- 따라서 같은 공간을 매핑해도 **시작 위치·방향이 다르면 저장되는 맵 좌표가 통째로 회전·이동**한다.
- slam_toolbox는 `map_start_pose`(예: `[0.0, 0.0, 0.0]`) 파라미터로 원점을 로봇 시작 위치 기준 어디에 둘지 지정 가능.

> 검증: slam_toolbox README — `map_start_pose` 파라미터 / nav2 docs — SLAM이 map→odom 보정 publish — 일치

### 저장된 map.yaml의 `origin`은 다른 의미

```yaml
origin: [-5.23, -3.81, 0.0]   # [x, y, yaw]
```

- 이 `origin`은 **이미지(.pgm)의 좌측 하단 픽셀이 map 좌표계에서 갖는 pose**다. (yaw는 반시계, 많은 노드가 yaw 무시)
- 값이 음수인 이유: 로봇 시작점 (0,0) 기준으로 탐색 영역이 시작점의 왼쪽·아래로도 뻗어 있어, 좌하단 모서리가 음수 좌표에 놓이기 때문.
- 즉 "로봇 시작점"과 "yaml origin"은 별개 개념 — 헷갈리지 말 것.

> 검증: ROS map_server 문서 / ROS Answers — origin = 좌측 하단 픽셀의 2D pose (x,y,yaw) — 일치

---

## 2. initial pose의 개념 (맥락이 두 가지)

| 맥락 | initial pose 필요? | 이유 |
|------|-------------------|------|
| **SLAM으로 새 맵 생성 중** | 보통 불필요 | 시작 위치가 곧 원점이라 로봇이 출발하며 스스로 정의 |
| **기존 맵에서 localization (AMCL)** | **필수** | 미리 만든 맵 안에서 "지금 대략 여기, 이 방향"을 사람이 알려줘야 함 |

- AMCL 같은 입자필터는 initial pose를 **파티클을 뿌리는 초기 씨앗**으로 쓴다.
- 지정 방법: RViz **2D Pose Estimate** 툴로 클릭&드래그, 또는 `nav2_params.yaml`에 `set_initial_pose: true` + `initial_pose:`.
- 방향(yaw) 오차가 위치(x,y) 오차보다 치명적 — 초기 yaw가 틀어지면 이동할수록 벌어진다.

> 검증: nav2 docs — 2D Pose Estimate로 초기 위치 제공 / set_initial_pose·initial_pose 파라미터 — 일치

---

## 3. RViz에서 맵이 격자 구석에 몰려 보이는 현상

**거의 항상 정상이며 에러가 아니다.**

- RViz의 Grid는 **map 프레임 원점 (0,0)을 중심**으로 그려진다. 맵의 기하학적 중앙이 아니다.
- 그 (0,0)은 **SLAM을 시작한 지점**이므로, 로봇이 공간 중앙이 아닌 구석/입구에서 매핑을 시작했다면 맵 전체가 격자 중심에서 한쪽으로 쏠려 보인다.

> 검증: ROS Answers(grid center vs map center) — RViz Grid는 reference frame 원점 기준 — 일치

### 문제 판별

| 상황 | 해석 |
|------|------|
| 맵 형태는 멀쩡한데 격자에서 한쪽 치우침 | **정상.** 시작 지점이 구석이었을 뿐. 격자는 시각 보조선이라 localization/navigation에 영향 없음 |
| 맵이 깨지거나 겹쳐 보이고 좌표가 비정상적으로 큼 | 매핑 중 odometry drift·루프클로저 실패 의심 (별개 문제) |
| 로봇 TF가 맵 밖/엉뚱한 곳 | initial pose 미설정·오설정 → 2D Pose Estimate로 재지정 |

- 보기 좋게 중앙에 두려면: ①시작 위치를 공간 중앙으로 잡고 재매핑, 또는 ②yaml `origin` 직접 수정(단 goal 좌표도 같이 바뀌므로 운용 맵엔 비권장).

---

## 4. `/map`·`amcl_pose`는 누가? — 흔한 오해 정정

| 토픽/변환 | 발행 주체 | 비고 |
|-----------|-----------|------|
| `/scan` | 라이다 드라이버 | AMCL이 **구독** |
| `/map` | **map_server** | localization 모드에선 정적 파일(.pgm+.yaml) 로드. AMCL은 **구독**, 발행 아님 |
| `/amcl_pose` | **AMCL** | 출력용·진단용 (아래) |
| `map → odom` (TF) | **AMCL** | AMCL의 진짜 산출물 |

- **SLAM 모드(slam_toolbox)**: 맵을 만드는 중이라 `/map`을 **발행**.
- **Localization 모드(AMCL)**: 다 만든 맵을 쓰는 중이라 map_server가 발행, AMCL은 **구독**.

> 검증: nav2 docs — `/map`은 map_server가 발행, AMCL은 정적 맵을 받아 사용 — 일치

### amcl_pose는 거의 안 쓰는가?

- **navigation이 실제로 참조하는 건 TF 트리** (`map→odom→base_link`). 다른 Nav2 노드는 `amcl_pose` 토픽이 아니라 TF를 조회해 위치를 얻는다.
- `amcl_pose`(`PoseWithCovarianceStamped`)는 "추정 위치 + 불확실성(공분산)"을 곁다리로 내보내는 **출력**. 용도: RViz 시각화 / 수렴·확신도 모니터링(공분산 크면 아직 헤매는 중) / 사용자 코드에서 위치 한 번 읽기.

---

## 5. 왜 `map→odom→base_link` 방향인가 (핵심)

> 오해: "위치 추정이면 `base_link→odom→map`이어야 하지 않나?"

**화살표 방향 ≠ 위치를 묻는 방향.** 화살표는 "부모→자식(누가 누구에게 매달려 있나)"일 뿐이고, TF는 **양방향 조회**가 된다(변환은 역행렬이 항상 존재). 트리가 `map→odom→base_link`여도:

```
"map에서 base_link 어디?" → lookupTransform(map, base_link)
```

끝에서 끝까지 곱해 그냥 나온다. 그래서 화살표를 뒤집을 필요가 없다.

### 방향을 강제하는 규칙: "부모는 정확히 하나"

> 검증: REP-105 — "each coordinate frame has one parent, any number of children" / 두 프레임 사이 경로는 유일 — 일치

1. `base_link`의 부모는 이미 `odom`(엔코더가 `odom→base_link` publish 중).
2. localization이 실제로 계산하는 건 `map→base_link`.
3. 그러나 `map→base_link`를 직접 쏘면 base_link의 부모가 odom·map **둘** → 트리 규칙 위반(사이클).
4. 그래서 한 다리 물러서서 **`map→odom`만** publish:

```
T(map→odom) = T(map→base_link) × T(odom→base_link)⁻¹
                  ↑ 추정한 값         ↑ 엔코더가 이미 준 값
```

→ base_link의 부모는 여전히 odom 하나, localization은 빈 다리 `map→odom`만 채움. 곱하면 `map→base_link` 복원.

> 검증: REP-105 — "localization은 map→base_link를 broadcast하지 않고, odom→base_link를 받아 map→odom을 broadcast한다" — 일치

### 왜 map이 뿌리(root)인가

- 고정된 세계 프레임(map, odom)이 부모, 그 안에서 움직이는 base_link가 자식 — REP-105 규약.
- 로봇 여러 대·센서 여러 개가 **공통 map 하나를 공유**하려면 map이 뿌리여야 한다. base_link가 뿌리면 로봇마다 세상이 따로 생겨 공유 불가.

---

## 6. odom의 역할 한 줄 정리

- `odom→base_link`: 엔코더가 만드는 **부드러운 단기 움직임**(점프 없음) → 단기 제어가 덜컹대지 않음.
- AMCL이 매 스캔마다 누적 drift를 계산해 `map→odom`에 반영 → **odom 판 전체를 슬쩍 밀어 drift 상쇄**.
- 결과: 로봇은 odom 위에서 부드럽게 움직이고, map 안에서는 정확한 위치 유지. 점프 충격은 odom 층이 흡수.

---

## 다른 섹션과의 연결
- TF 트리 구조·AMCL 입자필터 동작·TF2 Buffer 코드 → [nav2_amcl_tf_tree.md](nav2_amcl_tf_tree.md)
- SLAM 개념(LiDAR/OGM/slam_toolbox 노드-토픽) → [slam_concepts.md](slam_concepts.md)
- Loop closure·Pose graph 최적화(매핑 중 drift 보정) → [loop_detection_and_closure.md](loop_detection_and_closure.md)
- localization/nav2/slam.yaml 파라미터 심화 → [nav2_localization_slam_config.md](nav2_localization_slam_config.md)

## 의문점 / 나중에 파고들 것
- AMCL 초기 수렴 실패 시 공분산 임계값과 재초기화(global localization) 트리거 조건
- slam_toolbox `map_start_pose` 지정 시 저장 yaml `origin`이 어떻게 바뀌는지 실측

---

### 출처
- [REP-105: Coordinate Frames for Mobile Platforms](https://www.ros.org/reps/rep-0105.html)
- [Configuring AMCL — Nav2 Documentation](https://docs.nav2.org/configuration/packages/configuring-amcl.html)
- [Navigating while Mapping (SLAM) — Nav2 Documentation](https://docs.nav2.org/tutorials/docs/navigation2_with_slam.html)
- [slam_toolbox — GitHub (Steve Macenski)](https://github.com/SteveMacenski/slam_toolbox)
- [To understand the concept of Origin field from map_server — ROS Answers](https://answers.ros.org/question/322919/to-understand-the-concept-of-origin-field-from-map_server/)
- [how to identify the grid center with saved map center? — ROS Answers](https://answers.ros.org/question/336348/how-to-identity-the-grid-center-with-saved-map-center/)
