# OAK-D Image Transport 토픽 구조 및 압축 방식

## 한 줄 요약

RGB는 `/compressed`(JPEG) 써도 되지만, Depth는 JPEG이 거리값을 손상시키므로 `image_raw` 또는 `/compressedDepth`를 써야 한다.

## 핵심 내용

### OAK-D Pro 주요 이미지 토픽

```
/robot3/oakd/rgb/image_raw                   ← RGB 원본
/robot3/oakd/rgb/image_raw/compressed        ← RGB JPEG 압축 (권장)
/robot3/oakd/rgb/image_raw/compressedDepth   ← (RGB에 쓸 일 없음)

/robot3/oakd/stereo/image_raw                ← Depth 원본 (현장에서 주로 사용)
/robot3/oakd/stereo/image_raw/compressed     ← Depth에 사용 불가 (JPEG 오류)
/robot3/oakd/stereo/image_raw/compressedDepth← Depth 압축 전용 (PNG/RVL, 무손실)
```

### 왜 Depth는 `/compressed`를 못 쓰나

| 항목 | RGB (`rgb8`) | Depth (`16UC1`) |
|------|-------------|-----------------|
| 채널 수 | 3채널 (R/G/B) | 1채널 |
| 픽셀 값 의미 | 색상 | 거리값 (mm 단위 정수) |
| 비트 깊이 | 8-bit/채널 | 16-bit |
| JPEG 압축 | 가능 (손실이어도 무방) | **불가** |

JPEG은 8-bit 컬러 포맷 전용 코덱.  
`16UC1`은 컬러가 아니라 `isColor() = false` → `compressed_image_transport`가 거부함.

설령 인코딩이 된다 해도 JPEG은 **손실 압축** → 픽셀 값(거리값)이 바뀌어 측정이 틀어짐.

> 검증: `compressed_image_transport/src/compressed_publisher.cpp` (rolling branch) — JPEG 허용 조건: `enc::isColor() == true AND bitDepth == 8 or 16`  
> 에러 메시지: `"Compressed Image Transport - JPEG compression requires 8/16-bit color format (input format is: %s)"`

### `/compressedDepth`는 왜 있나

Depth 전용 무손실 압축 플러그인 (`compressed_depth_image_transport` 패키지).

- 지원 포맷: `16UC1`, `32FC1` 만
- 코덱: PNG (기본), RVL (v4.0.0+)
- JPEG 코드 없음

> 검증: `compressed_depth_image_transport/src/codec.cpp` (rolling branch) — 지원 포맷 직접 확인  
> 에러 메시지: `"Compression requires single-channel 32bit-floating point or 16bit raw depth images"`

### 현장에서 `stereo/image_raw`를 그냥 쓰는 이유

1. point cloud 생성, depth_to_laserscan 등 Depth 처리 노드들이 `image_raw` 직접 구독
2. Depth는 단채널 16-bit → raw 크기가 RGB(3채널 8-bit)보다 작아서 압축 필요성이 낮음
   - RGB raw: width × height × 3 bytes
   - Depth raw: width × height × 2 bytes
3. `/compressedDepth` 구독 시 플러그인 설치 및 디코딩 오버헤드 발생

## 다른 섹션과의 연결

- [depth_rgb_alignment.md](depth_rgb_alignment.md) — Depth/RGB 좌표계 정렬 방법
- [oakd_pro_yaml_params.md](oakd_pro_yaml_params.md) — OAK-D 드라이버 파라미터 (i_pipeline_type, 해상도 등)
- [cvbridge_and_ros2_image.md](cvbridge_and_ros2_image.md) — ROS2 Image 메시지 → OpenCV 변환

## 참고 문서

- [REP 118 — Depth Images](https://ros.org/reps/rep-0118.html): 16UC1/32FC1 포맷 정의
- [compressed_image_transport — ROS Index](https://index.ros.org/p/compressed_image_transport/): CHANGELOG v2.3.2 "JPEG only supports 8 bits images"
- [compressed_depth_image_transport — ROS Index](https://index.ros.org/p/compressed_depth_image_transport/): PNG/RVL 코덱 지원
- [image_transport_plugins GitHub](https://github.com/ros-perception/image_transport_plugins): 소스코드 직접 확인 가능
