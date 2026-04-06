# TurtleBot4 토픽 전체 정리

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| ROS2 | Humble |
| 로봇 | TurtleBot4 (iRobot Create3 + Raspberry Pi 4 + OAK-D) |

---

## 1. 시스템 / 진단

### `/diagnostics`, `/robot8/diagnostics`
ROS2 표준 진단 시스템. 각 노드가 자신의 상태를 publish.
- 타입: `diagnostic_msgs/msg/DiagnosticArray`
```
예: "Motor OK", "Battery LOW: 15%", "IMU ERROR: timeout"
```

### `/robot8/diagnostics_agg`
여러 진단 메시지를 트리 구조로 집계한 것.  
개별 진단들을 카테고리별로 묶어줌 (센서/모터/배터리 등).

### `/robot8/diagnostics_toplevel_state`
집계 결과의 최종 요약 한 줄.
```
0 = OK
1 = WARN
2 = ERROR
3 = STALE (데이터 끊김)
```

### `/parameter_events`
노드 파라미터가 변경될 때마다 발행. 주로 디버깅/모니터링용.

### `/rosout`
모든 노드의 로그 출력이 모이는 곳.
```bash
ros2 topic echo /rosout   # 전체 로그 확인
```

### `/robot8/ip`
로봇 IP 주소 문자열. 네트워크 연결 확인용.

---

## 2. 전원 / 하드웨어

### `/robot8/battery_state`
타입: `sensor_msgs/msg/BatteryState`
```
voltage: 14.2
percentage: 0.78     # 78%
power_supply_status: DISCHARGING / CHARGING / FULL
```

### `/robot8/dock_status`
타입: `irobot_create_msgs/msg/DockStatus`
```
is_docked: true/false
dock_visible: true/false   # 도킹 IR 신호 감지 여부
```
undock 명령 후 `is_docked: false` 되면 성공.

### `/robot8/wheel_status`
타입: `irobot_create_msgs/msg/WheelStatus`
```
current_ma_left: 300    # 왼쪽 모터 전류 (mA)
current_ma_right: 310
pwm_left: 128
pwm_right: 130
```
과전류 감지, 모터 고장 진단에 사용.

### `/robot8/joint_states`
타입: `sensor_msgs/msg/JointState`
```
name: ['left_wheel', 'right_wheel']
position: [3.14, 6.28]   # 누적 회전각 (rad)
velocity: [0.5, 0.5]     # 현재 각속도 (rad/s)
```
odom 계산의 원본 데이터.

---

## 3. 제어 (입력)

### `/robot8/cmd_vel`
타입: `geometry_msgs/msg/Twist`
```
linear:
  x: 0.3    # 전진속도 (m/s), 음수면 후진
  y: 0.0    # 차동구동은 항상 0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.5    # 회전속도 (rad/s), 양수=좌회전
```
teleop이 여기 publish → 로봇이 subscribe해서 바퀴 제어.

### `/robot8/cmd_audio`
타입: `irobot_create_msgs/msg/AudioNoteVector`
```
notes: [{frequency: 440, max_runtime_ms: 500}]   # 라 음 0.5초
```

### `/robot8/cmd_lightring`
타입: `irobot_create_msgs/msg/LightringLeds`  
LED 6개 각각 RGB 값 설정.
```
leds: [{red: 255, green: 0, blue: 0}, ...]
```

---

## 4. 센서

### `/robot8/scan`
타입: `sensor_msgs/msg/LaserScan`  
SLAM의 핵심 입력.
```
angle_min: -3.14      # 시작 각도
angle_max: 3.14       # 끝 각도
angle_increment: 0.01 # 각도 해상도
ranges: [0.5, 0.7, inf, 1.2, ...]   # 거리 배열 (m)
```
inf = 장애물 없음, 값 = 해당 방향 장애물까지 거리.

### `/robot8/imu`
타입: `sensor_msgs/msg/Imu`
```
orientation: {x,y,z,w}           # 쿼터니언 (현재 자세)
angular_velocity: {x,y,z}        # 각속도 (rad/s)
linear_acceleration: {x,y,z}     # 선가속도 (m/s²)
```
급격한 충돌, 기울기 감지. odom 보정에도 활용.

### `/robot8/odom`
타입: `nav_msgs/msg/Odometry`
```
pose:
  position: {x: 1.2, y: 0.5, z: 0.0}
  orientation: {x,y,z,w}
twist:
  linear: {x: 0.3, ...}
  angular: {z: 0.1, ...}
```
바퀴 회전 누적으로 계산 → 시간이 지날수록 오차 누적 (drift).  
SLAM이 scan으로 보정하는 이유.

### `/robot8/mouse`
바닥 광학 마우스 센서. 미끄러운 바닥에서 바퀴 slip 감지/보정용.

### `/robot8/hazard_detection`
타입: `irobot_create_msgs/msg/HazardDetectionVector`
```
detections:
  - type: BUMP        # 충돌
  - type: CLIFF       # 낭떠러지
  - type: STALL       # 바퀴 멈춤
```
감지되면 로봇이 자동으로 멈춤.

---

## 5. 카메라 (OAK-D)

### OAK-D 구조
```
OAK-D 카메라
 ├── RGB 카메라 (1개)
 ├── 스테레오 카메라 (2개, 깊이 계산용)
 └── IMU (내장)
```

### `/robot8/oakd/rgb/image_raw`
타입: `sensor_msgs/msg/Image`  
RGB 원본 이미지. 해상도 높음 → 용량 큼.

### `/robot8/oakd/rgb/preview/image_raw`
저해상도 버전 (보통 300×300). 객체 인식 등 실시간 처리용.

### `/robot8/oakd/stereo/image_raw`
좌우 카메라 시차로 계산한 깊이 이미지.  
각 픽셀값 = 해당 지점까지 거리.

### `/robot8/oakd/rgb/camera_info`
타입: `sensor_msgs/msg/CameraInfo`
```
width: 1920, height: 1080
K: [fx, 0, cx, 0, fy, cy, 0, 0, 1]   # 내부 파라미터 행렬
D: [k1, k2, p1, p2]                   # 왜곡 계수
```
이미지 좌표 → 실제 3D 좌표 변환에 필요.

### `compressed / compressedDepth / theora`
- `compressed` : JPEG/PNG 압축 (일반 이미지)
- `compressedDepth` : 깊이 이미지 전용 압축
- `theora` : 동영상 스트림 압축

네트워크 대역폭 절약용. 원격 모니터링할 때 raw 대신 이걸 구독.

### `/robot8/oakd/imu/data`
카메라 내장 IMU. `/robot8/imu`(로봇 본체)와 별개.  
카메라 흔들림 보정에 사용.

---

## 6. HMI / 조이스틱

### `/robot8/hmi/buttons`
Create3 본체 위 3개 버튼 입력.
```
button_1: false
button_2: true
button_power: false
```

### `/robot8/hmi/display`, `/robot8/hmi/display/message`
7세그먼트 디스플레이에 숫자/문자 출력.

### `/robot8/hmi/led`
버튼 주변 LED 상태.

### `/robot8/joy`
타입: `sensor_msgs/msg/Joy`
```
axes: [0.0, 0.8, -1.0, ...]    # 스틱, 트리거
buttons: [0, 1, 0, 0, ...]     # 버튼 눌림 여부
```

### `/robot8/joy/set_feedback`
조이스틱 진동(rumble) 명령.

---

## 7. 좌표계

### `/robot8/tf`
타입: `tf2_msgs/msg/TFMessage`  
동적 좌표계 변환. 매 프레임 업데이트.
```
예: odom → base_link  (로봇 이동에 따라 계속 변함)
```

### `/robot8/tf_static`
고정 좌표계 변환. 한 번만 발행.
```
예: base_link → laser    (LiDAR 위치는 안 변함)
    base_link → camera   (카메라 위치는 안 변함)
```

### `/robot8/robot_description`
URDF XML 문자열. 로봇 링크/관절 구조 정의.  
RViz가 로봇 3D 모델 그릴 때 사용.

---

## 8. SLAM (slam_toolbox 실행 후 추가)

### `/robot8/map`
타입: `nav_msgs/msg/OccupancyGrid`
```
info:
  resolution: 0.05      # 1셀 = 5cm
  width: 384
  height: 384
  origin: {x: -10.0, y: -10.0}
data: [0, 0, 100, -1, ...]
# 0=빈공간, 100=장애물, -1=미탐색
```

### `/robot8/map_metadata`
map의 info 부분만 따로 발행. 맵 크기/해상도 빠르게 확인용.

### `/robot8/pose`
타입: `geometry_msgs/msg/PoseWithCovarianceStamped`  
odom과 달리 SLAM이 보정한 위치 → 더 정확.
```
pose:
  position: {x: 1.2, y: 0.5}
  orientation: {w: 0.99, z: 0.1}
covariance: [...]   # 위치 불확실도
```

### `/robot8/slam_toolbox/feedback`
SLAM 내부 처리 상태 (루프 클로저 발생 등).

### `/robot8/slam_toolbox/graph_visualization`
pose graph — 로봇이 지나온 경로와 노드 연결 구조. RViz 시각화용.

### `/robot8/slam_toolbox/scan_visualization`
현재 scan이 맵에 어떻게 매칭되는지 시각화.

### `/robot8/slam_toolbox/update`
맵 강제 업데이트 트리거.

---

## 기타

### `/robot8/function_calls`
Create3 펌웨어 함수 호출 인터페이스.

### `/robot8/interface_buttons`
로봇 인터페이스 버튼 (HMI buttons와 별개).
