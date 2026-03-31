# TurtleBot4 Discovery Server 설정 — TUI와 setup.bash 불일치 문제

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| ROS2 | Humble |
| 로봇 | TurtleBot4 |
| TurtleBot4 IP | 192.168.1.2 |
| User PC IP | 192.168.1.3 |

---

## 문제 상황

User PC에서 `ros2 topic list`를 실행하면 토픽이 뜨지 않음.

```
rokey@rokey:~$ ros2 topic list
/parameter_events
/rosout
```

터틀봇에 SSH 접속해서 실행하면 토픽이 정상으로 뜸. 처음엔 이걸 PC에서 된다고 오해함.

---

## 원인

`ROS_DISCOVERY_SERVER` 환경변수의 서버 ID가 터틀봇에서 실행 중인 Discovery Server ID와 불일치.

터틀봇은 **ID 0**으로 서버를 실행 중:
```
fastdds discovery -i 0 -p 11811
```

그런데 User PC의 `/etc/turtlebot4_discovery/setup.bash`는:
```bash
export ROS_DISCOVERY_SERVER=";192.168.1.2:11811;"
```

`ROS_DISCOVERY_SERVER`는 세미콜론(`;`) 위치로 서버 ID를 결정함:

```
;  192.168.1.2:11811  ;
↑                     
ID 0: 비어있음    ID 1: 192.168.1.2:11811
```

즉 PC는 **ID 1** 위치의 서버에 연결하려 하지만, 터틀봇은 **ID 0** 서버만 실행 중이므로 연결 실패.

---

## 진단 순서

1. 환경변수 확인
   ```bash
   echo $ROS_DISCOVERY_SERVER
   echo $ROS_DOMAIN_ID
   echo $ROS_SUPER_CLIENT
   ```

2. Discovery Server 포트 연결 확인
   ```bash
   nc -zv 192.168.1.2 11811
   # → Connection refused 이면 서버 미실행 또는 Server ID 불일치
   ```

3. 터틀봇에서 Discovery Server 실행 확인
   ```bash
   ssh ubuntu@192.168.1.2 "ps aux | grep fastdds"
   # fastdds discovery -i 0 -p 11811  ← -i 값이 서버 ID
   ```

4. 터틀봇 방화벽 확인
   ```bash
   ssh ubuntu@192.168.1.2 "sudo ufw status"
   ```

---

## 해결 방법

`/etc/turtlebot4_discovery/setup.bash`에서 `ROS_DISCOVERY_SERVER`의 앞뒤 세미콜론 제거:

```bash
# 수정 전 (틀림 — 서버를 ID 1 위치에서 찾음)
export ROS_DISCOVERY_SERVER=";192.168.1.2:11811;"

# 수정 후 (맞음 — 서버를 ID 0 위치에서 찾음)
export ROS_DISCOVERY_SERVER="192.168.1.2:11811"
```

수정 후 재소싱:
```bash
source /etc/turtlebot4_discovery/setup.bash
ros2 topic list
```

---

## ROS_DISCOVERY_SERVER 형식 설명

세미콜론으로 위치를 나누며, 위치 순서가 서버 ID:

| 값 | ID 0 | ID 1 |
|----|------|------|
| `192.168.1.2:11811` | 192.168.1.2:11811 | 없음 |
| `;192.168.1.2:11811` | 없음 | 192.168.1.2:11811 |
| `;192.168.1.2:11811;` | 없음 | 192.168.1.2:11811 |
| `192.168.1.2:11811;10.0.0.1:11811` | 192.168.1.2:11811 | 10.0.0.1:11811 |

터틀봇의 Discovery Server는 기본적으로 `-i 0`으로 실행되므로 `ROS_DISCOVERY_SERVER`에 세미콜론 없이 `IP:PORT`만 적어야 함.

---

## 참고

- `ROS_SUPER_CLIENT=True` 설정이 있어야 Discovery Server에 등록된 모든 토픽을 볼 수 있음
- `/etc/turtlebot4_discovery/setup.bash`는 `~/.bashrc`에 source되어야 터미널마다 자동 적용됨
