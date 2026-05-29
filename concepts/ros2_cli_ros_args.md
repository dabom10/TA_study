# ROS 2 CLI: `--ros-args` 와 `-r` (remap)

`ros2 run` 등으로 노드를 실행할 때 토픽/노드 이름 등을 코드 수정 없이 바꿔주는 ROS 2 표준 인자 정리.

## 한 줄 요약

`--ros-args`는 "여기서부터 ROS 인자다"라는 경계 표시이고, `-r from:=to`는 이름 리매핑(remap)이다.

## `--ros-args`

> 검증: https://design.ros2.org/articles/ros_command_line_arguments.html — 일치

문서 원문:
> "To prevent ROS specific command line flags from colliding with user-defined ones, the former are scoped using the `--ros-args` flag and a trailing double dash token (`--`)."

노드 실행 파일은 사용자 정의 인자와 ROS 인자를 같이 받을 수 있어 충돌을 막기 위한 스코프 표시. ROS 인자는 반드시 `--ros-args` 뒤에 둔다.

## `-r` / `--remap`

> 검증: https://design.ros2.org/articles/ros_command_line_arguments.html — 일치

문서 원문:
> "Remapping rules may be introduced using the `--remap`/`-r` option. This option takes a single `from:=to` remapping rule."

토픽/서비스/액션/노드 이름을 실행 시점에 바꿔치기한다.

## 예시 — 멀티로봇 네임스페이스로 teleop 보내기

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/robot4/cmd_vel
```

- 노드가 발행하던 `/cmd_vel` → `/robot4/cmd_vel`로 변경
- `robot4` 네임스페이스 로봇만 움직임
- **코드 수정 없이** 토픽 이름만 교체

## 자주 쓰는 ROS 인자

| 옵션 | 의미 | 예시 |
|---|---|---|
| `-r` / `--remap` | 이름 리매핑 | `-r /cmd_vel:=/robot4/cmd_vel` |
| `-p` / `--param` | 파라미터 설정 | `-p use_sim_time:=true` |
| `-r __ns:=...` | 노드 네임스페이스 변경 | `-r __ns:=/robot4` |
| `-r __node:=...` | 노드 이름 변경 | `-r __node:=teleop2` |

### 네임스페이스 vs 토픽 단일 리매핑
- `-r /cmd_vel:=/robot4/cmd_vel` : 한 토픽만 변경
- `-r __ns:=/robot4` : 노드의 모든 상대 토픽이 `/robot4/...` 아래로 들어감 (`cmd_vel`이 자동으로 `/robot4/cmd_vel`)

### 멀티로봇 TF 리매핑 주의
TransformListener가 전역 `/tf`를 구독하면 네임스페이스 안의 TF를 못 받는 경우가 있어 `-r /tf:=tf -r /tf_static:=tf_static` 추가가 필요. 자세한 사례는 [[tf_listener_namespace_mismatch]] (software/) 참조.

## 다른 섹션과의 연결
- [[ros2_communication_concepts]] — 리매핑 개념 일반
- [[turtlebot4_topic_overview]] — 네임스페이스가 적용된 토픽 구조

## 참고 링크
- ROS 2 Command Line Arguments (design doc): https://design.ros2.org/articles/ros_command_line_arguments.html
