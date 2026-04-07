# ROS2 통신 개념 정리: Topic / Service / Action, 동기/비동기, QoS

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| ROS2 | Humble |

---

## 동기 vs 비동기

| | 동기 (sync) | 비동기 (async) |
|--|------------|---------------|
| 특징 | 응답 올 때까지 기다림 | 요청 보내고 바로 다음 코드 실행 |
| 비유 | 전화 통화 | 문자 보내기 |

---

## Topic / Service / Action 비교

```
Topic   : 편지함 (구독자가 알아서 가져감, 단방향)
Service : 전화 (요청→즉시응답, 짧은 작업)
Action  : 택배 (요청→진행중피드백→완료알림, 긴 작업)
```

| 항목 | Topic | Service | Action |
|------|-------|---------|--------|
| 방향 | 단방향 | 양방향 | 양방향 |
| 응답 | 없음 | 즉시 1회 | 완료시 1회 |
| 피드백 | 없음 | 없음 | 있음 (진행 중) |
| 취소 | 불가 | 불가 | 가능 |
| 적합한 상황 | 센서 데이터 스트림 | 파라미터 조회, 짧은 계산 | 이동, 도킹 등 시간 걸리는 작업 |
| 동기/비동기 | 해당 없음 | 기본 동기, 비동기도 가능 | 비동기 (기다리지 않아도 됨) |

---

## Action 상세

### 흐름

```
내 노드                    Action Server (로봇)
   │                            │
   │──── send_goal ────────────→│  (목표 전달)
   │                            │ 처리 중...
   │←─── feedback ─────────────│  (진행상황 계속 전송)
   │←─── feedback ─────────────│
   │                            │ 완료!
   │←─── result ───────────────│  (최종 결과)
```

- 기다리는 동안 내 노드는 다른 일 가능
- 중간에 취소 가능 (`cancel_goal`)
- `call()`로 service를 호출하면 완료될 때까지 노드 전체가 블로킹 (동기)
- `call_async()`로 호출하면 Future 반환 후 즉시 리턴 (비동기) — 단, 콜백 안에서는 call() 사용 시 데드락 위험

### Goal 전송 방법

#### CLI
```bash
# 기본
ros2 action send_goal /robot1/undock irobot_create_msgs/action/Undock "{}"

# feedback 실시간으로 보기
ros2 action send_goal --feedback /robot1/undock irobot_create_msgs/action/Undock "{}"
```

#### Python (rclpy)
```python
from rclpy.action import ActionClient
client = ActionClient(node, Undock, '/robot1/undock')
client.send_goal_async(goal_msg)   # 비동기 (권장)
```

### Goal 데이터 예시

```bash
# 파라미터 없는 경우 (Undock, Dock)
ros2 action send_goal /robot1/undock irobot_create_msgs/action/Undock "{}"

# 파라미터 있는 경우
ros2 action send_goal /robot1/spin irobot_create_msgs/action/Spin "{angle: 1.57}"

ros2 action send_goal /robot1/drive_distance irobot_create_msgs/action/DriveDistance "{
  distance: 0.5,
  max_translation_speed: 0.3
}"

ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{
  pose: {
    header: {frame_id: 'map'},
    pose: {
      position: {x: 1.0, y: 2.0, z: 0.0},
      orientation: {w: 1.0}
    }
  }
}"
```

### Action 타입 구조 확인

```bash
ros2 interface show irobot_create_msgs/action/DriveDistance
```

출력:
```
float32 distance               # goal
float32 max_translation_speed
---
float32 total_distance_traveled  # result
---
float32 distance_traveled        # feedback
```

`---` 구분선으로 goal / result / feedback 세 파트로 나뉨.

### CLI 서브커맨드

| 서브커맨드 | 역할 |
|-----------|------|
| `send_goal` | goal 전송 |
| `list` | 현재 활성화된 action server 목록 |
| `info` | 특정 action 상세 정보 |
| `type` | action 타입 확인 |

---

## 토픽 리매핑 (`--ros-args -r`)

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/robot1/cmd_vel
```

| 부분 | 의미 |
|------|------|
| `--ros-args` | 이후는 ROS2 전용 인자임을 선언 |
| `-r /cmd_vel:=/robot1/cmd_vel` | 토픽 리매핑 |
| `-p param:=value` | 파라미터 설정 |

소스코드 안 바꾸고 토픽 이름만 바꿔치기하는 것.

```
기본:  teleop → /cmd_vel          → 로봇이 안 들음 ❌
리매핑: teleop → /robot1/cmd_vel  → 로봇이 들음 ✓
```

### 버전별 차이

| ROS2 버전 | 방식 |
|-----------|------|
| Dashing, Eloquent | `--remap /cmd_vel:=/robot1/cmd_vel` |
| Foxy 이후 (현재) | `--ros-args -r /cmd_vel:=/robot1/cmd_vel` |

launch 파일에서는 `--ros-args` 없이 `remappings` 인자로 씀:
```python
Node(
    package='teleop_twist_keyboard',
    executable='teleop_twist_keyboard',
    remappings=[('/cmd_vel', '/robot1/cmd_vel')]
)
```

---

## QoS Durability (Transient Local)

| 옵션 | 동작 |
|------|------|
| `Volatile` (기본값) | 구독 전 데이터 버림 |
| `Transient Local` | 마지막 N개 메시지 보존 → 늦게 구독해도 받음 |

```python
QoSProfile(
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1   # 마지막 1개 보존
)
```

### /map 토픽에 Transient Local을 쓰는 이유

맵은 자주 바뀌지 않는 데이터 — SLAM이 처음 한 번 발행하면 끝.  
늦게 뜬 노드도 받을 수 있어야 하므로 map 토픽은 관례적으로 Transient Local 사용.

반면 `/scan`, `/odom` 같은 센서 데이터는 Volatile — 옛날 데이터 필요 없음.

### map_saver_cli에서의 활용

```bash
ros2 run nav2_map_server map_saver_cli -f "<map_name>" \
  --ros-args -p map_subscribe_transient_local:=true -r __ns:=/robot1
```

- `-p map_subscribe_transient_local:=true` : 구독 측 QoS를 Transient Local로 맞춰줌
- SLAM이 먼저 실행된 경우에도 마지막 `/map` 메시지를 받아서 저장 가능

---

## map_saver_cli 저장 결과

실행 후 두 파일 생성:

### `<map_name>.yaml`
```yaml
image: first_map.pgm
resolution: 0.05           # 1픽셀 = 5cm
origin: [-1.23, -2.34, 0]  # 맵 원점 (실제 좌표)
negate: 0
occupied_thresh: 0.65      # 이 값 이상이면 장애물
free_thresh: 0.25          # 이 값 이하면 빈 공간
```

### `<map_name>.pgm`
- 흑백 이미지 (PGM = Portable Gray Map)
- 흰색 = 빈 공간, 검은색 = 장애물, 회색 = 미탐색

두 파일은 항상 같은 디렉토리에 있어야 함 (yaml이 pgm을 참조).

### 불러올 때

```bash
ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=<map_name>.yaml
```

---

## ROS2 Bag

**특정 시점의 토픽 데이터를 통째로 녹화해뒀다가 나중에 똑같이 재발행하는 파일.**  
"그 순간의 로봇 세계를 얼려둔 것" — 알고리즘은 실제 로봇 데이터인지 bag인지 구분하지 못한다.

### 핵심 용도: 로봇 없이 개발/테스트

```
1. 로봇으로 한 번 주행하며 bag 녹화
2. 이후 ros2 bag play 만 실행
3. 카메라, IMU, odom 등이 그 순간 그대로 재발행
```

| 상황 | bag 없이 | bag 있으면 |
|------|----------|------------|
| 알고리즘 반복 테스트 | 매번 로봇 주행 필요 | `ros2 bag play` 한 번 |
| 환경 재현 | 불가능 | 동일 데이터로 항상 재현 |
| 디버깅 | 실시간만 가능 | 원하는 구간 반복 재생 |

### 주의사항

- bag에 `cmd_vel`이 포함되면 **로봇이 실제로 움직임**
- 센서 데이터만 재생하려면 `--topics`로 선택

### 기본 명령어

```bash
# 녹화
ros2 bag record -o <저장경로> <토픽1> <토픽2> ...
ros2 bag record -o <저장경로> -a        # 전체 토픽

# 재생
ros2 bag play <bag경로>
ros2 bag play <bag명> --topics /robot8/scan /robot8/odom   # 특정 토픽만
ros2 bag play <bag명> --rate 0.5                           # 0.5배속

# 정보 확인
ros2 bag info <bag경로>
```

**파일 포맷:** sqlite3 (`.db3`) 또는 MCAP + `metadata.yaml` (토픽 목록, 메시지 수 등)
