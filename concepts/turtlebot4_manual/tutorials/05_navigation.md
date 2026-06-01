# Tutorials - Navigation (Localization + Nav2)

> 검증: `~/turtlebot4` (origin/humble·origin/jazzy) launch/config 직접 비교 — 일치
> 검증: turtlebot4-user-manual navigation 페이지 (WebFetch) — 일치
> 미검증 없음

## 한 줄 요약
실로봇 `localization` / `nav2` 실행 **명령과 launch 파일은 humble·jazzy 완전 동일**하다(둘 다 `nav2_bringup`을 include하는 얇은 래퍼). 버전 간 진짜 차이는 **config(`nav2.yaml`의 Nav2 API)**에 있다.

## 핵심 내용

### 실행 명령 (humble·jazzy 공통)
```bash
ros2 launch turtlebot4_navigation localization.launch.py map:=office.yaml
ros2 launch turtlebot4_navigation nav2.launch.py     # 별도 터미널
```

### launch 구조 (humble↔jazzy byte-identical)
- **localization.launch.py** → `nav2_bringup/localization_launch.py`를 include. 즉 AMCL·map_server 본체는 `nav2_bringup` 소속이고, TB4는 `config/localization.yaml` + `map` 인자만 얹는다. 기본 map = `maps/warehouse.yaml`.
- **nav2.launch.py** → `OpaqueFunction`으로 namespace 처리 후 `nav2_bringup/navigation_launch.py` include. `global_costmap/scan`·`local_costmap/scan`을 `<ns>/scan`으로 `SetRemap`, `use_composition=False`, 기본 `params_file=config/nav2.yaml`.
- 핵심: **launch 파일 자체는 두 브랜치 diff 0 byte.** "패키지가 다르다"는 건 여기가 아니다(아래 09_rviz2 / 시뮬레이터 참고).

### config 차이 (humble → jazzy)
**localization.yaml**
- amcl의 `use_sim_time: True` 제거
- `map_server` 블록 **통째 제거** → map 로딩을 launch의 `map` 인자로 일원화
- map_saver `use_sim_time` 제거, `map_subscribe_transient_local: True`→`true`
- amcl 핵심 튜닝은 유지: `robot_model_type: nav2_amcl::DifferentialMotionModel`, `max_particles: 2000`, `transform_tolerance: 1.0`, `laser_max_range: 100.0`

**nav2.yaml** (약 230줄 변경 — Nav2 humble→jazzy API 전환)
- `bt_navigator`:
  - humble: `use_sim_time: True` + `plugin_lib_names` 대량 명시 + 별도 `bt_navigator_navigate_{to_pose,through_poses}_rclcpp_node` 블록
  - jazzy: `enable_stamped_cmd_vel: true`(cmd_vel을 `TwistStamped`로) + `navigators: [navigate_to_pose, navigate_through_poses]` + 플러그인 네임스페이스(`nav2_bt_navigator::NavigateToPoseNavigator`) + `wait_for_service_timeout`, `action_server_result_timeout: 900.0` 신설, rclcpp_node 블록 제거
- **controller_server (가장 큰 차이)**: humble `FollowPath = dwb_core::DWBLocalPlanner`(DWB, `max_vel_x: 0.26`, DWB critics 7종) → jazzy `nav2_mppi_controller::MPPIController`(MPPI, `vx_max: 0.5`/`vx_min: -0.35`, `model_dt`/`batch_size`/`time_steps` 등 MPPI critics 셋). `progress_checker_plugin`→`progress_checker_plugins`(리스트화).
- **costmap footprint**: 두 costmap 모두 `robot_radius: 0.175` → **8각형 `footprint` 폴리곤**(0.189m 반경)으로 변경.
- **플러그인 표기**: `/` → `::` 일괄 변경(`nav2_navfn_planner::NavfnPlanner`, `nav2_behaviors::Spin` 등). behavior_server는 `costmap_topic`/`footprint_topic` 단일 → `local_*`/`global_*` 분리. 각 서버 `use_sim_time: True` 제거되고 `enable_stamped_cmd_vel: true`로 대체.
- **유지되는 값**: `inflation_radius: 0.45`, `cost_scaling_factor: 4.0`, planner `GridBased=NavfnPlanner`, `resolution: 0.06`, costmap update 주기.

**slam.yaml** (mapping 튜토리얼용, 참고)
- `scan_topic` `scan`→`/scan`, `map_name`·`use_map_saver: true` 추가, `minimum_travel_distance` 0.0→0.1, `scan_buffer_size` 20→10 등 튜닝.

## 다른 섹션과의 연결
- [[nav2_amcl_tf_tree]] — map/odom 프레임, AMCL 동작 원리, TF
- [[nav2_transform_tolerance_source_timeout]] — transform_tolerance/source_timeout 실전 에러
- [[nav2_map_switching]] — `load_map` 서비스 멀티맵
- 09_rviz2 — 초기 pose(2D Pose Estimate)는 rviz에서 지정, 네비 시작 전 필수
- 시뮬 통합 실행의 패키지 rename(`turtlebot4_ignition_bringup`→`turtlebot4_gz_bringup`)은 [[turtlebot4_gz_sim_no_robot]]

## 의문점 / 나중에 파고들 것
- `enable_stamped_cmd_vel`(jazzy)가 cmd_vel 타입을 `TwistStamped`로 바꾸는데 Create3 펌웨어 호환은?
- jazzy `navigators` 플러그인 구조에서 커스텀 BT navigator 추가 방법
- humble에서 `plugin_lib_names`를 비우면 동작 여부 (jazzy는 기본 로드)
