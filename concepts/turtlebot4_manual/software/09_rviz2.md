# Software - Rviz2 (turtlebot4_viz)

> 검증: GitHub `turtlebot4_desktop` humble·jazzy 트리 + `view_robot.launch.py` 원문 (WebFetch) — 일치
> 검증: turtlebot4-user-manual navigation 페이지 (WebFetch) — view_navigation을 Jazzy로 표기, 일치
> 미검증: humble에서 네비 시각화에 view_robot를 쓴다는 점 — repo 트리상 view_navigation이 jazzy 전용임은 확인했으나, humble 매뉴얼의 정확한 rviz 실행 명령은 미확인(추론)

## 한 줄 요약
rviz2 시각화는 **`turtlebot4_desktop` repo의 `turtlebot4_viz`** 패키지가 담당한다(=`@turtlebot4/` 체크아웃엔 없음). **humble엔 `view_navigation.launch.py`가 없고 jazzy에서 추가**됐다 — loc/nav2가 아니라 **여기가 humble↔jazzy launch 패키지 차이의 실체**.

## 핵심 내용

### 패키지 위치
- `turtlebot4_viz` ⊂ repo `turtlebot4_desktop` (navigation과 별개 repo)

### launch / rviz config 목록 (humble↔jazzy 차이)
| 항목 | humble | jazzy |
|------|--------|-------|
| launch | view_robot, view_model, view_diagnostics | + **view_navigation** |
| rviz config | robot.rviz, model.rviz | + **navigation.rviz** |

- **humble**: 네비 시각화도 `view_robot.launch.py`(robot.rviz)로 처리(전용 네비 launch 없음)
- **jazzy**: `view_navigation.launch.py`(navigation.rviz, nav2 디스플레이 프리셋) 추가

### view_robot.launch.py 구조 (humble)
- `rviz2` 노드 1개 + `robot.rviz` 로드
- `description:=true`일 때 `turtlebot4_description/robot_description.launch.py`를 **3초 지연** include (rviz 초기화 후 모델 로드 → 렌더 이슈 방지)
- args: `use_sim_time`(false), `description`(false), `model`(standard/lite), `namespace`

### 실행 명령
```bash
ros2 launch turtlebot4_viz view_robot.launch.py        # humble·jazzy 공통
ros2 launch turtlebot4_viz view_navigation.launch.py   # jazzy 전용
```
- 네비 전 **2D Pose Estimate**로 AMCL 초기 pose 지정 필수.

## 다른 섹션과의 연결
- 05_navigation — 초기 pose / nav goal 입력 도구가 rviz2
- [[nav2_amcl_tf_tree]] — TF 트리·프레임 시각화

## 의문점 / 나중에 파고들 것
- `navigation.rviz` vs `robot.rviz` 디스플레이 구성 구체 차이
- humble에서 robot.rviz만으로 nav 시각화가 충분한지, 수동 추가 디스플레이는?
