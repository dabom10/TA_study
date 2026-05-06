# teleop_twist_keyboard Jazzy에서 로봇 미반응

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 24.04 |
| ROS2 | Jazzy |
| 로봇 | TurtleBot4 |
| 패키지 | teleop_twist_keyboard |

---

## 문제 상황

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/robot<N>/cmd_vel
```

실행 후 `i`, `j`, `l` 키를 눌러도 화면에 아무 변화 없고 로봇이 움직이지 않음.

---

## 원인

두 가지가 복합적으로 작용:

### 1. Jazzy에서 cmd_vel 타입 변경

Humble까지는 `geometry_msgs/msg/Twist`, Jazzy부터 `geometry_msgs/msg/TwistStamped`로 전환.

> 검증: [GitHub Issue #504 - Nav2 Migrated to TwistStamped](https://github.com/turtlebot/turtlebot4/issues/504)

기본 teleop_twist_keyboard는 `Twist`를 발행 → subscriber(로봇)가 무시함.

`ros2 topic info /robot<N>/cmd_vel`로 확인 시:
```
Type: ['geometry_msgs/msg/Twist', 'geometry_msgs/msg/TwistStamped']
Publisher count: 2   # teleop_twist_keyboard(Twist) + teleop_twist_joy(TwistStamped)
Subscription count: 1
```

### 2. 이동 키는 화면 출력이 없는 것이 정상

teleop_twist_keyboard 코드 구조상 화면에 출력되는 건 속도 조절 키(q/z/w/x/e/c)뿐.  
이동 키(i/j/l/k 등)는 publish만 하고 출력 없음 → 동작 중이어도 "안 먹히는 것처럼" 보임.

```
# 실제 코드 (teleop_twist_keyboard.py)
elif key in speedBindings.keys():
    print(vels(speed, turn))  # 속도 키만 출력
# moveBindings에는 print 없음
```

키 입력 정상 여부 확인 방법: `q` 키로 속도값 변화 여부 확인.

---

## 진단 순서

1. `q` 키 입력 시 `currently: speed X.XX` 값이 바뀌는지 확인
   - 바뀜 → 키 입력 정상, 타입 문제
   - 안 바뀜 → TTY/터미널 문제 (stdin이 raw mode 진입 실패)

2. 타입 확인
   ```bash
   ros2 topic info /robot<N>/cmd_vel
   # Type에 TwistStamped만 있으면 stamped:=true 필요
   ```

---

## 해결 방법

`stamped:=true` 파라미터 추가:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -p stamped:=true -r /cmd_vel:=/robot<N>/cmd_vel
```

이동 키를 눌러도 화면 변화는 없음 — 로봇이 실제로 움직이는지로 동작 확인.

---

## 참고

- Humble → Jazzy 마이그레이션 시 teleop 관련 공통 사항
- `cmd_vel_unstamped` 토픽이 별도로 존재하는 이유도 동일: Twist 하위호환용
- [teleop_twist_keyboard Jazzy 문서](https://docs.ros.org/en/jazzy/p/teleop_twist_keyboard/)
