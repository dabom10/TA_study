# OAK-D Pro ROS2 YAML 파라미터 정리

## 한 줄 요약

depthai-ros 드라이버의 `oakd.yaml` 파라미터는 `camera` / `rgb` / `stereo` 세 섹션으로 나뉘며, `i_` prefix는 초기화 전용(재시작 필요), `r_` prefix는 런타임 변경 가능을 의미한다.

## OAK-D Pro 하드웨어 구조

```
[Left Mono (OV9782)] ←── 7.5cm ──→ [RGB 12MP (중앙)] ←── 7.5cm ──→ [Right Mono (OV9782)]
                                         ↑
                                  IR 레이저 도트 프로젝터 (Active Stereo 보조)
```

| 센서 | 역할 |
|------|------|
| 중앙 RGB | 컬러 이미지 출력 |
| Left + Right Mono 쌍 | 스테레오 매칭으로 depth 계산 |
| IR 레이저 도트 프로젝터 | 저텍스처 표면에 점 투사 → 스테레오 매칭 보조 (Active Stereo) |
| BNO085 IMU | 관성 측정 (yaml에서 별도 활성화 필요) |

## `camera` 섹션 — 전체 동작 설정

| 파라미터 | 값 | 의미 |
|---|---|---|
| `i_pipeline_type` | `RGBD` | RGB + Depth 파이프라인. `RGB`만 쓰면 depth 비활성 |
| `i_usb_speed` | `SUPER_PLUS` | USB 3.2 Gen2 최대 대역폭. 고해상도 스트리밍에 필요 |
| `i_enable_imu` | `false` | 내장 BNO085 IMU 비활성 |
| `i_enable_ir` | `false` | IR 플러드라이트 LED 비활성 (면 조명) |
| `i_floodlight_brightness` | `0` | IR 플러드라이트 밝기 (0=꺼짐, 최대 1023). 야간/저조도용 |
| `i_laser_dot_brightness` | `100` | IR 레이저 도트 프로젝터 밝기. Active Stereo로 depth 정확도 향상 |
| `i_nn_type` | `none` | 온디바이스 추론 비활성. `rgb`(2D), `spatial`(3D depth-aware) 가능 |

> `i_enable_ir: false`이지만 `i_laser_dot_brightness: 100`인 이유:
> IR 플러드라이트(면 조명)는 꺼도, 레이저 도트(점 패턴)는 depth 정확도를 위해 켜두는 경우.

## `rgb` 섹션 — RGB 카메라 설정

| 파라미터 | 값 | 의미 |
|---|---|---|
| `i_board_socket_id` | `0` | 중앙 RGB 센서 (CAM_A). 0=RGB, 1=Left Mono, 2=Right Mono |
| `i_resolution` | `640P` | 센서 캡처 해상도 (내부 설정값) |
| `i_width` / `i_height` | `704` / `704` | 출력 해상도. **16의 배수 필수** (align_depth 조건) |
| `i_fps` | `10.0` | 프레임레이트. stereo fps와 맞춰야 동기화 정상 동작 |
| `i_publish_topic` | `true` | `/rgb/image_raw` ROS 토픽 퍼블리시 |
| `i_enable_preview` | `true` | 저해상도 프리뷰 스트림 별도 생성 |
| `i_preview_size` | `320` | 프리뷰 해상도 (320×320). NN 입력용으로 주로 사용 |
| `i_keep_preview_aspect_ratio` | `true` | 프리뷰 축소 시 비율 유지 |
| `i_low_bandwidth` | `true` | USB 전송 전 압축. 대역폭 절약 |
| `i_interleaved` | `false` | RGB/Depth 프레임을 별도 토픽으로 퍼블리시 (인터리브 안 함) |
| `i_max_q_size` | `10` | 내부 프레임 큐 최대 크기. 처리 지연 시 메모리 버퍼 한도 |

## `stereo` 섹션 — Depth 설정

| 파라미터 | 값 | 의미 |
|---|---|---|
| `i_publish_topic` | `true` | `/stereo/depth` ROS 토픽 퍼블리시 |
| `i_align_depth` | `true` | Depth를 RGB 좌표계로 재투영 + RGB 출력 해상도로 upscale |
| `i_fps` | `10.0` | Depth 프레임레이트 |

## `i_align_depth` 동작 원리

Depth는 기본적으로 Left 모노 카메라 좌표계 기준으로 생성되고, 해상도도 Mono 해상도(최대 800P)로 나온다.
RGB는 중앙 카메라 기준이고 해상도가 다르다.

`i_align_depth: true`는 두 가지를 동시에 처리한다:

```
Left+Right Mono → Depth map (Left 좌표계, Mono 해상도)
                        ↓
          온디바이스 StereoDepth 노드
                        ↓
    ① 뷰포인트 재투영 (Left 좌표계 → RGB 카메라 좌표계)
    ② 해상도 upscale (Mono 해상도 → RGB 출력 해상도 704×704)
                        ↓
      /stereo/depth (RGB와 픽셀 1:1 대응, 704×704)
```

캘리브레이션 데이터(내부/외부 파라미터)가 카메라 칩셋에 사전 저장되어 있어 온디바이스 실시간 처리 가능.

출력 해상도가 16의 배수여야 하는 이유: 하드웨어 정렬 연산의 메모리 블록 단위 제약.

## 전체 데이터 흐름

```
Left Mono + Right Mono
    → 스테레오 매칭 (레이저 도트 Active Stereo 보조)
    → Depth map
    → align_depth: RGB 좌표계 재투영 + 704×704 upscale
    → /stereo/depth

RGB (640P 캡처 → 704×704 출력)
    → low_bandwidth 압축
    → /rgb/image_raw (704×704)
    → /rgb/preview/image_raw (320×320)
```

## 다른 개념과의 연결

- [depth_rgb_alignment.md](depth_rgb_alignment.md) — alignment 원리 (reprojection, FOV 차이)
- Active Stereo: IR 도트 프로젝터로 저텍스처 표면(흰 벽, 단색 바닥)의 depth 정확도 향상

---

> 검증: [OAK-D Pro Hardware Docs](https://docs.luxonis.com/projects/hardware/en/latest/pages/DM9098pro.html) — 센서 구성(12MP RGB, OV9782 스테레오, IR 프로젝터, BNO085 IMU, baseline 7.5cm) 일치
> 검증: [RGB Depth Alignment – DepthAI](https://docs.luxonis.com/projects/api/en/latest/samples/StereoDepth/rgb_depth_aligned/) — align_depth 시 RGB 해상도로 upscale, 16의 배수 제약 일치
> 검증: [DepthAI ROS Driver](https://docs.luxonis.com/software/ros/depthai-ros/driver/) — 파라미터 설명 일치
