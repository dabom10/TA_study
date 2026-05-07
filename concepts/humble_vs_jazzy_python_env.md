# Humble vs Jazzy — Python 환경 & 패키지 버전 차이

## 한 줄 요약
Jazzy(Ubuntu 24.04)는 Python 패키지 관리 방식이 바뀌고, 공식 의존성 버전이 명시되어 있으며, Humble 코드 일부가 그대로 실행되지 않는다.

> 검증: [docs.ros.org/en/rolling/Releases/Release-Jazzy-Jalisco.html](https://docs.ros.org/en/rolling/Releases/Release-Jazzy-Jalisco.html) — Ubuntu 24.04 기준 버전 일치 확인

---

## 공식 의존성 버전 비교 (Ubuntu 기준)

| 패키지 | Humble (Ubuntu 22.04) | Jazzy (Ubuntu 24.04) |
|--------|----------------------|----------------------|
| Python | 3.10 | 3.12.3 |
| NumPy  | 1.21.x | **1.26.4** |
| OpenCV | 4.5.x | **4.6.0** |
| CMake  | 3.22 | 3.28.3 |

Jazzy 공식 버전과 다른 버전이 설치되면 ROS2 패키지(특히 `cv_bridge`)와 충돌 가능.

---

## 코드 호환성 차이

### tf2_geometry_msgs import 패턴

```python
# 불필요한 직접 import (do_transform_point를 실제로 호출하지 않는 경우)
from tf2_geometry_msgs.tf2_geometry_msgs import do_transform_point

# 충분한 방법 (tf_buffer.transform()이 PointStamped 등을 처리하려면 타입 등록 필요)
import tf2_geometry_msgs
```

`tf_buffer.transform()`이 geometry_msgs 타입을 처리하려면 `import tf2_geometry_msgs`로 타입을 등록해야 함. `do_transform_point`를 직접 호출하지 않는 코드라면 `import tf2_geometry_msgs`로 충분.

> 미검증: geometry2 jazzy CHANGELOG에 이 import 경로가 공식적으로 deprecated됐다는 명시 없음. 코드 동작 기준으로 서술.

### 그 외 주요 변경

| 항목 | Humble | Jazzy |
|------|--------|-------|
| cmd_vel 메시지 | `Twist` | `TwistStamped` (enable_stamped_cmd_vel 파라미터) |
| BehaviorTree.CPP | 3.8 | 4.5+ (BT XML 형식 변경) |
| Nav2 기본 로컬 플래너 | DWB | MPPI (TurtleBot4 기준) |
| TurtleBot4 패키지 | ros-humble-turtlebot4-* | ros-jazzy-turtlebot4-* |

---

## Ubuntu 24.04의 pip 관리 방식 변화

### PEP 668 — externally-managed-environment

Ubuntu 24.04부터 시스템 Python에 pip로 직접 설치하면 아래 오류가 뜸:

```
error: externally-managed-environment
```

**이유:** pip가 apt로 설치된 패키지를 덮어쓰면 시스템이 불안정해질 수 있어서 Ubuntu가 기본 차단.

**`--break-system-packages` 플래그:**
```bash
pip install 패키지명 --break-system-packages
pip uninstall 패키지명 --break-system-packages
```

차단을 무시하고 시스템 Python에 강제 설치/삭제. 이름이 무섭지만 **apt에 없는 패키지 하나를 추가할 때는 실제로 큰 위험 없음.**

진짜 위험한 경우: pip가 이미 apt로 설치된 패키지의 버전을 의존성으로 **덮어쓸 때**.

---

## 실제로 발생한 버전 충돌 사례

### ultralytics 설치 후 numpy 버전 충돌

```bash
pip install ultralytics --break-system-packages
```

이 명령 하나로 두 가지 apt 패키지가 pip 버전으로 교체됨:

| 패키지 | apt 버전 (Jazzy 공식) | pip 교체 후 |
|--------|----------------------|-------------|
| numpy | 1.26.4 | **2.4.4** ← 문제 |
| opencv | 4.6.0 | **4.13.0** ← 무해 |

`cv_bridge`는 NumPy 1.x 기준으로 컴파일된 C++ 바인딩을 포함하고 있어서 NumPy 2.x 환경에서 실행 시 crash 위험.

**증상:** import는 성공하지만 아래 경고 출력
```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.4.4 as it may crash.
```

**해결:**
```bash
# Jazzy 공식 버전으로 고정
pip install "numpy==1.26.4" --break-system-packages

# pip opencv 제거 → apt의 4.6.0 복원
pip uninstall opencv-python -y --break-system-packages
```

OpenCV는 4.13 → 4.6으로 내려도 API 하위 호환 유지되므로 코드 수정 불필요.

---

## 최종 설치 상태 (검증 완료)

```bash
python3 -c "
import numpy; print('numpy:', numpy.__version__)       # 1.26.4
import cv2; print('opencv:', cv2.__version__)           # 4.6.0
from cv_bridge import CvBridge; print('cv_bridge: OK')
import ultralytics; print('ultralytics: OK')
"
```

---

## 다른 섹션과의 연결

- [`humble_vs_jazzy_fastdds.md`](humble_vs_jazzy_fastdds.md) — DDS/통신 계층 차이
- [`cvbridge_and_ros2_image.md`](cvbridge_and_ros2_image.md) — cv_bridge 상세 개념
- [`virtual_environment_concepts.md`](virtual_environment_concepts.md) — venv/pip 격리 개념
