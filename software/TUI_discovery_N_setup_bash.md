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

## Discovery Server 구조

| 쪽 | 역할 | 내용 |
|------|------|------|
| **터틀봇** | 서버 실행 | `fastdds discovery -i 0 -p 11811` 자동 실행 |
| **PC** | 클라이언트 | `ROS_DISCOVERY_SERVER` 환경변수로 접속 대상 지정 |

터틀봇 TUI(`turtlebot4-setup`)에서 Discovery Server 항목을 **true**로 설정하면,
설정이 `/etc/turtlebot4/` 아래 파일에 저장되고 부팅/적용 시 아래 명령이 자동 실행됨:

```
fastdds discovery -i 0 -p 11811
```

- `-i 0` : 서버 ID = 0
- `-p 11811` : 대기 포트

`ROS_DISCOVERY_SERVER`는 **PC(클라이언트) 쪽에 설정**하는 변수로, 서버를 여는 게 아니라 "어디로 접속할지"를 지정하는 것.

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

Discovery Server는 여러 대를 동시에 운영할 수 있어서, `ROS_DISCOVERY_SERVER`는 **배열** 형태로 서버 목록을 관리함. **세미콜론이 구분자**이며, 위치(인덱스)가 서버 ID:

```
ROS_DISCOVERY_SERVER="서버0주소;서버1주소;서버2주소"
                           ↑         ↑         ↑
                         ID 0      ID 1      ID 2
```

비어있으면 "그 ID 위치엔 서버 없음"으로 해석:

```
";192.168.1.2:11811"
  ↑  ↑
  │  ID 1 = 192.168.1.2:11811
  │
  ID 0 = 비어있음
```

| 값 | ID 0 | ID 1 |
|----|------|------|
| `192.168.1.2:11811` | 192.168.1.2:11811 | 없음 |
| `;192.168.1.2:11811` | 없음 | 192.168.1.2:11811 |
| `;192.168.1.2:11811;` | 없음 | 192.168.1.2:11811 |
| `192.168.1.2:11811;10.0.0.1:11811` | 192.168.1.2:11811 | 10.0.0.1:11811 |

터틀봇의 Discovery Server는 기본적으로 `-i 0`으로 실행되므로 `ROS_DISCOVERY_SERVER`에 세미콜론 없이 `IP:PORT`만 적어야 함.

---

## ROS_SUPER_CLIENT 설명

Discovery Server 모드에서 노드는 기본적으로 **자기가 직접 통신하는 노드 정보만** 서버로부터 받아옴.
`ros2 topic list` 같은 명령은 직접 통신하는 노드가 없으므로 토픽이 표시되지 않을 수 있음.

`ROS_SUPER_CLIENT=true`로 설정하면 **서버에 등록된 모든 노드/토픽 정보를 전부 수신**:

| 모드 | 동작 |
|------|------|
| 일반 클라이언트 | 나와 관계있는 노드 정보만 받음 |
| Super Client | 서버에 등록된 전체 정보 받음 → `ros2 topic list`에 모든 토픽 표시 |

PC에서 터틀봇 토픽을 조회하려면 반드시 필요.

---

## 참고

- `/etc/turtlebot4_discovery/setup.bash`는 `~/.bashrc`에 source되어야 터미널마다 자동 적용됨
