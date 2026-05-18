# TurtleBot4 Gazebo 시뮬레이션에 로봇 미표시

## 환경

- OS: Ubuntu 24.04
- ROS2: Jazzy

## 문제 상황

`ros2 launch nav2_minimal_tb4_sim simulation.launch.py` 실행 시 Gazebo 월드는 열리지만 로봇이 보이지 않음.  
이후 `ros2 launch turtlebot4_gz_bringup turtlebot4.launch.py` 시도 시 파일 없음 에러 발생.

```
file 'turtlebot4.launch.py' was not found in the share directory of package 'turtlebot4_gz_bringup'
```

## 원인

1. **`turtlebot4-simulator` 패키지 미설치** — `turtlebot4-gz-bringup`, `turtlebot4-gz-toolbox`, `turtlebot4-gz-gui-plugins` 등 Gazebo 시뮬레이터 패키지 전체가 없었음
2. **launch 파일명 오류** — 설치 후 올바른 파일명은 `turtlebot4_gz.launch.py`이며 `turtlebot4.launch.py`는 존재하지 않음

## 진단 순서

```bash
# 1. 설치된 turtlebot4 관련 패키지 확인
apt list --installed 2>/dev/null | grep turtlebot4

# 2. turtlebot4_gz_bringup 패키지의 실제 launch 파일 목록 확인
ls /opt/ros/jazzy/share/turtlebot4_gz_bringup/launch/
# → sim.launch.py, turtlebot4_gz.launch.py, turtlebot4_spawn.launch.py 등
```

## 해결 방법

```bash
# 1. turtlebot4-simulator 메타패키지 설치
sudo apt install ros-jazzy-turtlebot4-simulator

# 2. 올바른 launch 파일명으로 실행 (turtlebot4_gz.launch.py)
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py
```

기본 world는 `warehouse`. 변경 시:

```bash
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py world:=depot
```

> **주의**: `.venv` 가상환경이 활성화된 상태(`(.venv)` 프롬프트)에서 실행하면 Gazebo 플러그인 로딩 충돌이 발생할 수 있음. `deactivate` 후 실행할 것.

## 참고

> 검증: `apt list --installed | grep turtlebot4-gz` — 출력 없음으로 미설치 확인  
> 검증: `ls /opt/ros/jazzy/share/turtlebot4_gz_bringup/launch/` — `turtlebot4_gz.launch.py` 존재, `turtlebot4.launch.py` 없음 확인

- `turtlebot4-desktop` 메타패키지에는 시뮬레이터가 포함되지 않음 — `turtlebot4-simulator`를 별도 설치해야 함
- `nav2_minimal_tb4_sim`으로도 TurtleBot4 시뮬레이션 가능하나, 로봇 모델이 `nav2_minimal_tb4_description` 기준이라 실제 TurtleBot4 외관과 다름
