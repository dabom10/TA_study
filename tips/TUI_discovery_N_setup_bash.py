# TurtleBot4 Discovery Server 설정 정리

## 개요

TurtleBot4에서 ROS2 통신이 정상 작동하려면 아래 두 곳의 설정이 **반드시 일치**해야 한다.

| 설정 위치 | 경로 / 접근 방법 |
|-----------|-----------------|
| **setup.bash** | `/etc/turtlebot4_discovery/setup.bash` |
| **Discovery Server TUI** | 터미널에서 `turtlebot4-setup` 실행 후 Discovery Server 메뉴 진입 |

---

## 맞춰야 할 항목

| 항목 | TUI 항목명 | setup.bash 변수 | 예시 값 |
|------|-----------|-----------------|---------|
| Discovery Server 활성화 여부 | `Enabled` | — | `True` |
| Onboard Server 포트 | `Onboard Server - Port` | `ROS_DISCOVERY_SERVER` 내 포트 (index 0) | `11811` |
| Onboard Server ID | `Onboard Server - Server ID` | `ROS_DISCOVERY_SERVER` 내 `;` 앞 순서 | `0` |
| **Offboard Server IP** | `Offboard Server - IP` | `ROS_DISCOVERY_SERVER` 내 IP | `192.168.1.2` |
| Offboard Server 포트 | `Offboard Server - Port` | `ROS_DISCOVERY_SERVER` 내 포트 (index 1) | `11811` |
| Offboard Server ID | `Offboard Server - Server ID` | `ROS_DISCOVERY_SERVER` 내 `;` 뒤 순서 | `1` |
| ROS Domain ID | — | `ROS_DOMAIN_ID` | `1` |

---

## setup.bash 예시

```bash
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
[ -t 0 ] && export ROS_SUPER_CLIENT=True || export ROS_SUPER_CLIENT=False
export ROS_DOMAIN_ID=1
export ROS_DISCOVERY_SERVER=";192.168.1.2:11811;"
```

### ROS_DISCOVERY_SERVER 형식 설명

```
";192.168.1.2:11811;"
  │  └──────────────┘
  │       Offboard Server (ID=1) → PC(호스트)의 고정 IP : 포트
  │
  └── 앞의 ";" → Onboard Server(ID=0) 자리 (로봇 자체, 생략 시 기본값 사용)
```

> **포인트:** 세미콜론(`;`) 구분으로 서버 ID 순서가 결정됨
> - `;IP:PORT;` → ID=0 은 비움(Onboard 기본값), ID=1 은 Offboard

---

## TUI 설정 확인 방법

```bash
# TurtleBot4 설정 메뉴 진입
turtlebot4-setup
```

진입 후 **Discovery Server** 메뉴 선택 → 아래 항목 확인

```
Enabled                  [True]
Onboard Server - Port    [11811]
Onboard Server - Server ID [0]
Offboard Server - IP     [192.168.1.2]   ← setup.bash와 반드시 일치
Offboard Server - Port   [11811]
Offboard Server - Server ID [1]
```

---

## 설정 불일치 시 증상

| 증상 | 원인 |
|------|------|
| `ros2 topic list` 에 토픽이 안 보임 | Offboard Server IP 불일치 또는 미입력 |
| ROS2 노드 간 통신 불가 | `ROS_DOMAIN_ID` 불일치 |
| 간헐적 통신 끊김 | PC(호스트) IP가 DHCP로 바뀜 → **고정 IP 필수** |

---

## ⚠️ 주의사항

1. **PC(호스트)의 IP는 반드시 고정 IP로 설정**해야 함 
   DHCP 환경에서는 재부팅 시마다 IP가 바뀌어 Offboard Server IP와 불일치가 발생

2. setup.bash 수정 후에는 반드시 **재부팅 또는 재적용**이 필요.
   ```bash
   sudo reboot
   # 또는
   source /etc/turtlebot4_discovery/setup.bash
   ```

3. TUI에서 저장 후에도 setup.bash가 자동으로 업데이트되는지 확인 필요 
   TUI 저장 → setup.bash 반영 여부는 펌웨어 버전에 따라 다를 수 있음