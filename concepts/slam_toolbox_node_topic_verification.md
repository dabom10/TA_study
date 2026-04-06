# slam_toolbox 노드-토픽 관계 실습 검증

## 개념

SLAM 런치파일 실행 → slam_toolbox 패키지의 특정 노드가 실행됨 → 그 노드가 특정 토픽을 구독/발행

```
[slam.launch.py]
    └─ 노드 실행: /slam_toolbox (async_slam_toolbox_node 또는 sync_slam_toolbox_node)
            ├─ Subscribe: /scan (LiDAR), /tf, /tf_static, /odom
            └─ Publish:  /map, /slam_toolbox/scan_visualization, ...
```

---

## 실습 검증 순서

### Step 1: 런치 전 노드 목록

```bash
ros2 node list
```

→ `/slam_toolbox` 없음 확인

---

### Step 2: SLAM 런치 실행

```bash
ros2 launch turtlebot4_navigation slam.launch.py
```

---

### Step 3: 런치 후 노드 목록

```bash
ros2 node list
```

→ `/slam_toolbox` 생겼는지 확인

**결과:**
```
# 여기에 실습 결과 기록
```

---

### Step 4: 노드 상세 정보 (pub/sub/service)

```bash
ros2 node info /slam_toolbox
```

→ 어떤 토픽을 Subscribe/Publish하는지 확인

**결과:**
```
# 여기에 실습 결과 기록
```

---

### Step 5: 특정 토픽 발행자 확인 (역방향 검증)

```bash
ros2 topic info /map
ros2 topic info /scan
```

→ `/map` publisher가 `/slam_toolbox`인지, `/scan` subscriber가 `/slam_toolbox`인지 확인

**결과:**
```
# 여기에 실습 결과 기록
```

---

### Step 6: 전체 그래프 시각화

```bash
rqt_graph
```

→ Nodes/Topics (all) 선택 → 화살표로 노드-토픽 관계 확인

---

### Step 7: 런치파일 소스 확인 (코드 대조)

```bash
find /opt/ros/humble -name "slam.launch.py" 2>/dev/null
```

→ 실제 어떤 노드를 어떤 파라미터로 실행하는지 코드와 대조

**런치파일 위치:**
```
# 여기에 경로 기록
```

---

## 확인된 관계 요약

> 실습 후 채우기

| 방향 | 토픽 | 역할 |
|------|------|------|
| Subscribe | `/scan` | LiDAR 포인트 데이터 수신 |
| Subscribe | `/tf`, `/tf_static` | 좌표 변환 |
| Subscribe | `/odom` | 주행 거리계 |
| Publish | `/map` | 생성된 OGM 지도 |
| Publish | `/slam_toolbox/scan_visualization` | 스캔 시각화 |

---

## 참고

- `ros2 node info` : 노드 기준으로 토픽 확인
- `ros2 topic info` : 토픽 기준으로 노드 확인 (역방향)
- `rqt_graph` : 전체 그래프 시각화
