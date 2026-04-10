# rosdep install 명령어와 apt 개념 정리

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu (ROS2 환경) |
| 관련 도구 | rosdep, apt |

---

## rosdep install --from-paths src --ignore-src -r -y

### 옵션별 의미

| 옵션 | 의미 |
|------|------|
| `install` | 의존성 패키지를 설치 |
| `--from-paths src` | `src` 디렉토리 안의 패키지들을 탐색 |
| `--ignore-src` | `src` 안에 소스코드로 이미 있는 패키지는 설치 대상에서 제외 |
| `-r` | 에러가 나도 멈추지 않고 계속 진행 (continue on error) |
| `-y` | 설치 확인 프롬프트에 자동으로 yes 응답 |

### 실행 위치

워크스페이스 루트에서 실행해야 합니다:

```
~/ros2_ws/          ← 여기서 실행
├── src/            ← package.xml들이 여기 있음
├── build/
└── install/
```

---

## 의존성 패키지란?

**"내 코드가 동작하려면 미리 설치되어 있어야 하는 다른 패키지"**

예시:
```
내 패키지
├── OpenCV 필요 (이미지 처리)
├── sensor_msgs 필요 (ROS 메시지 타입)
└── rclcpp 필요 (ROS2 C++ 라이브러리)
```

---

## package.xml을 찾는 이유

`rosdep`은 소스코드(`#include` 등)를 직접 분석하지 않습니다.
`package.xml`의 `<depend>` 태그를 읽어서 무엇을 설치할지 결정합니다.

```
src/
└── my_package/
    ├── package.xml   ← "나는 OpenCV, rclcpp가 필요해" 라고 명시
    ├── CMakeLists.txt
    └── src/
        └── main.cpp  ← rosdep은 여기 #include를 읽지 않음
```

### 동작 흐름

```
rosdep --from-paths src
    → src 안의 package.xml 탐색
    → package.xml의 <depend> 태그 읽기
    → 해당 패키지 apt install
```

---

## rosdep install의 정확한 역할

- package.xml에 적힌 의존성 패키지들을 **한 번에 전부 설치**
- 업데이트나 지속적인 관리는 하지 않음
- **"지금 이 순간 필요한 것들을 설치"** 하는 명령어

### 재실행이 필요한 경우

| 상황 | rosdep 재실행 필요? |
|------|---------------------|
| 새 패키지를 src에 추가했을 때 | 필요 |
| 다른 PC에 같은 환경 구축할 때 | 필요 |
| package.xml에 새 의존성 추가됐을 때 | 필요 |
| 이미 설치된 환경에서 빌드만 할 때 | 불필요 |

---

## apt란?

**APT (Advanced Package Tool)** = Ubuntu/Debian 계열 리눅스의 패키지 설치 관리자

```bash
sudo apt install git        # git 설치
sudo apt install python3    # python3 설치
sudo apt install vim        # vim 설치
```

`rosdep`은 내부적으로 apt를 호출합니다:

```
rosdep install
    → package.xml 읽기
    → apt install ros-humble-opencv  ← 이걸 대신 해줌
    → apt install ros-humble-rclcpp
    → ...
```

---

## package.xml은 빌드 결과물이 아니다

`package.xml`은 빌드해서 생성되는 파일이 아니라 **개발자가 직접 작성하는 설정 파일**입니다.

### 패키지 생성 시 자동 생성

```bash
ros2 pkg create --build-type ament_cmake my_package
```

실행하면 기본 틀이 자동으로 생성됩니다:

```
my_package/
├── package.xml        ← 자동 생성 (기본 틀만 있음)
├── CMakeLists.txt     ← 자동 생성
└── src/
```

### 이후 개발자가 직접 의존성 추가

```xml
<depend>rclcpp</depend>
<depend>sensor_msgs</depend>   ← 직접 추가
<depend>OpenCV</depend>        ← 직접 추가
```

### 전체 작업 순서

```
1. ros2 pkg create → package.xml 자동 생성 (기본 틀)
2. package.xml 수정 → 필요한 의존성 직접 추가
3. rosdep install  → package.xml 읽고 의존성 설치
4. colcon build    → 소스코드 컴파일
```

빌드 시 의존성 패키지가 없으면 `#include` 를 못 찾아 **컴파일 에러**가 나기 때문에
반드시 빌드 전에 rosdep으로 의존성을 설치해야 합니다.

---

## 참고

- `package.xml`의 `<depend>` 태그에 의존성을 명시해야 rosdep이 인식
- `rosdep`은 apt의 래퍼(wrapper) 역할을 함
- 빌드(`colcon build`) 결과물은 `build/`, `install/` 폴더 안의 바이너리/라이브러리 파일들

---

## apt vs apt-get

| 항목 | `apt` | `apt-get` |
|------|-------|-----------|
| 출시 | 2014년 (신) | 구버전 |
| 대상 | 사람이 직접 사용 | 스크립트/자동화 |
| 진행률 바 | ✅ | ❌ |
| 출력 안정성 | 버전마다 바뀔 수 있음 | 일정하게 유지됨 |

`apt`는 `apt-get` + `apt-cache` 등 여러 명령어를 합친 사용자 친화적 버전. 기능 자체는 동일하며 둘 다 `/etc/apt/sources.list`를 참조한다.

- **터미널에서 직접** → `apt`
- **Dockerfile, 쉘 스크립트, CI/CD** → `apt-get` (출력 형식이 안정적)

---

## apt vs pip / PEP 668

Ubuntu에서 Python 패키지를 설치할 때 pip보다 apt를 권장하는 이유.

### 왜 pip가 위험한가

Ubuntu 시스템 자체가 Python으로 돌아가는 부분이 있고, apt가 그 환경을 관리함. pip가 거기에 마음대로 덮어쓰면 시스템 도구가 망가질 수 있음.

```
apt install numpy (버전 1.21)   ← 시스템 도구가 이 버전 기준으로 동작
pip install numpy (버전 1.25)   ← apt 모르게 덮어씀 → 시스템 도구 망가짐
```

ROS2 환경에서는 더 위험: rosdep은 apt 기반이라 pip로 설치한 패키지를 인식 못 함 → 버전 불일치 → 빌드 에러.

### PEP 668

이 문제를 막기 위해 Ubuntu 22.04부터 적용된 규격. `/usr/lib/python3.xx/EXTERNALLY-MANAGED` 마커 파일이 있으면 pip가 시스템 Python 설치를 차단함.

```bash
pip3 install numpy
# error: externally-managed-environment
# → apt 써라, 강제하려면 --break-system-packages (비권장)
```

마커 파일이 없어서 에러가 안 뜨는 경우도 있음 (ROS2 설치 가이드 중 삭제하라는 글이 많아서).

### 올바른 설치 방법

| 상황 | 방법 |
|------|------|
| ROS2 관련 패키지 | `sudo apt install ros-humble-패키지명` |
| 일반 Python 패키지 | `sudo apt install python3-패키지명` |
| apt에 없는 경우 | 가상환경(`venv`) 안에서 pip |

> 검증: [PEP 668 공식 문서](https://peps.python.org/pep-0668/) — EXTERNALLY-MANAGED 마커 파일 메커니즘 확인
