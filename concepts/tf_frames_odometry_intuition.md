# TF 프레임 직관 — odom·base_link·map과 오도메트리 원리

## 한 줄 요약
odom은 "부팅 때 꽂은 임시 말뚝", base_link는 "바퀴 회전을 합산한 현재 로봇 위치", map은 "지도가 정한 영구 고정 기준점"이다. 정적인 건 base_link↔센서일 뿐, odom↔base_link는 매 순간 적분으로 갱신되는 동적 변환이다.

> 방향(왜 `map→odom`인가)·맵 원점·initial pose·RViz 격자 현상은 [slam_map_origin_initial_pose.md](slam_map_origin_initial_pose.md), TF2 Buffer 코드·AMCL 파라미터는 [nav2_amcl_tf_tree.md](nav2_amcl_tf_tree.md) 참고. 여기선 "각 프레임이 무엇이고 값이 어떻게 생기나"의 직관에 집중.

---

## 1. 세 프레임을 "깃발" 비유로

| | **odom 깃발** | **map 깃발** |
|---|---|---|
| 어디 꽂힘 | 부팅한 바로 그 자리 (0,0,0) | 지도 만들 때 정한 실제 세계의 한 지점 (보통 매핑 시작 위치) |
| 매번 바뀌나 | **켤 때마다 다른 자리** | **항상 같은 자리** (맵 파일에 박제) |
| base_link를 어떻게 아나 | 바퀴 회전 누적 (추측항법) | 라이다로 주변 보고 지도와 대조 |
| 성질 | 부드럽지만 drift | 정확·고정, 보정 시 점프 |

- **odom = 임시 말뚝**: 로봇을 어디서 켰느냐에 따라 매번 다른 곳에 꽂힌다. 그래서 odom 좌표로 "현관 위치"를 적어두면 다음 부팅 때 엉뚱한 곳을 가리킨다.
- **map = 건물에 영구히 박힌 깃발**: 한 번 지도를 만들 때 "여기가 (0,0)"으로 정하면, 로봇을 어디서 켜든 늘 같은 실제 장소를 가리킨다.
- **base_link = 지금 이 순간의 로봇 본체** (센서들이 매달린 기준점).

> 검증: REP-105 — map은 drift 없는 world-fixed, odom은 부팅 기준 연속 프레임 — 일치

---

## 2. odom→base_link는 어떻게 생기나 (바퀴 회전 → pose 적분)

"바퀴 회전량"은 원재료일 뿐, 거기서 pose를 **적분**해 변환을 만든다. 차동구동(diff drive) 기준:

```
[1] 엔코더 → 각 바퀴 이동거리
    회전수 × 2π × 바퀴반지름 R = 굴러간 거리
    → Δt 동안 왼쪽 Δs_L, 오른쪽 Δs_R

[2] 두 바퀴 거리 → 로봇 전진량·회전량 (바퀴간격 L)
    전진량   Δs = (Δs_R + Δs_L) / 2
    방향변화 Δθ = (Δs_R − Δs_L) / L

[3] 누적(적분)
    θ += Δθ
    x += Δs · cos(θ)
    y += Δs · sin(θ)
```

이 누적된 `(x, y, θ)`가 곧 `odom → base_link` 변환이다.
- 바퀴 한 바퀴 = 둘레(2πR)만큼 바닥 이동 → 회전과 거리는 자전거 바퀴처럼 묶여 있어 바로 환산됨.
- rqt_tf_tree에서 `odom→base_link`는 동적이라 rate가 낮게(예: 21 Hz) 찍히고, static 변환(센서)은 10000처럼 높게 찍힌다.

### ⚠️ 단순화 주의 — 실제 Create3는 "바퀴 단독"이 아니라 다중센서 융합

위 [1]~[3]은 **개념 이해용 단순화(바퀴 회전만)** 다. 실제 TurtleBot4의 `odom→base_link`는 **Create3 베이스가** 발행하며, **바퀴 엔코더 + IMU + 광학 마우스 센서(바닥 옵티컬 플로우)** 를 융합해 추정한다(`/odom` 20 Hz → rqt의 21 Hz가 이것).

| | 위 단순화 | Create3 실제 |
|---|---|---|
| 방식 | 추측항법 = 증분 누적 | **똑같이** 추측항법 = 증분 누적 |
| 증분 Δ 출처 | 바퀴 회전만 | 바퀴 + IMU + 광학 마우스 융합 |
| 결과 | odom→base_link (drift) | odom→base_link (drift 더 적음) |

- 바뀌는 건 "한 걸음 Δ(Δs, Δθ)를 얼마나 정확히 재느냐"뿐, **누적해서 base_link를 만든다는 구조는 동일.**
- 각 센서 역할: 바퀴=거리(미끄러지면 거짓 보고), IMU=회전/heading(더 정확), 광학 마우스=실제 미끄러짐·횡방향 감지(slip 보정).
- 융합해도 여전히 **추측항법 → drift는 느려질 뿐 사라지지 않음 → map 보정 필요**(결론 불변).

> 검증: iRobot Create3 docs — "fuses the reading from its various sensors to produce a dead reckoning estimate"(wheel encoders·IMU·optical mouse), `/odom` 20 Hz — 일치

### 발행 주체 정리

| 다리 | 발행 노드 | 비고 |
|------|-----------|------|
| `odom → base_link` (동적) | **Create3 베이스** | 바퀴+IMU+광학 융합 추측항법, 20 Hz |
| `base_link → 센서` (정적) | **robot_state_publisher** | `robot_description`(URDF) 읽어 fixed→/tf_static·movable→/tf 발행 |

> robot_description(URDF)이 base_link 아래 TF 서브트리 전체의 출처 — 없으면 센서 데이터를 지도 좌표로 못 바꿔 SLAM/Nav2가 무너진다.
> 검증: robot_state_publisher ROS docs/GitHub — robot_description+joint_states 구독, fixed→/tf_static·movable→/tf — 일치

> 검증: ros2_control diff_drive_controller / DiffBot odometry — 위 kinematic 적분식, odom(부모)→base_link(자식) publish — 일치

### 정적인 것 vs 동적인 것

```
base_link → imu_link / oakd_camera / cliff_sensor   ← 정적 (볼트로 고정, /tf_static)
odom → base_link                                     ← 동적 (매 순간 적분 갱신)
```

base_link는 "센서들의 기준점"이라 고정처럼 보이지만, **그 base_link 덩어리 자체가 odom 안에서 돌아다닌다.** 정적인 건 base_link "안쪽"이고, base_link "바깥"(odom과의 관계)은 동적이다.

---

## 3. "현재 base_link"는 어떻게 아나 — 추측항법(dead reckoning)

직접 재는 센서는 없다. **기억해서 더한 값**이다.

```
부팅:        base_link = (0, 0, 0)
매 Δt마다:   새 위치 = 직전 위치 + 방금 굴러간 증분(Δs, Δθ)
```

> 현재 base_link = 출발점부터 지금까지 모든 이동 증분을 빠짐없이 더한 합계.

**비유 — 눈 감고 걷기**: 출발 지점을 알고, 눈 감고 걸음 수·방향만 세서 "지금 대략 여기"를 추정. 주변을 둘러보는 게 아니라 누적 기억만으로 안다. → 외부 확인이 없으니 작은 오차가 계속 쌓여 **drift 필연**. "눈을 뜨는 행위 = 라이다로 맵 대조 = localization"이 그래서 필요.

---

## 4. "odom 값 = base_link 값?" — 미묘한 구분

거의 맞지만 한 군데 다듬어야 한다.

- ❌ `odom = base_link` — odom(출발점 깃발)과 base_link(현재 로봇)는 서로 다른 두 점.
- ✅ `odom→base_link 변환 값 = odom 기준으로 본 base_link의 좌표`

`/odom` 토픽(`nav_msgs/Odometry`)이 이를 그대로 담는다:
```
header.frame_id = "odom"        ← 기준(출발점)
child_frame_id  = "base_link"   ← 위치를 말하는 대상
pose.pose       = (x, y, θ)     ← odom에서 본 base_link 좌표
```

비유: "출발점에서 동쪽 3m"는 출발점도 현재 위치도 아닌 **둘 사이 변위**. 단 출발점을 원점(0,0,0)으로 삼았으니 그 변위가 곧 "현재 좌표"가 된다. → 같은 base_link라도 **어느 자(프레임)로 재느냐**에 따라 값이 다르다: odom 자(누적, drift) vs map 자(보정된 정확값).

---

## 5. base_footprint = 바닥에 투영한 2D 점

`base_link`를 바닥면(z=0)으로 수직 투영한 "그림자 좌표".

- **z 항상 0**, **roll/pitch = 0**, **yaw는 base_link와 동일**.
- `base_link↔base_footprint` 변환에는 로봇 키만큼의 z 오프셋·기울기 제거가 담긴다.
- 존재 이유: 맵·코스트맵·경로계획은 전부 **2D 바닥 평면**에서 도므로, "바닥 위 로봇 위치" 한 점이 필요. base_link의 높이·기울기를 털어내 네비게이션이 쓰기 좋게 정리해준다.

> 검증: REP-120 / ROS Answers — base_footprint = base_link의 ground 투영, z=0, Nav2가 지면 기준 위치로 사용 — 일치

### 배치는 설정마다 다름 (주의)

- 흔한 문서: `odom → base_footprint → base_link` **체인**.
- 실측 사례(이 환경 rqt_tf_tree): `odom`이 `base_link`와 `base_footprint`를 **각각 직속 자식**으로 둠 (형제, base_footprint는 leaf).
- 어느 쪽이든 *역할*(2D 바닥 위치)은 동일. 누가 어떤 다리를 publish하느냐는 그 로봇의 publisher 설정에 달림.
  확인: `ros2 run tf2_ros tf2_echo odom base_footprint`, `ros2 topic echo /tf --once`

> 검증: 로컬 `tf_tree.jpg` — odom 직속으로 base_link·base_footprint 분기, base_footprint는 자식 없음 — 확인 / 다수 문서는 체인 구조로 설명 — 배치 불일치(설정 차이)

---

## 6. 왜 이런 트리 구조인가 (설계 이유)

### 부모는 하나 = 답도 하나
프레임이 부모를 둘 가지면 "A가 B에서 어디?"의 경로가 둘 생기고, drift 때문에 두 답이 어긋난다. 트리(부모 하나)로 강제해 **경로를 유일하게** 만든다. → 자세한 `map→odom` 방향 유도는 [slam_map_origin_initial_pose.md](slam_map_origin_initial_pose.md) 5장.

### 관심사 분리 — 각 노드는 자기가 아는 다리만
| 다리 | publisher | 그 노드만 아는 것 |
|------|-----------|-------------------|
| base_link → 센서 | robot_state_publisher(URDF) | 고정 기하 (CAD), static |
| odom → base_link | Create3 (바퀴+IMU+광학센서 융합) | 굴러간 양, drift |
| map → odom | AMCL / slam_toolbox | 라이다·맵 대조 보정값 |

이점: ①독립 실행(주행부만 켜도 odom까지 동작) ②부품 교체 자유(AMCL↔slam_toolbox) ③고장 격리(localization 죽어도 주행은 살아있음).

### root는 설정이 아니라 emergent
root = "그 위로 부모 다리를 아무도 안 그린 프레임". 지금 `map→odom`을 쏘는 노드가 없으면 odom이 자동 root. AMCL을 켜면 `map→odom`이 생겨 map이 새 root가 됨 — 구조가 바뀌는 게 아니라 빈 윗다리가 채워질 뿐.

### 전체 목적
트리가 완성되면 어떤 프레임 데이터든 경로를 걸어 다른 프레임으로 변환 가능:
```
점(lidar_frame) → base_link → odom → map
       ↑URDF        ↑엔코더    ↑AMCL
```
세 노드가 각자 그린 다리를 이어, 누구도 단독으로 모르는 "라이다 점의 맵 좌표"가 나온다. **분산 정보를 한 줄로 합성하는 것**이 TF의 존재 이유.

---

## 7. rqt_tf_tree에서 map이 안 보일 때

**정상이며, localization/SLAM 미실행이라는 뜻.**
- rqt_tf_tree는 실제로 publish되는 변환만 그림. `map→odom`을 쏘는 노드(AMCL/slam_toolbox)가 없으면 map 프레임 자체가 트리에 없고 odom이 root가 된다.
- map을 띄우려면 localization(AMCL) 또는 SLAM(slam_toolbox)을 실행 → 트리 맨 위에 map이 생기고 `map→odom→base_link` 연결.

> 미검증: TurtleBot4 localization/slam 런치 파일명·인자 — 패키지 버전(Humble/Jazzy)별로 다를 수 있어 실제 패키지에서 확인

---

## 다른 섹션과의 연결
- 맵 원점·initial pose·RViz 격자·`map→odom` 방향 유도·amcl_pose 역할 → [slam_map_origin_initial_pose.md](slam_map_origin_initial_pose.md)
- TF2 Buffer/TransformListener 코드, AMCL 파라미터, depth→지도 좌표 파이프라인 → [nav2_amcl_tf_tree.md](nav2_amcl_tf_tree.md)
- SLAM 노드-토픽 구조 → [slam_concepts.md](slam_concepts.md)
- 누적 오차 보정(루프클로저·포즈그래프) → [loop_detection_and_closure.md](loop_detection_and_closure.md)

## 의문점 / 나중에 파고들 것
- 이 환경에서 `odom→base_footprint`를 publish하는 구체적 노드 (tf2_echo로 현장 확인)
- 시뮬(Gazebo) vs 실로봇에서 base_footprint 배치(체인 vs 형제)가 갈리는 원인
- EKF(robot_localization) 사용 시 odom→base_link publisher가 어떻게 바뀌는지

---

### 출처
- [REP-105: Coordinate Frames for Mobile Platforms](https://www.ros.org/reps/rep-0105.html)
- [REP-120: Coordinate Frames for Humanoid Robots](https://www.ros.org/reps/rep-0120.html)
- [Create® 3 Odometry — iRobot Education](https://iroboteducation.github.io/create3_docs/api/odometry/)
- [robot_state_publisher — GitHub (ros)](https://github.com/ros/robot_state_publisher)
- [diff_drive_controller — ros2_control 문서](https://control.ros.org/humble/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html)
- [Odometry — DiffBot Differential Drive Mobile Robot](https://ros-mobile-robots.com/theory/modeling-control/odometry/)
- [How to Publish Wheel Odometry Information Over ROS — automaticaddison](https://automaticaddison.com/how-to-publish-wheel-odometry-information-over-ros/)
- [What is the purpose of base_footprint? — ROS Answers](https://answers.ros.org/question/208051/what-is-the-purpose-of-base_footprint/)
