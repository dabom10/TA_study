# colcon build 및 ROS2 워크스페이스 구조 정리

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu (ROS2 환경) |
| 관련 도구 | colcon, ROS2 |

---

## 전체 흐름

```
패키지 생성   → 코드만 존재 (실행 불가)
     ↓
colcon build  → install/에 실행 가능한 노드 생성
     ↓
source        → PATH, AMENT_PREFIX_PATH에 경로 등록
     ↓
ros2 run      → 환경변수 보고 노드 찾아서 실행
```

---

## colcon build 후 생성되는 디렉토리

### `build/`

컴파일 중간 과정에서 생기는 파일들 저장

```
build/
└── my_package/
    ├── CMakeFiles/        ← CMake가 생성한 빌드 설정
    ├── my_node.cpp.o      ← .cpp를 컴파일한 오브젝트 파일
    └── Makefile           ← 실제 컴파일 명령 목록
```

- `.cpp` → 컴파일 → `.o` (오브젝트 파일) → 링킹 → 실행파일
- 최종 결과물이 아닌 중간 산출물
- 재빌드 시 변경된 파일만 다시 컴파일하는 데 사용 (빌드 속도 향상)

### `install/`

빌드가 끝난 최종 결과물 저장. ROS2가 실제로 여기서 파일을 참조

```
install/
└── my_package/
    ├── lib/my_package/my_node   ← 실행 가능한 노드
    ├── share/my_package/        ← launch 파일, 설정 파일 등
    └── local_setup.bash         ← 환경변수 설정 파일
```

- `ros2 run my_package my_node` 실행 시 여기서 찾음
- `source install/setup.bash` 를 해야 ROS2가 이 디렉토리를 인식

### `log/`

빌드 과정의 기록 저장

```
log/
└── build_2026-04-01_12-00-00/
    ├── my_package/
    │   ├── stdout_stderr.log   ← 빌드 출력 전체
    │   └── command.log         ← 실행된 명령어 기록
    └── logger_all.log          ← 전체 빌드 로그
```

- 빌드 에러 발생 시 원인 파악에 사용
- 터미널에 출력된 것보다 더 상세한 정보 포함

---

## source install/setup.bash

### 왜 필요한가?

`colcon build` 로 `install/` 에 실행파일이 생겼어도 ROS2는 그 파일이 어디 있는지 모릅니다.
`source install/setup.bash` 는 **"여기 있는 패키지들을 ROS2에 알려주는"** 명령어입니다.

### source 안 하면?

```bash
ros2 run my_package my_node
# → "Package 'my_package' not found" 에러
```

### source 하면?

```bash
source install/setup.bash
ros2 run my_package my_node
# → 정상 실행
```

### `source` 명령어란?

```bash
source 파일명   # = . 파일명
```

- 일반 `bash 파일.sh` 실행 → 새 프로세스에서 실행 → 터미널에 환경변수 안 남음
- `source 파일.sh` 실행 → 현재 터미널에 직접 적용 → 환경변수 남음

### 터미널 새로 열면 다시 해야 함

`source` 는 현재 터미널에만 적용되므로 매번 실행 필요.
매번 치기 귀찮으면 `~/.bashrc` 에 추가:

```bash
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

---

## PATH와 AMENT_PREFIX_PATH

### PATH란?

OS가 명령어 실행 시 실행파일을 찾는 경로 목록 (콜론으로 구분)

```bash
echo $PATH
# /usr/bin:/usr/local/bin:/opt/ros/humble/bin:...
```

명령어 실행 시 왼쪽부터 순서대로 탐색:

```
git 실행
→ /usr/bin 에 있나? → 있음 → 실행
→ 없으면 다음 경로로...
```

`source install/setup.bash` 후 내 노드 경로가 PATH에 추가됨:

```bash
PATH=/home/rokey/ros2_ws/install/my_package/lib/my_package:$PATH
```

### AMENT_PREFIX_PATH란?

ROS2 전용 환경변수. ROS2 명령어들이 패키지를 찾을 때 사용

```bash
AMENT_PREFIX_PATH=/home/rokey/ros2_ws/install/my_package
# → "ROS2야, my_package는 여기 있어"
```

`ros2 run`, `ros2 topic`, `ros2 launch` 등이 이 변수를 참조

### source 할 때마다 경로가 누적됨

```bash
source /opt/ros/humble/setup.bash   # ROS2 기본 경로 추가
source ~/ros2_ws/install/setup.bash # 내 워크스페이스 경로 추가
# → PATH에 두 경로 모두 등록됨
```

---

## 참고

- `install/` 이 실제로 신경 쓸 디렉토리 — `ros2 run`, `ros2 launch` 는 전부 여기서 실행
- 패키지 생성 → 코드만 존재, 빌드해야 비로소 실행 가능한 노드가 생성됨
