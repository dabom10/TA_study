# CvBridge와 ROS2 이미지 변환

## 한 줄 요약
CvBridge는 ROS2 Image 메시지 ↔ OpenCV 이미지(numpy 배열) 간 변환을 담당하는 도구.

## 핵심 내용

### 왜 필요한가?

ROS2와 OpenCV는 이미지를 저장하는 형식이 서로 다름.

```
ROS2 Image 메시지          OpenCV 이미지
─────────────────          ─────────────
header (시간, 프레임ID)     numpy 배열
height, width              (height, width, 채널)
encoding (bgr8 등)
data (bytes)
```

직접 호환이 안 되므로 변환 도구가 필요 → CvBridge

---

### 사용 방법

```python
from cv_bridge import CvBridge

# 노드 초기화 시 인스턴스 생성
self.bridge = CvBridge()

# ROS2 메시지 → OpenCV (구독 시)
frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

# OpenCV → ROS2 메시지 (퍼블리시 시)
msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
```

---

### 콜백에서의 역할

```python
def listener_callback(self, msg):
    self.frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
```

- `msg` — ROS2 Image 메시지 (토픽에서 수신)
- `imgmsg_to_cv2` — ROS2 메시지 → OpenCV numpy 배열로 변환
- `desired_encoding='bgr8'` — OpenCV 기본 포맷(BGR, 채널당 8비트)으로 변환
- 변환 결과를 `self.frame`에 저장해두고 메인 루프에서 사용

---

### 한 줄 구조

```
카메라(ROS2) ──[imgmsg_to_cv2]──▶ OpenCV(numpy)
카메라(ROS2) ◀──[cv2_to_imgmsg]── OpenCV(numpy)
```

## 다른 섹션과의 연결
- `2_0_a_image_publisher.py` — `cv2_to_imgmsg` 사용 (OpenCV → ROS2 퍼블리시)
- `2_0_b_image_subscriber.py` — `imgmsg_to_cv2` 사용 (ROS2 → OpenCV 표시)
- `2_1_d_capture_image.py` — 콜백에서 `imgmsg_to_cv2`로 프레임 저장
- [ros2_communication_concepts.md](ros2_communication_concepts.md) — 토픽/콜백 개념

## 의문점 / 나중에 파고들 것
- `encoding` 종류: bgr8 외에 rgb8, mono8, 32FC1 등 언제 쓰나
- CvBridge 없이 직접 변환하는 방법 (numpy로 직접 파싱)
