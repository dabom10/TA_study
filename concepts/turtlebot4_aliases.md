# TurtleBot4 별칭(alias) 명령어 정리

`turtlebot4-source`, `turtlebot4-service-restart`, `turtlebot4-daemon-restart` 등은
별도 프로그램이 아니라 `/etc/turtlebot4/aliases.bash`에 정의된 **bash alias**다.
TurtleBot4 설치 시 `~/.bashrc`에서 이 파일을 자동으로 source 하도록 등록된다.

> 검증: `etc/turtlebot4/aliases.bash` (turtlebot/turtlebot4_setup, humble 브랜치) — 원문 확인, 일치
> 검증: `scripts/turtlebot4_setup.sh` 53~55행 — `ROBOT_SETUP` 정의 및 aliases.bash source 등록 확인, 일치

---

## aliases.bash 전체 별칭 (원문)

```bash
# Restart ROS2 daemon
alias turtlebot4-daemon-restart='ros2 daemon stop; ros2 daemon start'

# Help command
alias turtlebot4-help='echo -e "..."'   # 매뉴얼/GitHub 링크 출력

# Restart ntpd on Create 3
alias turtlebot4-ntpd-sync='curl -X POST http://<create3IP>/api/restart-ntpd'

# Restart turtlebot4 service
alias turtlebot4-service-restart='sudo systemctl restart turtlebot4.service'

# Run turtlebot4_setup
alias turtlebot4-setup='ros2 run turtlebot4_setup turtlebot4_setup'

# Source ROBOT_SETUP
alias turtlebot4-source='source $ROBOT_SETUP'

# Update all packages
alias turtlebot4-update='sudo apt update && sudo apt upgrade'
```

`~/.bashrc`에는 설치 시 다음이 추가된다:

```bash
export ROBOT_SETUP=/etc/turtlebot4/setup.bash
source $ROBOT_SETUP
source /etc/turtlebot4/aliases.bash
```

---

## 핵심 3종 상세

### turtlebot4-source → `source $ROBOT_SETUP`

- `$ROBOT_SETUP`은 로봇에서는 `/etc/turtlebot4/setup.bash`를 가리킨다.
  User PC에서 Discovery Server를 설정한 경우 `/etc/turtlebot4_discovery/setup.bash`.
- `turtlebot4-setup` TUI로 `ROS_DOMAIN_ID`, `ROS_DISCOVERY_SERVER`, `RMW_IMPLEMENTATION` 등을
  변경한 뒤, **새 터미널을 열지 않고** 현재 터미널에 바로 반영할 때 사용.
- → [turtlebot4_tui_and_setup_bash_guide.md](turtlebot4_tui_and_setup_bash_guide.md)

### turtlebot4-service-restart → `sudo systemctl restart turtlebot4.service`

- `turtlebot4.service`는 부팅 시 ROS2 노드들을 자동 실행하는 systemd 서비스
  (robot_upstart로 등록됨).
- **로봇 위(RPi)에서** 실행해야 의미가 있다. 설정 변경 후 또는 노드가 멈췄을 때 노드 전체 재시작.
- `sudo` 필요.

### turtlebot4-daemon-restart → `ros2 daemon stop; ros2 daemon start`

- ROS2 CLI 데몬은 노드/토픽 목록을 캐싱한다. `ros2 topic list`에 토픽이 안 뜨거나
  목록이 오래된(stale) 경우 캐시를 비우기 위해 사용.
- 로봇이 아니라 **명령을 실행하는 PC(User PC)에서** 주로 사용.
- Discovery Server 설정 변경 후 토픽이 안 보일 때 진단 단계로 자주 등장.
- → [ros2_image_raw_message_lost_wifi.md](../network/ros2_image_raw_message_lost_wifi.md),
  [wifi_change_create3_reset.md](../network/wifi_change_create3_reset.md)

---

## 나머지 별칭

| 별칭 | 실제 명령 | 용도 |
|------|-----------|------|
| `turtlebot4-setup` | `ros2 run turtlebot4_setup turtlebot4_setup` | 설정 TUI 실행 |
| `turtlebot4-update` | `sudo apt update && sudo apt upgrade` | 패키지 전체 업데이트 |
| `turtlebot4-help` | 매뉴얼/GitHub 링크 출력 | 도움말 |
| `turtlebot4-ntpd-sync` | `curl -X POST http://<create3IP>/api/restart-ntpd` | Create3 보드 ntpd 재시작 |

---

## 출처

- [turtlebot4_setup/etc/turtlebot4/aliases.bash (humble)](https://github.com/turtlebot/turtlebot4_setup/blob/humble/etc/turtlebot4/aliases.bash)
- [TurtleBot4 User Manual — Setup](https://turtlebot.github.io/turtlebot4-user-manual/software/turtlebot4_setup.html)
