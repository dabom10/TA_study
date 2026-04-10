# TA_study notes

ROS2 / TurtleBot4 / 로봇 개발 TA 업무를 하며 마주친 에러 해결 기록, 개념 정리, 명령어 레퍼런스를 모아둔 저장소입니다.
에러는 원인·해결 중심으로, 개념은 섹션 간 연결고리 중심으로 기록합니다.

---

## 디렉토리 구조

```
TA_study/
├── README.md
├── env/              # 환경 세팅 에러 (Ubuntu, ROS2, CUDA 등)
├── hardware/         # 하드웨어 에러 (로봇, 카메라, 센서)
├── software/         # 코드/패키지 에러
├── network/          # 네트워크/통신 에러
└── concepts/         # 개념 정리, 학습 내용, 명령어 레퍼런스, 지식 노트
    └── turtlebot4_manual/   # TurtleBot4 User Manual 스터디
        ├── setup/
        ├── software/
        ├── mechanical/
        ├── electrical/
        ├── tutorials/
        └── troubleshooting/
```

---

## 문제 목록

| 날짜 | 분류 | 내용 | 파일 |
|------|------|------|------|
| 2026-03-30 | env | NVIDIA 드라이버 설치 후 HDMI 외장 모니터 블랙스크린 | [nvidia_hdmi_troubleshooting.md](env/nvidia_hdmi_troubleshooting.md) |
| 2026-03-31 | env | GNOME IBus 한글 전환 안 됨 | [ibus_hangul_super_space.md](env/ibus_hangul_super_space.md) |
| 2026-03-31 | network | configure_discovery.sh 인터넷 차단 환경에서 wget 실패 | [configure_discovery_wget_fail.md](network/configure_discovery_wget_fail.md) |
| 2026-03-31 | network | TurtleBot4 Discovery Server ID 불일치로 토픽 미출력 | [TUI_discovery_N_setup_bash.md](network/TUI_discovery_N_setup_bash.md) |
| 2026-03-31 | concepts | 시스템 설정 및 자주 쓰는 명령어 모음 | [command.md](concepts/command.md) |
| 2026-03-31 | concepts | TurtleBot4 TUI 항목 및 setup.bash 대응 완전 가이드 | [turtlebot4_tui_and_setup_bash_guide.md](concepts/turtlebot4_tui_and_setup_bash_guide.md) |
| 2026-04-01 | concepts | rosdep/apt 개념, apt vs apt-get 차이 | [rosdep_and_apt.md](concepts/rosdep_and_apt.md) |
| 2026-04-01 | concepts | ROS2 패키지 생성, colcon build, source/PATH 개념 | [ros2_workspace_and_package.md](concepts/ros2_workspace_and_package.md) |
| 2026-04-02 | concepts | ROS2 메시지 타입, Interface 개념 및 import/package.xml 정리 | [ros2_message_type_and_interface.md](concepts/ros2_message_type_and_interface.md) |
| 2026-04-02 | concepts | ROS2 통신 개념: Topic/Service/Action, QoS, 리매핑, Bag | [ros2_communication_concepts.md](concepts/ros2_communication_concepts.md) |
| 2026-04-03 | concepts | 두산 M0609 + OnRobot RG2 로봇팔 기초 개념 | [doosan_m0609_rg2_manipulation.md](concepts/doosan_m0609_rg2_manipulation.md) |
| 2026-04-03 | concepts | 시리얼 통신 종류 비교 (UART, SPI, I2C, USB, CAN) | [serial_communication_types.md](concepts/serial_communication_types.md) |
| 2026-04-03 | concepts | TurtleBot4 강의 변경사항, FastDDS/CycloneDDS, Create3 comm LED | [turtlebot4_lecture_5th_updates.md](concepts/turtlebot4_lecture_5th_updates.md) |
| 2026-04-06 | concepts | TurtleBot4 전체 토픽 상세 정리 | [turtlebot4_topic_overview.md](concepts/turtlebot4_topic_overview.md) |
| 2026-04-06 | concepts | SLAM 개념: LiDAR Framework, OGM/Costmap, slam_toolbox 노드-토픽 구조 | [slam_concepts.md](concepts/slam_concepts.md) |
| 2026-04-07 | concepts | Loop Detection vs Loop Closure, Scan Degeneracy, Pose Graph 최적화 | [loop_detection_and_closure.md](concepts/loop_detection_and_closure.md) |
| 2026-04-08 | concepts | TurtleBot4 싱글로봇 네트워크 설정 (Discovery Server, TUI, setup.bash) | [turtlebot4_single_robot_network.md](concepts/turtlebot4_single_robot_network.md) |
| 2026-04-09 | software | SLAM 실행 후 /scan 발행 없음 — turtlebot4_node가 RPLIDAR 자동 정지 | [turtlebot4_rplidar_stopped_no_scan.md](software/turtlebot4_rplidar_stopped_no_scan.md) |
| 2026-04-10 | concepts | apt update vs upgrade 차이 정리 | [apt_update_vs_upgrade.md](concepts/apt_update_vs_upgrade.md) |
| 2026-04-10 | concepts | FastDDS, DDS 표준, RMW 레이어, Discovery Server vs Simple Discovery, 라우팅 개념 | [fastdds_and_discovery_server.md](concepts/fastdds_and_discovery_server.md) |
| 2026-04-10 | concepts | 강의장 멀티로봇 네트워크 구성 비교 (Onboard DS vs Server PC DS) | [classroom_multirobot_network_comparison.md](concepts/classroom_multirobot_network_comparison.md) |
| 2026-04-10 | concepts | 가상환경 개념, Anaconda vs Docker 격리 수준 비교 | [virtual_environment_concepts.md](concepts/virtual_environment_concepts.md) |

---

## TurtleBot4 User Manual 스터디

> 원본: https://turtlebot.github.io/turtlebot4-user-manual/overview/
> 파일 위치: `concepts/turtlebot4_manual/`

| 섹션 | 파일 | 상태 |
|------|------|------|
| Overview | [01_overview.md](concepts/turtlebot4_manual/01_overview.md) | ⬜ |
| Setup - Basic Setup | [setup/01_basic_setup.md](concepts/turtlebot4_manual/setup/01_basic_setup.md) | ⬜ |
| Setup - Networking | [setup/02_networking.md](concepts/turtlebot4_manual/setup/02_networking.md) | ⬜ |
| Setup - Simple Discovery | [setup/03_simple_discovery.md](concepts/turtlebot4_manual/setup/03_simple_discovery.md) | ⬜ |
| Setup - Discovery Server | [setup/04_discovery_server.md](concepts/turtlebot4_manual/setup/04_discovery_server.md) | ⬜ |
| Software - Overview | [software/01_overview.md](concepts/turtlebot4_manual/software/01_overview.md) | ⬜ |
| Software - TurtleBot4 Common | [software/02_tb4_common.md](concepts/turtlebot4_manual/software/02_tb4_common.md) | ⬜ |
| Software - TurtleBot4 Robot | [software/03_tb4_robot.md](concepts/turtlebot4_manual/software/03_tb4_robot.md) | ⬜ |
| Software - TurtleBot4 Simulator | [software/04_tb4_simulator.md](concepts/turtlebot4_manual/software/04_tb4_simulator.md) | ⬜ |
| Software - TurtleBot4 Desktop | [software/05_tb4_desktop.md](concepts/turtlebot4_manual/software/05_tb4_desktop.md) | ⬜ |
| Software - TurtleBot4 Setup | [software/06_tb4_setup.md](concepts/turtlebot4_manual/software/06_tb4_setup.md) | ⬜ |
| Software - Create3 | [software/07_create3.md](concepts/turtlebot4_manual/software/07_create3.md) | ⬜ |
| Software - Sensors | [software/08_sensors.md](concepts/turtlebot4_manual/software/08_sensors.md) | ⬜ |
| Software - Rviz2 | [software/09_rviz2.md](concepts/turtlebot4_manual/software/09_rviz2.md) | ⬜ |
| Software - Simulation | [software/10_simulation.md](concepts/turtlebot4_manual/software/10_simulation.md) | ⬜ |
| Mechanical - TurtleBot4 | [mechanical/01_tb4.md](concepts/turtlebot4_manual/mechanical/01_tb4.md) | ⬜ |
| Mechanical - TurtleBot4 Lite | [mechanical/02_tb4_lite.md](concepts/turtlebot4_manual/mechanical/02_tb4_lite.md) | ⬜ |
| Electrical - Create3 | [electrical/01_create3.md](concepts/turtlebot4_manual/electrical/01_create3.md) | ⬜ |
| Electrical - Raspberry Pi 4B | [electrical/02_rpi4.md](concepts/turtlebot4_manual/electrical/02_rpi4.md) | ⬜ |
| Electrical - User Interface PCBA | [electrical/03_ui_pcba.md](concepts/turtlebot4_manual/electrical/03_ui_pcba.md) | ⬜ |
| Electrical - Power Budget | [electrical/04_power_budget.md](concepts/turtlebot4_manual/electrical/04_power_budget.md) | ⬜ |
| Tutorials - Driving | [tutorials/01_driving.md](concepts/turtlebot4_manual/tutorials/01_driving.md) | ⬜ |
| Tutorials - First Node (C++) | [tutorials/02_first_node_cpp.md](concepts/turtlebot4_manual/tutorials/02_first_node_cpp.md) | ⬜ |
| Tutorials - First Node (Python) | [tutorials/03_first_node_py.md](concepts/turtlebot4_manual/tutorials/03_first_node_py.md) | ⬜ |
| Tutorials - Generating a map | [tutorials/04_mapping.md](concepts/turtlebot4_manual/tutorials/04_mapping.md) | ⬜ |
| Tutorials - Navigation | [tutorials/05_navigation.md](concepts/turtlebot4_manual/tutorials/05_navigation.md) | ⬜ |
| Tutorials - TurtleBot4 Navigator | [tutorials/06_tb4_navigator.md](concepts/turtlebot4_manual/tutorials/06_tb4_navigator.md) | ⬜ |
| Tutorials - Multiple robots | [tutorials/07_multi_robot.md](concepts/turtlebot4_manual/tutorials/07_multi_robot.md) | ⬜ |
| Troubleshooting - Diagnostics | [troubleshooting/01_diagnostics.md](concepts/turtlebot4_manual/troubleshooting/01_diagnostics.md) | ⬜ |
| Troubleshooting - ROS2 Tests | [troubleshooting/02_ros2_tests.md](concepts/turtlebot4_manual/troubleshooting/02_ros2_tests.md) | ⬜ |
| Troubleshooting - FAQ | [troubleshooting/03_faq.md](concepts/turtlebot4_manual/troubleshooting/03_faq.md) | ⬜ |
| Troubleshooting - Factory Reset | [troubleshooting/04_factory_reset.md](concepts/turtlebot4_manual/troubleshooting/04_factory_reset.md) | ⬜ |
