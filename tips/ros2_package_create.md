# ROS2 패키지 생성 정리

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu (ROS2 환경) |
| 관련 도구 | ros2 pkg create |

---

## ros2 pkg create 기본 구조

```bash
ros2 pkg create --build-type ament_python --license Apache-2.0 --node-name beep_node turtlebot4_beep
```

| 옵션 | 의미 |
|------|------|
| `--build-type` | 빌드 시스템 선택 (ament_python / ament_cmake) |
| `--license` | 라이선스 지정 |
| `--node-name` | 기본 노드 파일 자동 생성 |
| `turtlebot4_beep` | 패키지 이름 |

---

## --build-type

| 옵션 | 언어 | 특징 |
|------|------|------|
| `ament_cmake` | C++ | 컴파일 필요, 실행 속도 빠름 |
| `ament_python` | Python | 컴파일 불필요, 작성 편함 |

### ament_python 선택 시 생성되는 구조

```
turtlebot4_beep/
├── package.xml
├── setup.py             ← Python 패키지 설정 (CMakeLists.txt 대신)
├── setup.cfg
├── resource/
│   └── turtlebot4_beep
└── turtlebot4_beep/
    ├── __init__.py
    └── beep_node.py     ← --node-name 으로 지정한 노드 파일
```

---

## --node-name

기본 노드 파일을 자동 생성해주는 옵션.
지정하지 않으면 노드 파일이 만들어지지 않아 직접 생성해야 합니다.

생성된 노드 파일 기본 틀:

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

if __name__ == '__main__':
    main()
```

---

## --license

패키지 라이선스 지정. `package.xml` 과 각 파일 상단 주석에 자동으로 명시됩니다.
지정하지 않으면 `TODO: License declaration` 으로 채워집니다.

---

## 패키지 이름 네이밍 컨벤션

- 소문자 + 언더스코어(`_`) 사용
- `ros2 run turtlebot4_beep beep_node` 처럼 패키지 이름으로 참조됨

---

## 참고

- 패키지 생성 후 `package.xml` 을 열어 필요한 의존성 직접 추가 필요
- 생성 직후에는 코드만 존재하며, `colcon build` 해야 실행 가능한 노드가 생성됨
