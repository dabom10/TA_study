# TransformListener 네임스페이스 불일치로 map 프레임 미수신

## 환경
- OS: Ubuntu 24.04
- ROS2: Jazzy
- 패키지: tf2_ros, nav2_amcl

## 문제 상황
멀티로봇 환경에서 네임스페이스를 붙여 노드 실행 시 TF transform 실패.

```
[WARN] [robot8.depth_to_map_node]: TF transform failed: "map" passed to lookupTransform argument target_frame does not exist.
```

AMCL은 active 상태이고 `/amcl_pose`에 데이터도 있는데, `tf_buffer` 안에 `map` 프레임이 없는 상황.

## 원인
AMCL 실행 시 TF 토픽 remapping이 적용된다:
```
-r /tf:=tf -r /tf_static:=tf_static
```
`/robot8` 네임스페이스에서 `tf` (상대경로) = `/robot8/tf`로 publish.

그런데 `tf2_ros.TransformListener`는 내부적으로 **절대경로** `/tf`를 구독한다:
```python
# tf2_ros/transform_listener.py
node.create_subscription(TFMessage, '/tf', ...)  # 절대경로
```

결과:
```
AMCL         → /robot8/tf 에 publish
TransformListener → /tf (전역) 구독
                → 데이터 못 받음 → tf_buffer 비어있음 → map 프레임 없음
```

## 진단 순서
1. `ros2 topic list | grep tf` — `/robot8/tf`와 `/tf` 둘 다 있는지 확인
2. `ros2 topic echo /robot8/tf | grep "frame_id: map"` — AMCL이 map→odom을 publish하는지 확인 (로봇 움직이면서 확인)
3. `ps aux | grep amcl` — 실제 실행 인자에서 `-r /tf:=tf` remapping 확인
4. `cat /tmp/launch_params_<hash> | grep tf_broadcast` — 실제 파라미터 파일 확인

## 해결 방법
노드 실행 시 동일한 remapping 추가:

```bash
python3 node.py --ros-args -r __ns:=/robot8 -r /tf:=tf -r /tf_static:=tf_static
```

TransformListener가 `/tf` 대신 `tf` (상대경로) = `/robot8/tf`를 구독하게 된다.

## 참고
- [nav2_amcl_tf_tree.md](../concepts/nav2_amcl_tf_tree.md)
- tf2_ros TransformListener 소스: `/opt/ros/jazzy/lib/python3.12/site-packages/tf2_ros/transform_listener.py`
