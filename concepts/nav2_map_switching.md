# Nav2 Map Switching (Humble vs Jazzy)

여러 맵을 런타임에 교체하면서 사용하는 멀티플로어 시나리오 — 3층에서 이동 → 엘리베이터 맵으로 스위칭 → 2층 맵으로 스위칭 — 가 ROS 2 Humble과 Jazzy에서 각각 어떻게 지원되는지 정리.

## 한 줄 요약

- **Humble / Jazzy 모두** `nav2_map_server`의 `load_map` 서비스로 런타임 맵 교체가 가능하다.
- **Jazzy 신규**: `nav2_route` (Route Server)가 멀티플로어 그래프 + 엘리베이터/계단 트리거 프레임워크를 제공한다. 단, 맵 교체 자체를 자동으로 해주지는 않고 사용자가 `load_map`을 트리거 안에서 호출하는 식으로 엮어야 한다.

## `load_map` 서비스 (Humble + Jazzy 공통)

> 검증: https://docs.ros.org/en/humble/p/nav2_map_server/ — 일치
> 검증: https://docs.ros.org/en/jazzy/p/nav2_map_server/ — 일치

문서 원문:
> "Map server will expose maps on the node bringup, but can also change maps using a `load_map` service during run-time."

서비스 타입: `nav2_msgs/srv/LoadMap`

```bash
ros2 service call /map_server/load_map nav2_msgs/srv/LoadMap \
  "{map_url: /path/to/floor2.yaml}"
```

### 맵 교체 시 사용자가 직접 처리해야 하는 것
- AMCL 초기 pose 재설정 (`/initialpose` 발행)
- Costmap 클리어 (`/global_costmap/clear_entirely_global_costmap` 등)
- 진행 중이던 Nav2 goal 취소 후 재설정

## Jazzy의 Route Server (`nav2_route`)

> 검증: https://docs.ros.org/en/jazzy/p/nav2_route/__README.html — 일치
> 검증: https://discourse.openrobotics.org/t/nav2-jazzy-roadmap-announcement/32127 — 일치 (Jazzy 로드맵에 Route Server 포함)

문서 원문:
- "Multi-floor navigation using graph nodes as terminals for stairs, elevators, etc"
- "free-space planning can be used between on-floor nodes and graph connections for floor connectors to enact specific behaviors to call elevators, climb stairs, etc."
- Route operation은 `std_srvs/Trigger`로 외부 서비스(엘리베이터 호출, 문 열기 등) 트리거 가능

### 구조적 패턴
1. 층 전환 지점(엘리베이터, 계단)을 그래프 노드로 모델링
2. 해당 노드 도달 시 Route Operation 플러그인 발동
3. 플러그인 내부에서 `load_map` 호출 + AMCL 초기화 + 새 골 설정

## 비교 표

| 기능 | Humble | Jazzy |
|---|---|---|
| `load_map` 런타임 맵 교체 | ✅ | ✅ |
| 멀티플로어 그래프/엘리베이터 트리거 프레임워크 (`nav2_route`) | ❌ | ✅ |
| 맵 교체 후 AMCL/costmap 자동화 | ❌ (직접 구현) | ❌ (직접 구현) |

## 다른 섹션과의 연결
- [[nav2_amcl_tf_tree]] — 맵 교체 시 AMCL/TF 트리 재초기화 필요
- [[slam_concepts]] — 맵 생성 측면

## 참고 링크
- nav2_map_server (Humble): https://docs.ros.org/en/humble/p/nav2_map_server/
- nav2_map_server (Jazzy): https://docs.ros.org/en/jazzy/p/nav2_map_server/
- LoadMap.srv: https://docs.ros.org/en/ros2_packages/jazzy/api/nav2_msgs/srv/LoadMap.html
- nav2_route README (Jazzy): https://docs.ros.org/en/jazzy/p/nav2_route/__README.html
- Nav2 Jazzy Roadmap: https://discourse.openrobotics.org/t/nav2-jazzy-roadmap-announcement/32127
- 실전 예시: https://automaticaddison.com/how-to-load-a-new-map-for-multi-floor-navigation-using-ros-2/

## 의문점 / 나중에 파고들 것
- Route Server에 실제 엘리베이터 트리거 + `load_map` 연동 예제 코드가 공식 저장소에 있는지
- 맵 교체 시 transform_tolerance, source_timeout 영향
