# ROS2 워크스페이스 & 패키지 생성 정리

## 전체 작업 순서

```
ros2 pkg create  → 패키지 생성 (코드만 존재, 실행 불가)
     ↓
package.xml 수정 → 의존성 직접 추가
     ↓
rosdep install   → 의존성 설치
     ↓
colcon build     → install/에 실행 가능한 노드 생성
     ↓
source           → PATH, AMENT_PREFIX_PATH에 경로 등록
     ↓
ros2 run         → 환경변수 보고 노드 찾아서 실행
```

---

## ros2 pkg create

```bash
ros2 pkg create --build-type ament_python --license Apache-2.0 --node-name beep_node turtlebot4_beep
```

| 옵션 | 의미 |
|------|------|
| `--build-type` | 빌드 시스템 선택 (ament_python / ament_cmake) |
| `--license` | 라이선스 지정 (미지정 시 TODO로 채워짐) |
| `--node-name` | 기본 노드 파일 자동 생성 (미지정 시 직접 생성 필요) |

### --build-type 비교

| 옵션 | 언어 | 특징 |
|------|------|------|
| `ament_cmake` | C++ | 컴파일 필요, 실행 속도 빠름 |
| `ament_python` | Python | 컴파일 불필요, 작성 편함 |

### ament_python 생성 구조

```
turtlebot4_beep/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/turtlebot4_beep
└── turtlebot4_beep/
    ├── __init__.py
    └── beep_node.py     ← --node-name 으로 지정한 노드 파일
```

생성된 노드 기본 틀:

```python
import rclpy
from rclpy.node import Node

class BeepNode(Node):
    def __init__(self):
        super().__init__('beep_node')

def main(args=None):
    rclpy.init(args=args)
    node = BeepNode()
    rclpy.spin(node)
    rclpy.shutdown()
```

### 패키지 이름 규칙

- 소문자 + 언더스코어(`_`)
- `ros2 run turtlebot4_beep beep_node` 처럼 패키지 이름으로 참조됨

---

## colcon build

### 생성되는 디렉토리

```
~/ros2_ws/
├── src/         ← 소스코드
├── build/       ← 컴파일 중간 산출물 (.o 파일 등)
├── install/     ← 최종 결과물. ros2 run이 여기서 찾음
└── log/         ← 빌드 로그
```

**`install/` 구조:**
```
install/my_package/
├── lib/my_package/my_node   ← 실행 가능한 노드
├── share/my_package/        ← launch 파일, 설정 파일
└── local_setup.bash
```

**`log/` 활용:** 빌드 에러 시 터미널 출력보다 더 상세한 정보 확인 가능

---

## source install/setup.bash

colcon build로 `install/`에 파일이 생겼어도 ROS2는 위치를 모른다. `source`로 알려줘야 한다.

```bash
source install/setup.bash
ros2 run my_package my_node   # 정상 실행

# source 안 하면:
# → "Package 'my_package' not found" 에러
```

**`source` vs `bash` 실행 차이:**
- `bash 파일.sh` → 새 프로세스에서 실행 → 현재 터미널에 환경변수 안 남음
- `source 파일.sh` → 현재 터미널에 직접 적용 → 환경변수 남음

터미널 새로 열면 다시 해야 함. 매번 치기 귀찮으면:

```bash
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

### PATH & AMENT_PREFIX_PATH

`source install/setup.bash` 실행 시 두 환경변수에 경로 추가됨:

| 변수 | 역할 |
|------|------|
| `PATH` | OS가 실행파일 탐색하는 경로 목록 |
| `AMENT_PREFIX_PATH` | ROS2 전용. `ros2 run/launch/topic` 등이 패키지 찾을 때 사용 |

```bash
# 누적 방식 (여러 번 source 가능)
source /opt/ros/humble/setup.bash   # ROS2 기본 경로
source ~/ros2_ws/install/setup.bash # 내 워크스페이스 경로 추가
```

---

## 참고

- 패키지 생성 후 `package.xml`에 의존성 직접 추가 → `rosdep install` → `colcon build` 순서
- `install/`이 실제로 신경 쓸 디렉토리 — `ros2 run`, `ros2 launch`는 전부 여기서 실행
