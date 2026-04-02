# ROS2 Bag 개념 및 용도 정리

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 22.04 |
| ROS2 | Humble |
| 로봇 | TurtleBot4 (robot8) |

---

## Bag이란?

**특정 시점의 ROS2 토픽 데이터를 통째로 녹화해뒀다가, 나중에 똑같이 재발행하는 파일**

"그 순간의 로봇 세계를 통째로 얼려둔 것"이라고 이해하면 쉽다.

---

## 핵심 용도

**로봇 없이도 로봇이 있는 것처럼 개발/테스트**

예시: 복도에서 사람을 인식하는 알고리즘 개발 중일 때

1. 로봇을 딱 한 번 실제로 주행시키며 bag 녹화
2. 이후부터는 `ros2 bag play <bag명>` 만 실행
3. 카메라, IMU, odom 등이 그 순간 그대로 재발행
4. 알고리즘은 실제 로봇 데이터인지 bag인지 구분 못함

---

## 장점

| 상황 | bag 없이 | bag 있으면 |
|------|----------|------------|
| 알고리즘 반복 테스트 | 매번 로봇 직접 주행 | `ros2 bag play` 한 번으로 끝 |
| 환경 재현 | 불가능 (조명, 장애물 등 변함) | 동일한 데이터로 항상 재현 가능 |
| 팀원과 데이터 공유 | 어려움 | bag 파일 하나 전달하면 끝 |
| 디버깅 | 실시간만 가능 | 원하는 구간 반복 재생 가능 |

---

## 토픽별 역할 (TurtleBot4 예시)

| 토픽 | 왜 녹화하나 |
|------|------------|
| `/robot8/oakd/rgb/image_raw` | 카메라 기반 알고리즘 테스트 |
| `/robot8/oakd/rgb/preview/image_raw` | 저해상도 프리뷰 (AI 추론 등 빠른 처리용) |
| `/robot8/oakd/stereo/image_raw` | 깊이(depth) 데이터 처리 테스트 |
| `/robot8/oakd/imu/data` | 카메라 내장 IMU (자세/기울기) |
| `/robot8/odom` | 위치 추정 알고리즘 테스트 |
| `/robot8/imu` | 로봇 본체 IMU |
| `/robot8/cmd_vel` | 어떤 이동 명령을 내렸는지 확인 |
| `/robot8/tf` | 로봇 각 부위 좌표 관계 |

---

## 주의사항

- bag 재생 시 `cmd_vel`이 포함되어 있으면 **로봇이 실제로 움직임**
- 녹화 시작 위치와 재생 시 로봇 위치가 다르면 **다른 경로로 이동**함
- 움직임 없이 센서 데이터만 재생하려면 `--topics` 옵션으로 토픽 선택 가능

```bash
# cmd_vel 제외하고 재생
ros2 bag play <bag명> --topics /robot8/oakd/rgb/image_raw /robot8/odom

# 특정 배율로 재생 (0.5 = 절반 속도)
ros2 bag play <bag명> --rate 0.5
```

---

## 기본 명령어

```bash
# 녹화
ros2 bag record -o <저장경로> <토픽1> <토픽2> ...
ros2 bag record -o <저장경로> -a  # 전체 토픽 녹화

# 재생
ros2 bag play <bag경로>

# 정보 확인
ros2 bag info <bag경로>
```

---

## 참고

- bag 파일 포맷: sqlite3 (`.db3`) 또는 MCAP
- `metadata.yaml`: bag의 토픽 목록, 메시지 수, 녹화 시간 등 메타정보 저장
