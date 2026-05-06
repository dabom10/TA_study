# WiFi 변경 후 Create3 토픽 미발행

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 24.04 |
| ROS2 | Jazzy |
| 로봇 | TurtleBot4 (Standard) |
| 네트워크 구성 | Discovery Server (Onboard) |

---

## 문제 상황

WiFi 네트워크 변경 및 장소 이동 후 로봇 재시작 시, 다수의 Create3 토픽에 데이터가 들어오지 않음.

```bash
# 토픽은 목록에 뜨지만 echo 해도 출력 없음
ros2 topic echo /robot<N>/battery_state --once   # 무응답
ros2 topic echo /robot<N>/dock_status --once     # 무응답
ros2 topic echo /robot<N>/wheel_status --once    # 무응답
ros2 topic echo /robot<N>/interface_buttons --once  # 무응답
```

PCBA의 BATTERY LED, COMMS LED 꺼짐.

---

## 원인

WiFi 변경 시 RPi4는 새 네트워크에 재연결되지만, Create3는 기존 DDS 연결 상태(domain ID, namespace, discovery server 주소)를 그대로 유지함. RPi4와 Create3의 ROS2 설정이 불일치해 대부분의 Create3 토픽 publisher가 데이터를 발행하지 못하는 상태가 됨.

> 검증: [TurtleBot4 User Manual - turtlebot4-setup](https://turtlebot.github.io/turtlebot4-user-manual/software/turtlebot4_setup.html) — "Reset Create3 = Create3의 domain ID, namespace, discovery server 설정을 현재 RPi4 설정에 맞게 재동기화"

---

## 진단 순서

1. **Create3 연결 확인** — USB-C Ethernet 브리지 생존 여부
   ```bash
   ping 192.168.10.1 -c 3   # 응답 있으면 브리지는 정상
   ```

2. **토픽 데이터 수신 여부 구분**
   ```bash
   turtlebot4-source
   ros2 topic echo /robot<N>/odom --once         # 동작 확인
   ros2 topic echo /robot<N>/battery_state --once  # 미동작 확인
   ```

3. **패턴 판별**

   | 증상 | 원인 |
   |------|------|
   | ping 안 됨 | USB-C 케이블 물리 단선 또는 Create3 미부팅 |
   | ping 되고, odom만 됨, 나머지 안 됨 | Create3 DDS 설정 불일치 → Reset Create3 필요 |
   | 토픽 자체가 목록에 없음 | create3_republisher 미실행 또는 USB-C 브리지 문제 |

4. **Create3 웹서버 접근 시도** (추가 확인)
   ```bash
   curl http://192.168.10.1:8080
   # 응답 없음 = Create3 HTTP 서버 비정상 → 설정 불일치 상태와 동반 발생
   ```

---

## 해결 방법

로봇에 SSH 접속 후 TUI에서 Create3 설정 재동기화:

```bash
ssh ubuntu@<로봇IP>
turtlebot4-setup
```

```
> ROS Setup
  Wi-Fi Setup
  ...
  Reset Create3   ← 선택 후 Yes
```

`Reset Create3` 실행 시:
- Create3의 domain ID, namespace, discovery server 설정을 현재 RPi4 설정에 맞게 덮어씀
- RPi4 설정은 변경되지 않음
- Create3가 재시작되며 Light Ring이 흰색 회전 → 흰색 고정 순서로 복구됨

완료 후 확인:
```bash
turtlebot4-source
ros2 topic echo /robot<N>/battery_state --once
```

---

## 참고

- COMMS LED off는 Discovery Server 구성에서 정상 (Create3가 WiFi 미사용) → [electrical/03_ui_pcba.md](../concepts/turtlebot4_manual/electrical/03_ui_pcba.md)
- BATTERY LED off는 battery_state 토픽 미수신 시 발생 — 이 문서의 증상과 동일
- [GitHub Issue #671 — Turtlebot4 stuck at 0% battery after Wi-Fi setup](https://github.com/turtlebot/turtlebot4/issues/671)
- [TurtleBot4 User Manual - turtlebot4-setup](https://turtlebot.github.io/turtlebot4-user-manual/software/turtlebot4_setup.html)
