# TurtleBot4 LED 상태 가이드

## 한 줄 요약
Create3 Light Ring은 로봇 전반 상태(부팅/배터리/WiFi/에러)를, PCBA 상태 LED는 각 서브시스템(전원/통신/WiFi/배터리) 상태를 표시한다.

---

## Create3 Light Ring (바닥 링 LED)

> 검증: [iRobot Create3 공식 문서](https://iroboteducation.github.io/create3_docs/hw/face/) — 일치

| 상황 | 패턴 | 의미 |
|------|------|------|
| **부팅** | 흰색 회전 (Spinning White) | 부팅 중 — happy sound 들릴 때까지 대기 |
| **정상 대기** | 흰색 고정 (Solid White) | 전원 켜짐, 정상 동작 중 |
| **충전 중** | 흰색 부분 표시 (Partial White) | 충전 중 (충전량만큼 링이 채워짐) |
| **완충** | 흰색 전체 고정 | 100% 충전 완료 |
| **배터리 부족** | 빨간색 맥동 (Pulsing Red) | 배터리 < 10% |
| **배터리 위험** | 빨간색 회전 (Spinning Red) | 배터리 < 3% — 즉시 충전 필요 |
| **로봇 에러** | 빨간색 고정 (Solid Red) | 에러 발생 — 전원 재시작 필요 |
| **AP 모드 활성** | 시안 회전 (Spinning Cyan) | Access Point 활성화됨 |
| **AP 접속됨** | 시안 고정 (Solid Cyan) | 디바이스가 AP에 연결된 상태 |
| **WiFi 연결 성공** | 초록 빠른 깜빡임 | WiFi 연결 성공 |
| **WiFi 실패 - 비밀번호** | 노랑 + 빨강 | 비밀번호 틀림 |
| **WiFi 실패 - 네트워크** | 노랑 + 초록 | 네트워크 도달 불가 |
| **WiFi 실패 - DHCP** | 노랑 + 파랑 | DHCP 타임아웃 |
| **WiFi 실패 - 기타** | 노랑 고정 (Solid Yellow) | 알 수 없는 WiFi 실패 |
| **펌웨어 업데이트** | 시안 고정 → 파랑 회전 → 흰색 회전 → 흰색 고정 | 업데이트 진행 순서 |
| **후진 안전장치 작동** | 반쪽 주황 (Half Orange) | 후방 감지 — 백업 안전 기능 활성 |
| **휠 비활성화** | 반쪽 노랑 (Half Yellow) | 바퀴 잠긴 상태 |

---

## TurtleBot4 표준형 PCBA 상태 LED

> 검증: [TurtleBot4 User Manual - Features](https://turtlebot.github.io/turtlebot4-user-manual/overview/features.html), [turtlebot4_common 소프트웨어 문서](https://turtlebot.github.io/turtlebot4-user-manual/software/turtlebot4_common.html) — 일치

**TurtleBot4 Lite에는 없음** — Light Ring만 있음

| LED | 켜짐 조건 | 의미 |
|-----|----------|------|
| **POWER** | 항상 (초록) | 전원 ON |
| **MOTOR** | 초록 | 바퀴 활성화 상태 |
| **COMMS** | 초록 | Create3 ↔ RPi 통신 정상 |
| **WIFI** | 초록 | IP 주소 취득 완료 |
| **BATTERY** | 초록 | 50~100% |
|  | 노랑 | 20~50% |
|  | 빨강 | 12~20% |
|  | 빨강 깜빡임 | 0~12% |

### COMMS LED 꺼짐이 정상인 경우

Discovery Server 구성에서는 Create3가 WiFi에 직접 연결하지 않으므로 COMMS LED가 꺼져 있어도 정상이다.

```
[Create3] ---USB-C--- [RPi (Discovery Server)] ---WiFi--- [PC]
```

- Simple Discovery: COMMS LED on이어야 정상
- Discovery Server: COMMS LED off가 정상

→ 자세한 내용: [turtlebot4_lecture_5th_updates.md](../../turtlebot4_lecture_5th_updates.md)

---

## 사용자 LED (USER_1, USER_2)

ROS2 토픽으로 직접 제어 가능:

```bash
# /hmi/led 토픽에 UserLed 메시지 발행
ros2 topic pub /hmi/led turtlebot4_msgs/msg/UserLed ...
```

| LED | 지원 색상 |
|-----|----------|
| USER_1 | 초록 |
| USER_2 | 초록, 노랑, 빨강 |

---

## 부팅~정상 동작 시퀀스

```
전원 ON
  → [흰색 회전] 부팅 중
  → happy sound 재생
  → [흰색 고정] 정상 대기
```

---

## 다른 섹션과의 연결

- Create3 ↔ RPi 통신 구조 → [turtlebot4_lecture_5th_updates.md](../../turtlebot4_lecture_5th_updates.md)
- PCBA 하드웨어 핀아웃 → [electrical/03_ui_pcba.md](electrical/03_ui_pcba.md)
- WiFi/네트워크 설정 → [turtlebot4_single_robot_network.md](../../turtlebot4_single_robot_network.md)
