# SLAM 개념 정리: 2D LiDAR Framework & OGM vs Costmap

## SLAM이란?

**Simultaneous Localization and Mapping** — 로봇이 미지의 환경에서 지도를 만들면서 동시에 자신의 위치를 추정하는 기술. 카메라, LiDAR, IMU 등 다양한 센서를 활용.

---

## 2D LiDAR SLAM Framework

![2D LiDAR SLAM Framework](lidar_framework.png)

| 구성 요소 | 역할 |
|-----------|------|
| **LiDAR** | 주변 환경의 거리 데이터 제공 (2D 스캔) |
| **Front-end Odometer** | 연속 스캔 간 매칭(Frame to frame matching)으로 pose 추정 → 로봇이 지금 어디 있는지 |
| **Loop Detection** | 과거 방문 위치와 현재 위치를 비교해 누적 오차 감지 |
| **Back-end Optimization** | Loop 정보를 바탕으로 전체 경로 최적화 (Kalman filter / Particle filter / Graph optimization) |
| **Global Grid Map** | 최적화된 pose로 OGM(Occupancy Grid Map) 생성 |

### Front-end 흐름
```
LiDAR 스캔 → Data preprocessing → Frame to frame matching → Pose estimation
```
### Back-end 흐름
```
Loop detection ──┐
                 ▼
         Back-end optimization → Global grid map
```

---

## OGM (Occupancy Grid Map) vs Costmap

### OGM — 원본 지도

![Occupancy Grid Map 예시](ogm_example.png)

SLAM이 생성하는 **환경 사실 지도**. 각 셀을 세 가지 상태로 기록.

| 값 | 의미 |
|----|------|
| `0` | 비어있음 (free) |
| `100` | 점유됨 (occupied) — 벽/장애물 |
| `-1` | 미탐색 (unknown) |

### Costmap — 판단용 지도

![Costmap 예시](costmap_example.png)

OGM을 가져와서 **"로봇이 여기를 지나가면 얼마나 위험한가"** 를 0~254 숫자로 계산한 지도. Nav2 경로 계획에 직접 사용.

| 값 | 의미 |
|----|------|
| `0` | 안전 |
| `~50` | 낮은 위험 |
| `~128` | 주의 |
| `~200` | 위험 |
| `253` | 치명적 |
| `254` | 장애물 (lethal) |

**Inflation Layer**: 벽/장애물 셀 주변을 일정 반경으로 팽창시켜 로봇이 벽 근처로 붙지 않도록 비용을 부여. 로봇 반경(footprint)을 반영한 안전 마진.

### 한 줄 비교

| | OGM | Costmap |
|--|-----|---------|
| **목적** | 환경 사실 기록 | 경로 계획용 위험도 계산 |
| **생성 주체** | SLAM | Nav2 (costmap_2d) |
| **값 범위** | 0 / 100 / -1 | 0 ~ 254 |
| **Inflation** | 없음 | 있음 |

---

## 참고

- ROS2 Nav2: `nav2_costmap_2d` 패키지가 OGM을 받아 costmap 생성
- global costmap: 전체 지도 기반 장기 경로 계획
- local costmap: 센서 실시간 데이터 기반 장애물 회피
