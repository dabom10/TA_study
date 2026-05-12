# ROS2 OAK-D 이미지 토픽 Hz 저하 — 커널 네트워크 버퍼 튜닝

## 환경

- OS: Ubuntu (원격 PC)
- ROS2: Jazzy
- RMW: rmw_fastrtps_cpp
- 로봇: TurtleBot4 (WiFi 연결)
- 실행 구성:
  - `ros2 launch turtlebot4_navigation localization.launch.py`
  - `ros2 launch turtlebot4_navigation nav2.launch.py`
  - `ros2 launch turtlebot4_viz view_navigation.launch.py`
  - rqt로 이미지 토픽 3개 동시 구독:
    - `/robot8/oakd/rgb/image_raw`
    - `/robot8/oakd/rgb/image_raw/compressed`
    - `/robot8/oakd/stereo/image_raw`

---

## 문제 상황

이미지 토픽 Hz가 3~7Hz 수준으로 낮게 측정됨. 목표는 최소 10Hz.

---

## 원인

### 1. `net.ipv4.ipfrag_high_thresh` 기본값 4MB (핵심 원인)

이미지 한 장이 ~1~3MB 크기인데, WiFi UDP MTU는 약 1500B이므로 OS가 이미지를 수백~수천 개의 IP fragment로 분할해서 전송한다.

수신 측 PC는 fragment들을 임시 버퍼(`ipfrag_high_thresh`)에 모아 이미지를 재조합하는데, 기본값이 **4MB**뿐이다.

3개의 대형 이미지 토픽이 동시에 수신되면 fragment 총량이 4MB를 초과 → **오버플로우된 fragment 무음 드롭** → 이미지 재조합 실패 → 해당 프레임 소실 → Hz 급락.

```
[WiFi 수신]
    ↓
[ipfrag 버퍼 4MB] ← fragment 재조합 (여기서 드롭 발생)
    ↓
[rmem 소켓 버퍼] ← 재조합 완료된 이미지 대기
    ↓
[ROS2 / rqt]
```

`rmem`을 128MB로 키워도 ipfrag 단계에서 이미지가 버려지면 소켓 버퍼까지 도달하지 못한다.

### 2. `net.core.rmem_max` 기본값 208KB

소켓 수신 버퍼가 너무 작아 DDS 수신 처리 속도를 따라가지 못하면 큐 오버플로우 발생 가능.

---

## 진단 순서

1. 현재 커널 파라미터 확인
   ```bash
   cat /proc/sys/net/ipv4/ipfrag_high_thresh   # 4194304 (4MB)
   cat /proc/sys/net/ipv4/ipfrag_time          # 30
   cat /proc/sys/net/core/rmem_max             # 기본 208KB → 이미 128MB로 조정된 상태
   ```

2. rqt에서 이미지 토픽 3개 동시 구독 후 Hz 측정
   ```bash
   ros2 topic hz /robot8/oakd/rgb/image_raw --window 10
   ```

---

## 해결 방법

### 1단계: rmem/wmem 소켓 버퍼 128MB로 증가

```bash
echo 134217728 | sudo tee /proc/sys/net/core/rmem_max
echo 134217728 | sudo tee /proc/sys/net/core/rmem_default
echo 134217728 | sudo tee /proc/sys/net/core/wmem_max
echo 134217728 | sudo tee /proc/sys/net/core/wmem_default
```

결과: 3~7Hz → 4~9Hz 개선 확인. 단, 재부팅 후 초기화됨 (영속화 미완료).

### 2단계: ipfrag 재조합 버퍼 128MB로 증가 + 대기시간 단축

```bash
sudo sysctl net.ipv4.ipfrag_high_thresh=134217728
sudo sysctl net.ipv4.ipfrag_time=3
```

- `ipfrag_high_thresh`: fragment 재조합 임시 버퍼를 4MB → 128MB
- `ipfrag_time`: 불완전한 fragment 보관 시간을 30초 → 3초 (버퍼 점유 시간 단축)

결과: Hz 측정 중.

### 영속화 (재부팅 후에도 유지)

```bash
sudo tee /etc/sysctl.d/10-ros-dds.conf << 'EOF'
net.core.rmem_max=134217728
net.core.rmem_default=134217728
net.core.wmem_max=134217728
net.core.wmem_default=134217728
net.ipv4.ipfrag_high_thresh=134217728
net.ipv4.ipfrag_time=3
EOF
```

### 롤백 명령어

```bash
sudo sysctl net.ipv4.ipfrag_high_thresh=4194304
sudo sysctl net.ipv4.ipfrag_time=30
```

---

## 참고

> 검증: [ROS 2 DDS Tuning 공식 문서](https://docs.ros.org/en/rolling/How-To-Guides/DDS-tuning.html) — `ipfrag_high_thresh=134217728` 권장 명시, 일치
> 검증: `/proc/sys/net/ipv4/ipfrag_high_thresh` 직접 확인 — 적용 전 4194304 (4MB) 확인

- 추가 개선 후보 (미적용):
  - FastRTPS XML 프로파일로 비동기 발행 모드 전환
  - rqt에서 raw + compressed 동시 구독 제거 (compressed만 유지)
  - 로봇 측 `ros2 topic hz` 확인 → 소스 Hz가 낮으면 카메라 yaml fps 파라미터 수정 필요
