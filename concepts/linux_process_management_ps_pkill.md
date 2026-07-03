---
분류: concepts
날짜: 2026-07-03
---

# Linux 프로세스 관리 — `ps`, `pkill`, 좀비, ROS2 launch 정리

## 한 줄 요약
프로세스 목록을 보고(`ps -ef`), 패턴으로 시그널을 보내(`pkill -f`) ROS2 launch가 남긴 잔존/좀비 프로세스를 정리하는 표준 절차 정리.

---

## 1. `ps -ef`

프로세스 상태를 출력하는 명령.

- `ps`: **p**rocess **s**tatus
- `-e`: **e**very — 모든 사용자의 모든 프로세스
- `-f`: **f**ull format — UID, PID, PPID, 시작시각, 커맨드까지 상세 표시

출력 예시:
```
UID    PID   PPID  C STIME TTY      TIME     CMD
rokey  1234  1000  0 10:30 pts/0    00:00:01 /usr/bin/python3 /opt/ros/humble/bin/ros2 launch nav2_bringup ...
```

| 컬럼 | 의미 |
|------|------|
| UID | 프로세스 소유 사용자 |
| PID | 프로세스 ID (kill 대상) |
| PPID | 부모 프로세스 ID |
| C | CPU 사용률 |
| STIME | 시작 시각 |
| TTY | 연결된 터미널 |
| TIME | 누적 CPU 시간 |
| CMD | 실행 커맨드 (전체 라인) |

주로 `grep`과 조합:
```bash
ps -ef | grep nav2 | grep -v grep
```

---

## 2. `pkill -9 -f <패턴>`

이름/패턴으로 프로세스를 찾아 시그널을 보내는 명령.

- `pkill`: **p**rocess **kill** — PID 몰라도 이름·패턴으로 시그널 전송
- `-9`: 시그널 번호 9 = **SIGKILL** (강제 종료, 프로세스가 거부 불가, 정리 과정 없음)
- `-f`: **f**ull command line 매칭 — 프로세스 이름뿐 아니라 **전체 커맨드라인**에서 패턴 검색

### `-f` 있고 없고 차이

프로세스가 이렇게 떠 있다고 하자:
```
PID 1234  python3 /opt/ros/humble/lib/nav2_bringup/navigation_launch.py
```

- `pkill -9 nav2` → **매칭 실패**. 프로세스 이름은 `python3`.
- `pkill -9 -f nav2` → **매칭 성공**. 커맨드라인 전체에 `nav2` 포함.

ROS2 노드들은 실제 실행 파일이 `python3`, `component_container` 등 공통 이름이라 **`-f` 없이는 못 잡는 경우가 대부분**.

---

## 3. 시그널 종류

| 시그널 | 번호 | 의미 | 사용 시점 |
|--------|------|------|-----------|
| SIGINT | 2 | Ctrl+C, 얌전히 종료 요청 | 첫 시도 |
| SIGTERM | 15 | 기본 종료 요청 (프로세스가 정리 후 종료) | 두 번째 |
| SIGKILL | 9 | 강제 종료 (거부 불가, 정리 없음) | 최후의 수단 |

`pkill`은 기본이 SIGTERM. `-9`로 SIGKILL 지정.

---

## 4. 좀비 프로세스

**좀비(zombie)** = 종료됐지만 부모가 `wait()`로 회수하지 않아 프로세스 테이블에 남은 항목. 상태 코드 `Z`.

### 찾기
```bash
# 좀비만 표시
ps axo pid,ppid,stat,comm | awk '$3 ~ /^Z/'

# 좀비 개수
ps axo stat | grep -c '^Z'

# 부모까지 트리로
ps -ef --forest | grep -E 'defunct|<Z>'

# top의 zombie 카운트
top -bn1 | grep zombie
```

### 죽이기 — 좀비는 `kill`이 안 먹는다
이미 죽은 상태이므로 **부모 프로세스**를 처리해야 한다.

```bash
# 부모에게 자식 회수 신호
kill -CHLD <PPID>

# 안 되면 부모를 종료 → init(PID 1)이 좀비를 회수
kill <PPID>
```

---

## 5. ROS2 launch 잔존 프로세스 정리 (nav2 / localization)

`ros2 launch`는 여러 자식 노드를 띄우므로 Ctrl+C 후에도 잔존 프로세스가 흔히 남음.

### 찾기
```bash
# nav2 계열 노드 전부
pgrep -af 'nav2|amcl|bt_navigator|controller_server|planner_server|behavior_server|map_server'

# launch 프로세스만
ps -ef | grep 'ros2 launch' | grep -v grep
```

### `pkill -9 -f nav2`로 잡히는 Nav2 스택 노드

| 프로세스 | 역할 |
|---------|------|
| `bt_navigator` | Behavior Tree 기반 내비게이션 총괄 |
| `controller_server` | 로컬 경로 추종 (DWB 등) |
| `planner_server` | 글로벌 경로 계획 (NavFn/Smac) |
| `behavior_server` | 복구 동작 (spin, backup, wait) |
| `smoother_server` | 경로 스무딩 |
| `waypoint_follower` | 웨이포인트 순차 이동 |
| `velocity_smoother` | cmd_vel 스무딩 |
| `collision_monitor` | 충돌 감시 |
| `lifecycle_manager` | 위 노드들 lifecycle 관리 (`nav2_lifecycle_manager`) |
| `map_server` / `amcl` | localization launch에서 뜨는 노드 (`nav2_map_server`, `nav2_amcl`) |
| `ros2 launch nav2_bringup ...` | 부모 launch 프로세스 |

**안 잡히는 것**: `robot_state_publisher`, `rviz2`, `slam_toolbox`, `create3` 관련 — 커맨드라인에 `nav2` 문자열이 없음.

### 정리 순서 (얌전한 것부터)

```bash
# 1. 미리 확인
pgrep -af nav2

# 2. SIGINT (Ctrl+C 등가)
pkill -INT -f 'ros2 launch.*nav2'
pkill -INT -f 'ros2 launch.*localization'

# 3. SIGTERM
pkill -TERM -f 'nav2|amcl|bt_navigator|controller_server|planner_server|behavior_server|map_server'

# 4. SIGKILL (최후 수단)
pkill -9 -f 'nav2|amcl|bt_navigator|controller_server|planner_server|behavior_server|map_server'

# 5. ROS2 데몬 재시작 (토픽/노드 목록 꼬였을 때)
ros2 daemon stop && ros2 daemon start
```

---

## 6. 주의사항

- `-9`(SIGKILL)는 노드가 DDS 정리(퍼블리셔·구독자 해제)를 못 하고 죽으므로 이후 토픽 목록·데몬 상태가 꼬일 수 있다. 가능하면 `-INT` → `-TERM` → `-9` 순.
- `pkill -f`는 문자열 매칭이라 무관한 프로세스도 함께 잡힐 수 있음 (예: `my_nav2_test.py`). 실행 전 `pgrep -af <패턴>`으로 대상 확인 필수.
- `ros2 launch` 종료 시 Ctrl+C는 **한 번만** 누르고 기다린다. 두 번 누르면 자식 정리 전에 launch가 죽어 좀비/고아 발생.

---

> 검증: `man ps`, `man pkill`, `man 7 signal` — 일치.
> 검증: Nav2 공식 노드 구성 (https://docs.nav2.org/) — 일치.
> 미검증: TurtleBot4 특정 launch 파일이 띄우는 정확한 프로세스 목록 — 로컬 launch 파일 미확인, 실제 환경에서 `pgrep -af nav2`로 확인 필요.
