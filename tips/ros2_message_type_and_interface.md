# ROS2 메시지 타입과 Interface 개념 정리

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| ROS2 | Humble |
| 참고 코드 | turtlebot4_beep/beep_node.py |

---

## 개념 정리

### ROS2 노드 통신의 구조

```
어떤 방식으로?  →  토픽 (/robot8/cmd_audio)
어떤 형식으로?  →  메시지 타입 (AudioNoteVector)
어떤 데이터를?  →  필드 (notes, append, ...)
```

노드들은 토픽으로 데이터를 주고받고, 그 데이터의 형식(틀)을 **메시지 타입**이라고 한다.
메시지 타입은 `.msg` 파일로 정의된다.

---

### Interface란

ROS2에서 데이터 형식을 정의한 것. 3가지 종류가 있다:

| 종류 | 디렉토리 | 용도 |
|------|----------|------|
| Message | `msg/` | 단방향 데이터 전송 (토픽) |
| Service | `srv/` | 요청/응답 |
| Action | `action/` | 장시간 작업 + 피드백 |

패키지 구조:
```
irobot_create_msgs/
├── msg/
│   ├── AudioNoteVector.msg
│   └── AudioNote.msg
├── srv/
└── action/
```

---

## 메시지 타입 확인 방법

### 1. 토픽에서 타입 확인
```bash
ros2 topic info /robot8/cmd_audio
# → Type: irobot_create_msgs/msg/AudioNoteVector
```

### 2. 메시지 구조 확인
```bash
ros2 interface show irobot_create_msgs/msg/AudioNoteVector
```

출력:
```
std_msgs/Header header
    builtin_interfaces/Time stamp
        int32 sec
        uint32 nanosec
    string frame_id
irobot_create_msgs/AudioNote[] notes
    uint16 frequency
    builtin_interfaces/Duration max_runtime
        int32 sec
        uint32 nanosec
bool append
```

들여쓰기 = 그 위 타입의 내부 필드.
**`/`가 붙은 타입명 = 별도로 import해야 하는 것.**

### 3. 전체 목록 확인
```bash
ros2 interface list        # 전체
ros2 interface list -m     # msg만
ros2 interface list -s     # srv만
ros2 interface list -a     # action만
```

---

## Python import 방법

`패키지/msg/타입` → `from 패키지.msg import 타입`

```python
from irobot_create_msgs.msg import AudioNoteVector, AudioNote
from builtin_interfaces.msg import Duration
```

- `interface show` 출력에서 `/`가 붙은 타입은 모두 import 대상
- pub/sub 둘 다 메시지 타입을 import해야 함

```python
# publish
self.pub = self.create_publisher(AudioNoteVector, '/cmd_audio', 10)

# subscribe
self.sub = self.create_subscription(Odometry, '/odom', self.callback, 10)
```

---

## package.xml 의존성 추가

import한 패키지를 `package.xml`에 등록:

```xml
<exec_depend>irobot_create_msgs</exec_depend>
<exec_depend>builtin_interfaces</exec_depend>
```

---

## Header 필드

```
std_msgs/Header header
    builtin_interfaces/Time stamp   ← 타임스탬프
    string frame_id                 ← 좌표계 이름
```

header는 **"이 데이터가 언제, 어느 기준으로 측정된 건지"** 가 중요할 때 사용.

| 상황 | header 필요 여부 |
|------|----------------|
| 단순 명령 (소리, 이동 등) | 불필요 |
| 센서 데이터 동기화 | 필요 (stamp로 시점 비교) |
| 좌표 변환 (TF) | 필요 (frame_id로 기준 좌표계 판단) |
| 여러 센서 융합 | 필요 |

값만 읽는 경우 (odom 위치, battery 상태 등)는 header를 무시해도 됨.
비워두면 ROS2가 기본값(0, 빈 문자열)으로 채워줌.

---

## beep_node.py 코드 분석

```python
class BeepNode(Node):
    def __init__(self):
        super().__init__('beep_node')
        # AudioNoteVector 형식으로 /robot8/cmd_audio 토픽에 퍼블리셔 생성
        self.pub = self.create_publisher(AudioNoteVector, '/robot8/cmd_audio', 10)
        # 1초 후 timer_callback 호출하는 타이머 등록 (반복)
        self.timer = self.create_timer(1, self.timer_callback)

    def timer_callback(self):
        msg = AudioNoteVector()
        msg.append = False  # 현재 재생 중인 소리 덮어씀
        msg.notes = [
            AudioNote(frequency=880, max_runtime=Duration(sec=0, nanosec=300_000_000)),
            ...
        ]
        self.pub.publish(msg)   # 메시지 전송
        self.timer.cancel()     # 타이머 취소 → 한 번만 실행
```

### main 흐름

```python
rclpy.init(args=args)                        # ROS2 초기화
node = BeepNode()                            # 노드 생성 + 타이머 등록
rclpy.spin_once(node, timeout_sec=3)         # 콜백 한 번 처리 (최대 3초 대기)
node.destroy_node()                          # 노드 객체 정리
rclpy.shutdown()                             # ROS2 컨텍스트 전체 종료
```

| 단계 | 설명 |
|------|------|
| `BeepNode()` | 타이머를 **등록**만 함, 콜백은 아직 실행 안 됨 |
| `spin_once` | 1초 기다렸다가 timer_callback 실행, 리턴 |
| `destroy_node` | 이 노드 객체만 정리 |
| `shutdown` | rclpy.init()으로 켠 ROS2 시스템 전체 종료 |

### spin 종류

| 함수 | 동작 |
|------|------|
| `spin(node)` | 콜백 무한 처리 (Ctrl+C로만 종료) |
| `spin_once(node, timeout_sec=N)` | 콜백 한 번 처리 후 리턴, 최대 N초 대기 |

---

## 참고

```bash
ros2 interface show irobot_create_msgs/msg/AudioNoteVector
ros2 topic info /robot8/cmd_audio
```
