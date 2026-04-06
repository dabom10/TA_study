# Turtlebot4 Create3 comm LED와 ros2 topic list의 관계

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| ROS2 | Humble |
| 로봇 | Turtlebot4 (Create3 + Raspberry Pi 4) |
| 네트워크 구성 | Discovery Server |

---

## 문제 상황

Create3의 comm LED가 꺼진 상태에서도 `ros2 topic list`에 robot8의 토픽이 모두 출력됨.

---

## 원인

### Turtlebot4 네트워크 구성: Discovery Server

```
[Create3] ---USB-C--- [Raspberry Pi (Discovery Server)] ---WiFi--- [PC]
```

Discovery Server 구성에서 Create3는 **WiFi에 직접 연결할 필요가 없다.**  
모든 통신은 USB-C로 연결된 RPi를 통해 중계된다.

### comm LED의 의미

**comm LED off = Create3가 WiFi에 연결되지 않은 상태**

Discovery Server 구성에서는 이것이 **정상 동작**이다.  
Create3는 WiFi 없이 USB-C를 통해 RPi와 통신하고, RPi가 discovery server로서 모든 토픽을 네트워크에 브로드캐스트한다.

따라서 comm LED가 꺼져 있어도 `ros2 topic list`에 Create3의 토픽이 정상적으로 나타난다.

---

## Simple Discovery vs Discovery Server 비교

| 구분 | Simple Discovery | Discovery Server |
|------|-----------------|-----------------|
| Create3 WiFi 필요 여부 | **필요** | **불필요** |
| comm LED | on이어야 정상 | off가 정상 |
| 통신 경로 | Create3, RPi 각각 WiFi 직접 연결 | Create3 → USB-C → RPi → WiFi → PC |
| 권장 환경 | 1~2대, 단순 기능 | 다중 로봇, 복잡한 기능 (Navigation 등) |
| 지원 DDS | CycloneDDS, FastDDS | FastDDS only |

---

## ros2 daemon과 DDS discovery

`ros2 topic list`는 ros2 daemon에 질의한다.

- `daemon stop` → 캐시 삭제 → robot8 토픽 사라짐
- `daemon start` → **즉시** robot8 토픽 나타남

즉시 나타나는 것은 RPi의 discovery server가 살아있어 DDS discovery가 실시간으로 이루어지기 때문이다.

---

## 참고

- [Turtlebot4 Networking 공식 문서](https://turtlebot.github.io/turtlebot4-user-manual/setup/networking.html)
