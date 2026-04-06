# 시리얼 통신 종류 및 개념 정리

## 환경

| 항목 | 내용 |
|------|------|
| 적용 레벨 | 하드웨어 간 물리적 통신 (임베디드, 로봇, MCU) |
| 관련 맥락 | TurtleBot4 Create3 펌웨어 ↔ Raspberry Pi 4 통신 |

---

## 시리얼 통신이란?

데이터를 **1비트씩 순서대로(직렬)** 전송하는 방식. 병렬 통신(여러 비트 동시 전송)과 반대 개념.

> 하드웨어 간의 물리적 전송 레이어. ROS2 같은 미들웨어와는 레이어가 다름.

---

## ROS2와 시리얼 통신의 관계

```
[ ROS2 토픽/서비스 ]   ← 미들웨어 레이어 (응용/소프트웨어)
         ↓ 직렬화(serialize)된 데이터를 실어서 전송
[ UART / USB 시리얼 ]  ← 물리적 전송 레이어 (하드웨어)
```

- 시리얼 통신이 ROS2를 **대체**하는 것이 아님
- 시리얼 통신은 데이터를 실어 나르는 **전송 수단**
- `micro-ROS`, `rosserial` 같은 라이브러리가 시리얼 위에 ROS2 메시지를 올려줌
- **TurtleBot4 예시**: Create3 펌웨어 ↔ RPi4 사이는 USB 시리얼로 물리 연결 → 그 위에서 ROS2 토픽 주고받음

---

## 주요 시리얼 통신 종류 비교

| 방식 | 동기/비동기 | 선 수 | 속도 | 특징 |
|------|-------------|-------|------|------|
| **UART** | 비동기 | 2선 (TX, RX) | 저~중 | 가장 기본, 1:1 통신, 별도 클럭 선 없음 |
| **SPI** | 동기 | 4선 (MOSI, MISO, SCK, CS) | 고속 | 마스터-슬레이브, 전이중(full-duplex) |
| **I2C** | 동기 | 2선 (SDA, SCL) | 저~중 | 다중 슬레이브 가능, 주소로 구분 |
| **USB** | 복합 (별도 계층) | 4선 이상 | 고속 | 플러그앤플레이, PC와 임베디드 연결에 흔함 |
| **CAN** | 비동기 | 2선 (CAN-H, CAN-L) | 중 | 차량/산업용, 노이즈에 강함, 다중 노드 |
| **RS-232** | 비동기 | 다수 | 저 | 구형 산업용, 장거리 약함 |
| **RS-485** | 비동기 | 2선 (차동) | 중 | 산업용 장거리, 노이즈 강함, 최대 1.2km |

---

## 각 방식 상세 설명

### UART (Universal Asynchronous Receiver-Transmitter)

- **비동기**: 송수신 측이 미리 약속된 속도(baud rate)로만 맞추면 됨. 클럭 선 없음.
- TX(송신) → 상대방 RX(수신)로 교차 연결
- 설정 항목: baud rate, data bits, stop bits, parity
- 용도: MCU↔센서, MCU↔MCU, 디버그 콘솔, GPS 모듈 등

```
Device A: TX ──────────────── RX :Device B
Device A: RX ──────────────── TX :Device B
```

### SPI (Serial Peripheral Interface)

- **동기**: 마스터가 클럭(SCK)을 생성해서 타이밍을 맞춤
- MOSI: Master Out Slave In / MISO: Master In Slave Out / CS: Chip Select (슬레이브 선택)
- 슬레이브가 여러 개면 CS 선을 슬레이브 수만큼 늘림
- 용도: 디스플레이, SD카드, IMU 센서, ADC 등 고속 데이터 전송

### I2C (Inter-Integrated Circuit)

- **동기**: SDA(데이터) + SCL(클럭) 2선만으로 다중 슬레이브 통신
- 각 슬레이브는 고유 **7비트 주소**를 가짐 → 주소로 대상 선택
- 속도가 느린 편 (표준 100kbps, 고속 400kbps)
- 용도: 온도 센서, OLED 디스플레이, EEPROM 등 저속 소형 센서

### USB (Universal Serial Bus)

- SPI/I2C처럼 클럭을 공유하는 방식이 아님 → 단순히 "동기/비동기"로 분류 불가
- control / bulk / interrupt / isochronous 네 가지 전송 방식을 가지는 별도 계층
- 플러그앤플레이, 핫스왑 지원
- 임베디드 보드에서 USB-to-UART 변환 칩(CH340, FT232 등)을 통해 PC와 연결하는 경우 많음
- **TurtleBot4**: Create3 ↔ RPi4를 USB-C로 연결 → **Ethernet over USB** 방식으로 IP 통신  
  (Create3는 `192.168.10.1:8080`으로 webserver 노출 → "시리얼" 아닌 네트워크 통신)

### CAN (Controller Area Network)

- 차동 신호(CAN-H, CAN-L)로 노이즈에 매우 강함
- 하나의 버스에 여러 노드가 연결 가능 (ID로 구분)
- 자동차 ECU 간 통신, 산업용 로봇 등에 사용
- 로봇팔 관절 모터 제어에도 활용 (예: Dynamixel 일부 모델)

---

## 동기 vs 비동기 차이

| 항목 | 동기 (Synchronous) | 비동기 (Asynchronous) |
|------|-------------------|----------------------|
| 클럭 공유 | 공유함 (별도 CLK 선) | 공유 안 함 |
| 타이밍 맞추는 방법 | 마스터 클럭 기준 | 사전 약속된 baud rate |
| 예시 | SPI, I2C | UART, CAN |

---

## 참고

- TurtleBot4 Create3 ↔ RPi4: USB-C → **Ethernet over USB** → ROS2 토픽/서비스 (IP 네트워크 기반)
  - Create3는 ROS2를 직접 실행하는 플랫폼 (마이크로컨트롤러가 아님)
  - micro-ROS 미사용 (micro-ROS는 MCU 같은 마이크로컨트롤러 전용 경량 프레임워크)
  - `create3_republisher` 노드가 Create3 토픽을 RPi 네임스페이스로 재발행
- rosserial: 시리얼 통신 위에 ROS 메시지를 전송하는 패키지 (ROS1 주력, ROS2는 micro-ROS 권장)
