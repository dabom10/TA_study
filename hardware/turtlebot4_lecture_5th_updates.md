# TurtleBot4 강의 5기 변경사항 및 수업 핵심 개념

## 환경

| 항목 | 내용 |
|------|------|
| 로봇 | TurtleBot4 (iRobot Create3 + Raspberry Pi 4) |
| 미들웨어 | ROS2 |
| DDS | FastDDS (기본), CycloneDDS (비교 대상) |

---

## SDD (System Design Document) 개념

### 구성

- **BRS (Business Requirements Specification)**: 비즈니스 관점의 요구사항. "무엇을 해야 하는가"
- **SRS (System Requirements Specification)**: 시스템이 만족해야 할 기술 요구사항. "어떻게 동작해야 하는가"
- **SDD**: 위 요구사항들을 구체적인 설계로 풀어낸 문서 전체를 통칭

### 실무에서의 현실

- **한 번 정하면 바꾸기 극도로 어려움**: 수치(숫자)가 들어가는 순간부터 이해관계자 간 충돌 시작
  - 예: "응답 시간 100ms 이내" → 구현 가능한지, 책임 범위가 어디까지인지 싸움
- **현업에서는 잘 안 씀**: 시간 부족, 빠른 개발 사이클(Agile 등)과 맞지 않음
- **방산(방위산업)에서는 필수**: 인증/검수 절차가 엄격하고 계약 기반이라 문서화 요구가 높음

---

## 5기부터 바뀐 강의 내용

### 1. Lifecycle Recovery

- **배경**: 노드가 생성(`create`)은 됐는데 활성화(`activate`)가 안 되는 문제가 실습 중 빈번하게 발생
- **해결책으로 추가**: 문제 발생 시 자동 복구가 아니라 **수동으로 직접 대응**하는 방식 (자동화 아님)
- **Lifecycle Node 상태 복습**:

```
Unconfigured → [configure] → Inactive → [activate] → Active
                                ↑                        ↓
                           [deactivate]            [deactivate]
                                                        ↓
                                              ErrorProcessing (오류 시)
```

- 노드가 Active 상태가 되지 않으면 토픽을 발행/구독하지 않음 → 증상이 "아무것도 안 됨"으로 나타남

---

### 2. FastDDS Recovery Server

#### 구조

- **PC를 Discovery Server로 운영**하는 방식
- 기존 Simple Discovery (브로드캐스트) 방식 대신, 중앙 서버가 노드 정보를 관리

```
[TurtleBot4 RPi4] ←──── Discovery ────→ [PC (FastDDS Server)]
[다른 ROS2 노드]  ←──── Discovery ────→ [PC (FastDDS Server)]
```

#### FastDDS vs CycloneDDS 비교

| 항목 | FastDDS | CycloneDDS |
|------|---------|------------|
| 이미지/영상 처리 | 보통 | 더 유리 |
| 공유 메모리(SHM) 지원 | 지원 | 지원 (더 적극적) |
| 소용량 데이터 | 가능 | 너무 작은 데이터는 불리 |
| 로컬 전용 여부 | 네트워크 통신 가능 | 공유메모리는 로컬PC 내부만 |
| 선택 이유 (TurtleBot4) | RPi4 성능 한계 때문에 선택 | - |

#### TurtleBot4가 FastDDS를 선택한 이유

1. **RPi4 자체 성능 부족**: 영상처리를 RPi4에서 직접 수행 불가
2. **CycloneDDS 공유 메모리는 로컬 전용**: 네트워크 너머 PC로 데이터를 넘길 수 없음
3. **데이터를 PC로 전송 → PC에서 AI 처리 → 결과만 RPi4로 반환** 하는 구조가 필요
4. → 네트워크 통신이 가능한 **FastDDS + Discovery Server** 방식 채택

#### 레이턴시 이슈

- 영상을 PC로 전송할 때 압축 → 전송 → 수신 → 디코딩 과정에서 레이턴시 발생
- 인코딩/디코딩 방식 선택이 실시간성에 영향을 미침

---

### 3. WiFi 동글 (Dongle)

- **동글**: USB 형태의 소형 WiFi 어댑터 (외장 무선랜카드)
- **인터넷 속도**: 규격 스펙 속도의 **평균 80%** 수준이 실제 출력
  - 예: 802.11ac 이론 최대 867Mbps → 실제 ~700Mbps 수준
- 원인: 간섭, 거리 감쇠, 프로토콜 오버헤드, 환경 요인 등

---

### 4. 네트워크 이슈와 하드웨어 병목

- TurtleBot4 실습에서 네트워크 관련 문제가 자주 발생
- **공유기 교체를 검토했으나 보류**: RPi4 자체 성능이 병목이라 공유기만 바꿔도 효과 제한적
- 현재: **RPi4 설정을 다양하게 조정하면서 최적화 시도 중**
- 근본 원인은 하드웨어 성능 한계 → 소프트웨어/설정 튜닝으로 보완하는 중

---

### 5. 펌웨어 ↔ Raspberry Pi 4 시리얼 통신

- **Create3 펌웨어** (iRobot 전용 마이크로컨트롤러)와 **RPi4** 사이의 통신
- **물리 연결**: USB-C 케이블 → 내부적으로 USB 시리얼 통신
- **레이어 구조**:

```
[ ROS2 토픽/서비스 ]   ← 미들웨어 (소프트웨어 레이어)
         ↓
[ USB 시리얼 통신  ]   ← 물리 전송 레이어 (하드웨어)
         ↓
[ Create3 펌웨어   ]   ← 하드웨어 (모터, 센서 제어)
```

- **시리얼 통신 ≠ ROS2 통신이 완전히 분리된 것이 아님**
  - 시리얼이 ROS2를 대체하는 게 아니라, 시리얼 위에 ROS2 데이터를 얹는 구조
  - Create3는 USB를 통해 RPi4와 ROS2 토픽을 주고받음 (iRobot 전용 브릿지 사용)
- 시리얼 통신 종류 및 개념 → [serial_communication_types.md](../tips/serial_communication_types.md) 참고

---

## 참고

- TurtleBot4 공식 문서: https://turtlebot.github.io/turtlebot4-user-manual/
- FastDDS Discovery Server 설정: eProsima 공식 문서
- iRobot Create3 ↔ RPi4 통신: iRobot Create3 Docs (USB/Ethernet bridge)
