# configure_discovery.sh 실행 시 아무 동작 없이 종료되는 문제

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu |
| ROS2 | Humble |
| 로봇 | TurtleBot4 |
| 네트워크 | 터틀봇 전용 네트워크 (인터넷 미연결) |

---

## 문제 상황

TurtleBot4 디스커버리 서버 설정을 위해 아래 명령을 실행했으나 아무 출력 없이 즉시 종료됨.

```bash
wget -qO /tmp/configure_discovery.sh https://raw.githubusercontent.com/turtlebot/turtlebot4_setup/humble/turtlebot4_discovery/configure_discovery.sh
sudo bash /tmp/configure_discovery.sh
```

`sudo`로 실행해도 동일하게 종료됨. `bash -x`로 디버깅해도 출력 없음.

---

## 원인

현재 연결된 네트워크(터틀봇 전용망)가 **인터넷이 차단된 상태**여서 `wget`이 파일을 받지 못하고 **0바이트 빈 파일**을 생성함.

```bash
ls -la /tmp/configure_discovery.sh
# -rw-rw-r-- 1 rokey rokey 0 ...  ← 0바이트
```

빈 파일을 실행하니 아무 동작 없이 종료된 것.

---

## 진단 순서

### 1. 파일 크기 확인

```bash
ls -la /tmp/configure_discovery.sh
```

0바이트이면 다운로드 실패.

### 2. wget 상세 로그 확인

```bash
wget -v https://raw.githubusercontent.com/turtlebot/turtlebot4_setup/humble/turtlebot4_discovery/configure_discovery.sh -O /tmp/configure_discovery.sh
```

---

## 해결 방법

인터넷이 연결된 다른 네트워크로 전환하여 스크립트를 다운로드한 후, 터틀봇 네트워크로 다시 전환하여 실행.

```bash
# 1. 인터넷 연결된 네트워크에서 다운로드
wget -qO /tmp/configure_discovery.sh https://raw.githubusercontent.com/turtlebot/turtlebot4_setup/humble/turtlebot4_discovery/configure_discovery.sh

# 2. 터틀봇 네트워크로 전환 후 실행
sudo bash /tmp/configure_discovery.sh
```

스크립트 실행 자체는 인터넷 불필요. 단, 입력할 디스커버리 서버 IP는 터틀봇 네트워크 기준으로 입력해야 함.

---

## 참고

- `wget -q` 옵션은 에러도 출력하지 않으므로, 다운로드 실패 여부를 알기 어려움
- 스크립트 실행 전 파일 크기 확인하는 습관을 들일 것
