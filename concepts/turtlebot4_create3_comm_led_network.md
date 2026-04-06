# Turtlebot4 Create3 comm LED와 ros2 topic list의 관계

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| ROS2 | Humble |
| 로봇 | Turtlebot4 (Create3 + Raspberry Pi 4) |

---

## 문제 상황

Create3의 comm LED가 꺼진 상태에서도 `ros2 topic list`에 robot8의 토픽이 모두 출력됨.

---

## 원인

### Turtlebot4 통신 구조

```
[Create3] ---USB-C (comm LED)--- [Raspberry Pi]
    |                                   |
    +-------WiFi 직접 연결---------[공유기]---[PC]
```

Create3는 **두 가지 통신 경로**를 가진다:
1. RPi와의 USB-C 연결 (comm LED가 나타내는 것)
2. WiFi 직접 연결 (공유기에 독립적으로 접속)

**comm LED = USB-C 연결 상태**, WiFi 연결 상태가 아님.

따라서 comm LED가 꺼져 있어도 Create3는 WiFi를 통해 DDS 브로드캐스트를 계속 보내며, `ros2 topic list`에 정상적으로 나타난다.

---

## ros2 daemon과 DDS discovery

`ros2 topic list`는 ros2 daemon에 질의한다.

- `daemon stop` → 캐시 삭제 → robot8 토픽 사라짐
- `daemon start` → **즉시** robot8 토픽 나타남

즉시 나타나는 것은 캐시가 아니라 **DDS가 실시간으로 Create3를 재발견**했다는 증거.  
Create3가 WiFi로 살아있기 때문에 가능한 것.

---

## topic list는 보이는데 echo 데이터가 없는 경우

topic list(DDS discovery)와 실제 데이터 수신은 별개 문제.  
데이터가 안 오는 원인:
- DDS QoS 불일치
- 멀티캐스트 설정 문제
- 해당 시점에 노드가 실제로 publish하지 않는 상태

---

## 참고

- Create3 공식 문서: USB-C는 RPi와의 내부 통신용, WiFi는 별도 연결
- `ros2 daemon stop && ros2 topic list` → 캐시인지 실시간인지 구분 가능
