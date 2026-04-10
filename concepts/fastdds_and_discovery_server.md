# FastDDS와 Discovery Server

## 한 줄 요약

ROS2는 DDS 표준 위에서 동작하고, FastDDS는 그 구현체 중 하나. Discovery Server는 노드 탐색 트래픽을 줄이는 중앙 등록 방식.

---

## DDS란

여러 벤더가 로봇 미들웨어를 각자 만들면 인터페이스가 달라서 같이 못 씀. 그래서 OMG(표준화 기구)가 **DDS(Data Distribution Service)** 라는 표준 규격을 정의함. "퍼블리셔/서브스크라이버가 어떻게 데이터를 주고받을지"를 규정한 명세서.

```
표준 규격 (DDS)
    └── 구현체들
         ├── FastDDS    (eProsima)       ← ROS2 Humble 기본값
         ├── CycloneDDS (Eclipse)
         ├── Connext DDS (RTI, 상용)
         └── GurumDDS   (구루네트웍스, 국내)
```

FastDDS = eProsima가 DDS 표준을 구현한 버전. ROS2 Humble에서 별도 설정 없으면 자동으로 사용.

> 검증: [ROS2 Middleware Vendors 공식 문서](https://docs.ros.org/en/humble/Concepts/Intermediate/About-Different-Middleware-Vendors.html) — FastDDS가 default, binary 배포판에 포함 확인

---

## RMW 추상화 레이어

ROS2 코드는 DDS 구현체가 뭔지 신경 쓰지 않음. **RMW(ROS Middleware interface)** 레이어가 중간에서 스위칭.

```
[ROS2 노드 코드]
      ↓
  [RMW 레이어]  ← 어떤 DDS 쓸지 여기서 결정
      ↓
  [FastDDS / CycloneDDS / ...]
```

`RMW_IMPLEMENTATION=rmw_fastrtps_cpp` 환경변수가 "RMW 레이어에 FastDDS 써라"고 지시.

---

## Simple Discovery vs Discovery Server

DDS에서 노드들이 서로를 찾는 과정을 **discovery**라고 함.

### Simple Discovery (기본값)

```
노드A 켜짐 → 네트워크 전체 브로드캐스트 → "나 켜졌어!"
           → 모든 노드가 수신 → 서로 정보 교환
```

로봇 6대 + PC 12대 환경에서 하나가 켜질 때마다 18개 전부에 패킷이 날아감. 토픽도 마구 퍼져서 트래픽 폭발.

### Discovery Server

```
노드A 켜짐 → Discovery Server에만 등록 → "나 켜졌어"
           → Server가 "TB1 관련 토픽 구독하는 애 있어?" 필터링
           → 필요한 노드끼리만 연결
```

> 검증: [ROS2 Discovery Server 공식 문서](https://docs.ros.org/en/humble/Tutorials/Advanced/Discovery-Server/Discovery-Server.html) — "nodes will only receive topic's discovery data if it has a writer or a reader for that topic" 확인

---

## 라우팅이란

네트워크에서 패킷을 목적지까지 **어느 경로로 보낼지 결정하는 것**. 집 공유기가 "이 패킷은 인터넷으로, 저 패킷은 프린터로" 분기시키는 게 라우팅.

강의장 AP가 "라우팅보다 격리 역할"인 이유: 원래 AP는 서브넷 간 패킷 전달(라우팅)도 할 수 있지만, 강의장에서는 그보다 **AP별로 TB 그룹을 물리적으로 분리**하는 게 목적.

```
AP1: TB1, TB2   ←(섞이지 않음)→   AP2: TB3, TB4
```

---

## 다른 개념 파일과의 연결

- FastDDS vs CycloneDDS 선택 이유 (RPi4 성능 한계) → [turtlebot4_lecture_5th_updates.md](turtlebot4_lecture_5th_updates.md)
- 강의장 네트워크 구성 (방식 1 vs 방식 2) → [classroom_multirobot_network_comparison.md](classroom_multirobot_network_comparison.md)
- Discovery Server ID / 세미콜론 설정 → [turtlebot4_single_robot_network.md](turtlebot4_single_robot_network.md)
