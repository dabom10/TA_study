# Loop Detection & Loop Closure

## 한 줄 요약

Loop Detection은 "여기 왔던 곳"을 인식하는 단계, Loop Closure는 그 인식을 이용해 누적 오차를 보정하는 전체 과정.

---

## 용어 구분

```
Loop Closure (전체 과정)
├── Loop Detection  ← "이 장소, 전에 왔다" 를 인식
└── Graph Optimization ← 인식 결과로 오차 보정
```

- **Loop Detection** = Place Recognition. 현재 센서 데이터와 과거 keyframe 데이터를 비교해 같은 장소인지 판단
- **Loop Closure** = Loop Detection이 성공했을 때, pose graph에 loop constraint를 추가하고 전체 경로를 최적화하는 과정

흔히 "loop closure가 됐다"고 하면 detection + correction 전체를 의미한다.

---

## 전체 메커니즘 흐름

```
로봇 이동
    ↓
[1] Keyframe 선택
    일정 거리(예: 0.5m) 또는 각도(예: 30°) 이상 이동했을 때만 저장
    → 모든 프레임 저장 시 연산량/메모리 폭발 방지
    ↓
[2] Loop Detection (Place Recognition)
    현재 keyframe을 과거 keyframe DB와 비교
    → 유사도 점수 계산 → 임계값 초과 시 후보(candidate) 선정
    ↓
[3] Geometric Verification
    후보 keyframe과 ICP / NDT 매칭으로 정확한 상대 transform T 계산
    → 매칭이 수렴하고 오차가 작으면 loop 확정
    ↓
[4] Pose Graph에 Loop Edge 추가
    기존 odometry edge들 + 새 loop edge
    ↓
[5] Graph Optimization
    g2o / GTSAM / Ceres 등으로 전체 노드(pose)를 재조정
    → 오차가 경로 전체에 분산 흡수됨
    ↓
[6] 지도 재구성
    보정된 pose로 OGM 또는 pointcloud map 재생성
```

---

## Loop Detection 상세: 유사도를 어떻게 비교하나?

### 2D Scan 기반 (TurtleBot4 기본)

| 방법 | 설명 |
|------|------|
| **Scan Correlation** | 현재 스캔과 과거 스캔을 격자 위에 겹쳐 overlap 비율 계산 |
| **Histogram Descriptor** | 거리값 분포를 히스토그램으로 요약 후 비교 |
| **Scan Context** (2D 응용) | 거리+각도 기반 polar grid 서술자 |

SLAM Toolbox는 **Karto SLAM** 엔진 내부의 scan correlator를 사용:
- 후보 keyframe 범위를 pose graph 거리로 1차 필터링
- Correlation 계산 → 임계값 초과 시 fine scan matching으로 정밀 검증
- **Ceres Solver** (`LEVENBERG_MARQUARDT`)로 graph 최적화 (SPA가 아님)

> 검증: `/opt/ros/humble/share/slam_toolbox/config/mapper_params_online_async.yaml` — solver_plugin: `solver_plugins::CeresSolver`, trust_strategy: `LEVENBERG_MARQUARDT` 확인

### 3D Pointcloud 기반

| 방법 | 설명 | 사용 알고리즘 |
|------|------|---------------|
| **Feature Descriptor** | 점군에서 기하학적 특징점 추출 후 비교 | FPFH, SHOT, ISS |
| **Global Descriptor** | 점군 전체를 하나의 벡터로 압축 비교 | M2DP, Scan Context, PointNetVLAD |
| **Overlap 기반** | 두 점군의 겹치는 영역 비율 계산 | OverlapNet |

3D 방식은 구분력이 높지만 연산량이 크다. 긴 복도처럼 2D 스캔이 구별 못하는 환경에서 효과적.

---

## Scan vs Pointcloud 비교

| 항목 | 2D Scan (`/scan`) | 3D Pointcloud (`/pointcloud`) |
|------|------------------|-------------------------------|
| 데이터 | 단일 평면 거리값 (360°) | 3D 공간 전체 점군 |
| 정보량 | 낮음 | 높음 |
| 환경 구분력 | 낮음 (대칭/반복 구조에 취약) | 높음 |
| 연산량 | 낮음 | 높음 |
| Loop Detection 난이도 | 긴 복도, 열린 공간에서 false positive 위험 | 상대적으로 강건 |
| TurtleBot4 기본 사용 | ✅ SLAM Toolbox | ❌ (3D LiDAR 없음) |
| 3D LiDAR / Depth cam | — | ✅ RTAB-Map, LIO-SAM, LOAM |

TurtleBot4는 RPLIDAR A1(2D LiDAR)이므로 기본 구성에서는 `/scan` 기반 loop detection만 가능.
3D pointcloud 방식을 쓰려면 OAK-D(depth camera)를 활용하거나 외부 3D LiDAR 장착 필요.

---

## Pose Graph 구조

```
노드(Node) = 로봇의 각 keyframe에서의 pose (x, y, θ)
엣지(Edge) = 두 pose 간의 상대 변환 + 불확실도(covariance)

Odometry edge:  연속 keyframe 간 (front-end 제공)
Loop edge:      loop detection이 확인한 keyframe 간 (장거리 constraint)

최적화 목표: 모든 edge constraint를 최대한 만족하는 pose 집합 탐색
           = 비선형 최소제곱 문제 → g2o, GTSAM, Ceres로 풀이
```

루프가 닫히면 오차가 경로 전체에 균등하게 분산되어 흡수된다.
루프가 없으면 odometry 오차는 끝점에만 쌓인다.

---

## False Positive 문제

Loop Detection이 틀리면(다른 장소를 같은 곳으로 인식) 지도가 심각하게 왜곡된다.

대응 방법:
- **Geometric Verification 필수**: descriptor 유사도만으로 loop 확정하지 않고, ICP 매칭 수렴 + inlier 비율로 2차 검증
- **임계값 보수적 설정**: 재현율(recall)보다 정밀도(precision)를 우선
- **다중 후보 투표**: 연속 프레임에서 같은 후보가 반복 등장할 때만 확정

---

## SLAM Toolbox 관련 파라미터 (참고)

```yaml
# slam_toolbox 파라미터 중 loop closure 관련
# 출처: /opt/ros/humble/share/slam_toolbox/config/mapper_params_online_async.yaml
solver_plugin: solver_plugins::CeresSolver        # Ceres 사용 (SPA 아님)
ceres_trust_strategy: LEVENBERG_MARQUARDT

do_loop_closing: true
loop_search_maximum_distance: 3.0                 # loop 후보 탐색 최대 거리 (m)
loop_match_minimum_chain_size: 10                 # loop 인정 최소 keyframe 체인 수
loop_match_maximum_variance_coarse: 3.0
loop_match_minimum_response_coarse: 0.35
loop_match_minimum_response_fine: 0.45            # fine match 최소 유사도

# Correlation Parameters - Loop Closure
loop_search_space_dimension: 8.0                  # correlation 탐색 공간 크기 (m)
loop_search_space_resolution: 0.05
loop_search_space_smear_deviation: 0.03
```

> 검증: `/opt/ros/humble/share/slam_toolbox/config/mapper_params_online_async.yaml` 직접 읽음 — 모든 파라미터명·값 일치

---

## Scan Degeneracy: 직선 도로에서 SLAM이 실패하는 이유

직선 도로나 긴 복도에서 SLAM이 실패하는 것은 **loop detection 문제가 아니라 front-end scan matching 문제**가 근본 원인이다.

### 1방향 Degeneracy (One-directional Degeneracy)

```
로봇 진행 방향 →

|  스캔A  |  스캔B  |  스캔C  |
 벽과의 거리는 동일, 진행 방향 정보 없음
```

ICP/scan matching은 두 스캔의 차이를 최소화하는 transform을 찾는다.  
직선 환경에서는 진행 방향(x축)으로 아무리 이동해도 스캔이 동일 → 최적화 문제가 해당 방향으로 **ill-conditioned** (구속조건 부족).

### 두 문제의 관계

| 문제 | SLAM 단계 | 원인 |
|------|-----------|------|
| 진행 방향 위치 추정 불가 | **Front-end** (scan matching) | 1방향 degeneracy |
| 원위치 복귀 인식 실패 | Back-end (loop detection) | 모든 스캔이 동일하게 생겨 구분 불가 |

Loop detection 실패는 **2차 결과**다. Loop detection이 성공해도 front-end가 이미 쌓은 드리프트를 완전히 교정하기 어렵다.

### 대응 방법

- IMU, wheel encoder 등 추가 센서로 진행 방향 구속조건 보완
- 3D LiDAR 사용 시 수직 방향 특징점으로 일부 보완 가능
- 최근 연구: eigenvalue 분석으로 degeneracy 방향 감지 후 해당 축 가중치 조정 (GenZ-ICP, DALI-SLAM 등)

> 검증: [Anti-Degeneracy Scheme for Lidar SLAM](https://arxiv.org/html/2502.11486), [LiDAR SLAM in Featureless Tunnel](https://www.mdpi.com/2079-9292/12/4/1002) — "one-directional degeneracy in corridor-like structures", front-end 문제임 확인

---

## 다른 개념과의 연결

- [SLAM & OGM 기본](slam_lidar_ogm_costmap.md): Loop Detection이 SLAM 프레임워크 내 어디에 위치하는지
- Front-end(scan matching)가 쌓은 오차를 Loop Closure가 교정 → 둘은 협력 관계
- Relocalization(Nav2 AMCL)과 다름: AMCL은 완성된 지도 위에서 위치 추정, loop closure는 지도 생성 중 실시간 오차 교정

---

## 의문점 / 나중에 파고들 것

- SLAM Toolbox의 lifelong mapping 모드에서 loop closure는 어떻게 동작하나?
- 멀티로봇 환경에서 inter-robot loop closure는?
- PointNetVLAD 같은 딥러닝 기반 place recognition의 실제 ROS2 통합 사례
- loop closure 실패 감지(outlier rejection) 구체적 방법
