# Depth/RGB Camera Alignment (Pixel-to-Pixel Alignment)

## 한 줄 요약

Depth 카메라와 RGB 카메라는 렌즈와 FOV가 달라서, 검출된 객체의 거리를 가져오려면 사전에 두 이미지를 pixel-to-pixel로 정렬해야 한다.

## 핵심 내용

### 왜 정렬이 필요한가

- Depth 카메라와 RGB 카메라는 **별개의 렌즈**를 사용 → 광학 중심(optical center) 위치가 다름
- **FOV(Field of View, 화각)** 도 다름 — 같은 공간을 봐도 zoom 수준이 달라 각 픽셀이 가리키는 실제 위치가 불일치
- 결과: RGB 이미지의 픽셀 (u, v) 와 Depth 이미지의 픽셀 (u, v) 가 서로 다른 공간 좌표를 가리킴

### 정렬 방법

Depth 이미지를 RGB 카메라 좌표계로 reprojection하는 방식:

```
Depth pixel → 3D 공간 좌표 (카메라 내부 파라미터 이용)
→ RGB 카메라 좌표계로 변환 (외부 파라미터 이용)
→ RGB 이미지 평면에 재투영 (RGB 카메라 내부 파라미터 이용)
```

또는 lookup table(LUT) 방식으로 미리 계산된 매핑 테이블 사용.

### 사전 처리 (Pre-processing) 필수

- 매 프레임마다 reprojection 연산을 실시간으로 하는 것은 비효율적
- **카메라 캘리브레이션** 단계에서 내부/외부 파라미터를 구하고, 정렬된 이미지 쌍을 만들어 두는 방식
- OAK-D 같은 RGB-D 카메라는 하드웨어 레벨에서 aligned depth stream을 제공하기도 함

### 언제 필요한가

| 용도 | 필요 여부 |
|------|-----------|
| 단순 객체 detection (2D bounding box) | 불필요 |
| **detection된 객체의 거리 측정** | **필수** |
| 포인트 클라우드 생성 (3D reconstruction) | 필수 |
| depth-only 장애물 감지 | 불필요 |

→ RGB로 detection → bounding box 중심 픽셀 → aligned depth에서 해당 픽셀 거리값 조회하는 파이프라인에서 필수

## 다른 개념과의 연결

- **카메라 캘리브레이션**: 내부 파라미터(fx, fy, cx, cy, distortion)와 외부 파라미터(R, t) 추정 → alignment의 전제 조건
- **포인트 클라우드**: aligned depth + RGB → 각 픽셀에 색상 정보가 있는 3D 점군 생성 가능
- **객체 거리 측정**: detection node가 bounding box를 퍼블리시하면, depth node에서 해당 영역의 depth 값을 읽어 거리 계산

## 의문점 / 나중에 파고들 것

- ROS2에서 depth-RGB aligned 토픽을 어떻게 구독하고 동기화하는가? (`message_filters::ApproximateTime`)
- OAK-D의 경우 `stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)` 옵션으로 alignment 설정

---

> 검증: [Align Depth and Color Frames – Depth and RGB Registration](https://www.codefull.net/2016/03/align-depth-and-color-frames-depth-and-rgb-registration/) — FOV 차이 및 reprojection 방식 일치  
> 검증: [Luxonis RGB-D docs](https://docs.luxonis.com/software/perception/rgb-d/) — 사전 정렬(pre-processing) 방식 일치
