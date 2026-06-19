# ROS2 통신 계층 구조 (rclpy/rclcpp → rcl → rmw → implementation → DDS)

> 검증: https://design.ros2.org/articles/ros_middleware_interface.html — 계층 구조(rclpy/rclcpp → rcl → rmw → rmw implementation → DDS) 및 `RMW_IMPLEMENTATION` 환경변수로 런타임 구현 선택 가능함 일치

`publisher.publish(msg)` 한 줄이 실제로 네트워크에 데이터를 실어 보내기까지 거치는 6개 층 정리.

---

## 1. 한 줄 요약

내 코드는 "보내!"라고 말만 하고 → `rcl`이 접수 → `rmw` 양식대로 → `implementation`(통역기)이 DDS 언어로 번역 → `DDS`(택배 회사)가 실제로 네트워크에 쏜다.

위로 갈수록 "무엇을(what)", 아래로 갈수록 "어떻게(how)".

---

## 2. 전체 6층 구조

```
①  내 코드 (rclpy / rclcpp)     "보내!" 라고 말만 함        (껍데기)
        │
②  rcl                          핵심 기능 알맹이            (C, 언어 공통)
        │
③  rmw                          빈 규격 (약속서)            (.h 선언만)
        │
④  rmw implementation           통역기 (ROS말 → DDS말)      (.cpp, 얇음)
        │
⑤  DDS                          실제 통신 본체 (택배 회사)   (진짜 일꾼)
        │
⑥  OS (Ubuntu 등)               맨 바닥 (도로)
        │
     네트워크 → 상대 노드
```

---

## 3. 각 층이 하는 일

### ① 내 코드 (rclpy / rclcpp)
- Python(`rclpy`) 또는 C++(`rclcpp`)으로 짠 노드.
- `publisher.publish(msg)` 라고 **말만** 함. 실제 통신은 안 함.
- `rclpy`, `rclcpp` 모두 얇은 언어 바인딩 — 실제 일은 아래층(rcl)에 넘김.

### ② rcl (ROS Client Library)
- "노드 만들기, 토픽 보내기" 같은 **핵심 기능이 C언어로 한 번** 구현된 알맹이.
- Python/C++ 어느 쪽으로 짜든 결국 다 여기로 모임.
  ```
  rclpy (Python 껍데기)  ┐
                         ├──→  rcl (진짜 알맹이)
  rclcpp (C++ 껍데기)    ┘
  ```
- → **언어가 달라도 동작이 똑같음.**
- 여기까지가 "ROS 영역". 어떤 DDS로 통신할지는 아직 미정.

### ③ rmw (ROS MiddleWare)
- **빈 규격(인터페이스).** "통신 함수는 이런 이름·모양이어야 한다"는 약속만 있고 **알맹이는 없음.**
- ROS가 모든 DDS에 공통으로 쓰려고 정한 통일 양식.
- 비유: "택배 맡기려면 이런 송장 양식 써라"는 **표준 송장 규격.**

### ④ rmw implementation
- ③의 빈 규격을 **실제로 채운 통역기 코드.**
- rcl이 준 데이터를 받아 → **특정 DDS가 알아듣는 형태로 변환** → DDS에 넘김.
- DDS 벤더마다 하나씩:
  - `rmw_fastrtps_cpp` — Fast DDS용
  - `rmw_cyclonedds_cpp` — Cyclone DDS용
  - `rmw_connextdds` — RTI Connext용
- **하는 일은 얇음(번역/중개만). 직접 배달하진 않음.**

### ⑤ DDS (Data Distribution Service)
- **진짜 일꾼.** 데이터를 네트워크에 실어 상대 노드까지 배달.
- **ROS와 무관하게 원래부터 독립적으로 존재하는 프로그램** (Fast DDS, Cyclone DDS 등). ROS는 갖다 쓸 뿐.
- 무거운 일은 여기서: **Discovery(상대 찾기), QoS(배달 보장 수준), Domain ID(구역 나누기).**

### ⑥ OS (Ubuntu 등)
- DDS가 그 위에서 돌아가는 바닥. 트럭이 달리는 도로.

---

## 4. 비유로 한 번에 (택배 보내기)

| 층 | 비유 | 역할 |
|---|---|---|
| ① 내 코드 | 편지 쓰는 나 | "이거 보내줘"만 함 |
| ② rcl | 동네 우체국 | 누가 맡기든 똑같이 접수 |
| ③ rmw | 표준 송장 규격 | "이 양식으로 맡겨라" |
| ④ implementation | 택배사 전담 창구 직원 | ROS말 → 택배사말 통역 |
| ⑤ DDS | 실제 택배 회사 (CJ, 한진) | 트럭 몰고 진짜 배달 |
| ⑥ OS | 도로 | 그 위를 달림 |

---

## 5. 데이터가 내려가는 흐름 (옷 갈아입기)

```
① rcl에 데이터 있음            (ROS 원본 데이터)
        ↓
② rmw 양식으로 정리됨           (ROS 통일 모양)
        ↓
③ implementation이 변환         (Fast DDS가 알아듣는 모양으로)   ★여기서 번역★
        ↓
④ DDS로 전송                    (실제 네트워크로 발사)
```

- **데이터** = rcl 모양 → rmw 양식 → DDS 모양으로 옷을 갈아입으며 내려감.
- **implementation** = 옷을 갈아입혀주는 **직원(코드)**. 데이터가 아니라 행위자.

### 왜 rmw 양식 ≠ DDS 형태인가
- **rmw 양식** = "ROS가" 정한 통일 모양 (모든 DDS 공통).
- **DDS 형태** = "그 DDS 회사가" 정한 자기만의 모양 (ROS 생기기 전부터 독립).
- 둘이 안 맞으니까 implementation이 **한 번 더 번역.**
- 이 차이를 implementation 층에서 다 흡수 → 위층은 DDS가 뭐로 바뀌든 신경 안 써도 됨.

---

## 6. 통신 외 코드는 언제 실행되나? (콜백)

내 노드 안에는 두 종류 코드가 섞여 있음:

- **(A) 통신 코드** — `publish`, `create_subscription` 등 → rcl→rmw→DDS 사다리.
- **(B) 그 외** — YOLO 추론, 좌표 계산, if/for, numpy → 사다리 안 탐. 내 프로세스가 직접 실행.

**(B)는 콜백(callback)으로 실행됨.**

```python
def scan_callback(self, msg):       # ← (B) 내가 짠 로직
    distance = min(msg.ranges)
    if distance < 0.5:
        self.publisher.publish(cmd)  # ← (A) 통신

self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
```

실행 흐름:
1. DDS가 `/scan` 데이터를 네트워크에서 받음 (맨 아래층)
2. rmw → rcl을 타고 "데이터 왔다!" 신호가 올라옴
3. **`rclpy.spin()`** 이 보고 내가 등록한 `scan_callback`을 **대신 호출**
4. 콜백 안의 (B) 코드는 평범한 파이썬으로 쭉 실행

> `rclpy.spin(node)` = 데이터 올 때까지 기다리다가, 오면 콜백 불러주는 무한 루프. 통신층과 내 로직(B)을 잇는 다리.

- rcl이 하는 일: 통신 + **"언제 내 코드를 부를지" 타이밍 관리** (콜백, 타이머).
- 비유: rcl/DDS는 **우편함**. 배달까지만 해주고, 읽고 답장 쓰는 일(B)은 내가 함.

---

## 7. rmw vs implementation vs DDS 차이 (제일 헷갈리는 부분)

| | rmw (인터페이스) | rmw implementation | DDS |
|---|---|---|---|
| 정체 | 약속/규격 (빈 양식) | 약속을 채운 통역기 | 실제 통신 본체 |
| 알맹이 | 없음 | 있음 (DDS별로 다름) | 있음 (진짜 다 함) |
| 개수 | 하나 (표준) | 여러 개 (벤더마다) | 여러 개 (독립 SW) |
| ROS 거? | ROS가 만듦 | ROS가 만듦 | **ROS와 무관한 독립 SW** |
| 일의 양 | — | 얇음 (번역만) | 두꺼움 (실제 통신) |
| 비유 | 송장 규격 | 택배사 전담 직원 | 택배 회사 |
| 예시 | rmw.h | `rmw_fastrtps_cpp` | Fast DDS |

- ④와 ⑤는 **짝꿍** — `rmw_fastrtps_cpp`(전담 직원) ↔ Fast DDS(회사 본체).

---

## 8. 실제 파일 모양

### rmw (인터페이스) — `.h`, 선언만
```c
// rmw/include/rmw/rmw.h
rmw_ret_t rmw_publish(
    const rmw_publisher_t * publisher,
    const void * ros_message,
    rmw_publisher_allocation_t * allocation);
```
→ 중괄호 `{}` 안 내용 없음. "이런 함수가 있어야 한다"는 약속.

### implementation — `.cpp`, 같은 함수에 알맹이 채움
```cpp
// rmw_fastrtps_cpp/src/rmw_publish.cpp
rmw_ret_t rmw_publish(
    const rmw_publisher_t * publisher,
    const void * ros_message,
    rmw_publisher_allocation_t * allocation)
{
    // ROS 데이터를 Fast DDS 형식으로 변환
    // Fast DDS의 publisher->write() 호출
    ...
}
```
→ rmw.h 선언과 **이름·모양이 완전히 똑같고**, 속을 Fast DDS로 채운 본체.

### 폴더 구조
```
rmw/                        ← 인터페이스 패키지
 └─ include/rmw/rmw.h        ← 함수 선언 (.h, 빈 약속)

rmw_fastrtps_cpp/           ← implementation 패키지
 ├─ src/rmw_publish.cpp      ← rmw_publish 실제 구현
 ├─ src/rmw_create_node.cpp
 └─ ...                      ← rmw.h의 모든 함수를 하나씩 .cpp로 구현
        │
        └── 내부에서 Fast DDS 라이브러리를 호출
```

| | 정체 | 파일 |
|---|---|---|
| rcl | C 코드 알맹이 | `.c` / `.h` |
| rmw | 인터페이스 (선언) | `.h` (함수 선언만) |
| implementation | 선언을 채운 C++ 구현 | `rmw_fastrtps_cpp/src/*.cpp` |

---

## 9. 층을 나눈 진짜 이유

DDS를 바꾸고 싶을 때, 환경변수 한 줄로:

```bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp    # 통역기+DDS 모두 Fast
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp  # 통역기+DDS 모두 Cyclone
```

- 한 줄로 ④⑤가 통째로 갈림.
- **① 내 코드는 한 글자도 안 고침.** (rcl은 함수 *이름*만 보고 호출, 어느 `.cpp`가 불릴지는 환경변수가 결정)
- **윗층은 아랫층이 뭘로 바뀌든 모른다** — 이게 층을 나눈 이유.

---

## 10. TA 트러블슈팅 연결

- TA 때 겪은 통신 문제(QoS 안 맞음, Discovery 안 됨)는 대부분 **⑤ DDS층** 일.
- ① 내 코드를 들여다봐도 안 보임 — 문제는 맨 아래 두 층에서 났으니까.
- "코드는 멀쩡한데 왜 통신이 깨지지?" → **위층 코드가 아니라 아래 DDS 설정(QoS/Discovery/Domain)을 봐라.**

관련: [[fastdds_and_discovery_server]], [[ros2_communication_concepts]], [[humble_vs_jazzy_fastdds]]

---

## 참고

- ROS 2 Design — ROS Middleware Interface: https://design.ros2.org/articles/ros_middleware_interface.html
