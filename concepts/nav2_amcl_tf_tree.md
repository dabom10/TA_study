# Nav2 / AMCL / TF 트리

## 한 줄 요약
AMCL이 `map → odom` TF를 publish하고, 이 체인이 완성되어야 카메라 좌표를 지도 위 좌표로 변환할 수 있다.

---

## TF 트리 구조

```
map
 └── odom          ← AMCL이 publish
      └── base_link   ← odometry 노드가 publish
           ├── camera_frame
           └── lidar_frame   ← robot_state_publisher(URDF)가 publish
```

각 화살표는 누군가 주기적으로 `/tf` 또는 `/tf_static` 토픽에 publish해야 존재한다.
끊기면 그 아래 프레임도 전부 접근 불가.

---

## 핵심 개념

### map 프레임
지도 기준 절대 좌표계. drift 없음. AMCL이 관리.

### odom 프레임
바퀴 엔코더 누적 좌표계. 연속적이고 smooth하지만 시간이 지날수록 drift 발생.

### 왜 두 프레임이 필요한가
odometry만 쓰면 오차가 쌓여서 위치를 잃는다.
- `odom → base_link`: 짧은 시간 정확, drift 발생
- `map → odom`: AMCL이 drift 보정값을 여기에 넣음

---

## AMCL

**Adaptive Monte Carlo Localization** — 입자 필터 기반 위치 추정.

```
입력: 라이다 스캔 + 사전 지도 + 로봇 이동량
출력1: /amcl_pose  (위치 추정값, 다른 노드가 읽기용)
출력2: /tf         (map → odom transform, TF 트리 등록용)
```

동작 순서:
1. initial pose 수신 → 입자를 그 주변에 뿌림
2. 로봇 이동 → 입자도 이동 (odom 기반)
3. 라이다 스캔 ↔ 지도 비교 → 맞는 입자 가중치 증가
4. 낮은 가중치 입자 제거, 높은 가중치 주변 재샘플링
5. 입자들의 평균 = 현재 위치 추정

**initial pose 없으면**: 입자를 어디 뿌려야 할지 몰라서 TF publish 안 함.

### 관련 파라미터
```yaml
tf_broadcast: true   # map→odom TF publish 여부
global_frame_id: "map"
odom_frame_id: "odom"
base_frame_id: "base_link"
```

---

## TF2 Buffer + TransformListener

```python
self.tf_buffer = Buffer()
self.tf_listener = TransformListener(self.tf_buffer, self)
```

- **Buffer**: TF 데이터를 시간순으로 저장하는 창고
- **TransformListener**: `/tf` 토픽을 구독해서 Buffer에 채움

```
/tf 토픽 → TransformListener → tf_buffer → tf_buffer.transform() 호출 시 꺼내 씀
```

### 주의: TransformListener는 절대경로 `/tf`를 구독

```python
# tf2_ros/transform_listener.py (Jazzy)
node.create_subscription(TFMessage, '/tf', ...)        # 절대경로
node.create_subscription(TFMessage, '/tf_static', ...)
```

멀티로봇 환경에서 AMCL이 `/robot8/tf`에 publish하면 TransformListener가 못 받는다.
→ 실행 시 remapping 필요: `-r /tf:=tf -r /tf_static:=tf_static`

---

## Nav2 스택 전체 구조

```
map_server     → 지도 파일 로드
amcl           → map → odom TF publish (localization)
nav2_planner   → 전역 경로 계획
nav2_controller → 경로 추종, cmd_vel publish
nav2_bt_navigator → 행동 트리로 전체 조율
```

`waitUntilNav2Active()` — 위 노드들이 전부 active 상태가 될 때까지 블로킹.

---

## Depth → 지도 좌표 변환 파이프라인

```
픽셀 (x, y) + depth z (mm → m)
        ↓  카메라 내부 파라미터 (K 행렬)
카메라 3D 좌표 (X, Y, Z)
  X = (x - cx) * z / fx
  Y = (y - cy) * z / fy
  Z = z
        ↓  TF transform
지도 좌표 (map frame)
```

K 행렬 (CameraInfo에서 수신):
```
K = [[fx,  0, cx],
     [ 0, fy, cy],
     [ 0,  0,  1]]
```

코드에서:
```python
pt_map = self.tf_buffer.transform(pt_camera, 'map', timeout=Duration(seconds=1.0))
```

---

## 다른 섹션과의 연결
- TF 트리 끊김 에러 → [tf_listener_namespace_mismatch.md](../software/tf_listener_namespace_mismatch.md)
- SLAM과의 차이: AMCL은 기존 지도로 localization, SLAM은 지도를 만들면서 localization → [slam_concepts.md](slam_concepts.md)
- OAK-D depth 이미지 구조 → [depth_rgb_alignment.md](depth_rgb_alignment.md)

## 의문점 / 나중에 파고들 것
- AMCL vs SLAM Toolbox localization 성능 차이
- `map → odom` publish 주기: 스캔 콜백 기반이라 로봇 정지 시 publish 빈도 낮아짐
- `Time()` (시간 0) vs `get_clock().now()` — tf_buffer.transform에서 차이
