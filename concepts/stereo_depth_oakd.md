# Stereo Depth 원리 (OAK-D Pro)

## 한 줄 요약

OAK-D Pro는 **75mm 떨어진 두 개의 스테레오 카메라**로 같은 물체가 좌/우 영상에서 어긋난 정도(disparity)를 재서 거리를 **mm 단위**로 계산한다. `거리 ∝ 1/disparity` 관계 때문에 **멀어질수록 정확도가 급격히(거리의 제곱에 비례) 떨어진다.**

## 핵심 내용

### 1. 왜 카메라가 2개인가 — 삼각측량(triangulation)

사람이 두 눈으로 거리감을 느끼는 원리와 동일하다. 같은 물체라도 가까우면 좌/우 시야에서 많이 어긋나 보이고, 멀면 거의 안 어긋난다. 이 어긋난 픽셀 양이 **disparity(시차)**.

- OAK-D Pro의 두 스테레오 센서는 **75mm(baseline, 기준선)** 간격으로 나란히 배치
- TurtleBot4(Pro)에 달리는 OAK-D Pro의 스테레오 센서는 **OV9282**, 컬러 센서는 4K IMX214

### 2. 거리 계산 공식 (focal length가 등장하는 지점)

```
        f × B
  Z = ─────────
          d
```

| 기호 | 의미 |
|------|------|
| `Z` | 물체까지 거리 (출력이 mm로 나오는 값) |
| `f` | focal length, 초점거리 (픽셀 단위) |
| `B` | baseline = 75mm (고정) |
| `d` | disparity, 두 영상에서 같은 점이 어긋난 픽셀 수 |

카메라가 매 프레임 하는 일:
1. 왼쪽/오른쪽 영상에서 **같은 지점을 매칭(stereo matching)**
2. 어긋난 픽셀 수 `d` 측정
3. 공식에 `f`, `B` 대입 → `Z`(mm) 출력

`f`와 `B`는 캘리브레이션으로 정해진 **고정값**이고, 실시간으로 변하는 건 `d` 하나다.

### 3. "멀수록 식별이 힘들다"의 이유

공식에서 **Z는 d에 반비례(Z ∝ 1/d)**. 멀어지면 `d`가 작아지는데, `d`가 작은 영역에서는 **1픽셀 오차가 큰 거리 오차로 증폭**된다. 수학적으로 거리 오차는 **거리의 제곱(Z²)에 비례** → 거리 2배면 오차 약 4배.

OAK-D Pro 측정 정확도 (800P, 75mm baseline 기준):

| 거리 | 절대 오차 |
|------|-----------|
| 4m 이하 | 2% 미만 |
| 4~7m | 4% 미만 |
| 7~10m | 6% 미만 |

이상적 동작 범위는 약 **0.8m ~ 12m**. (MinZ는 해상도·disparity 모드에 따라 ~20cm까지 내려감)

### 4. OAK-D Pro의 'Pro' 보너스 — IR 도트 프로젝터

스테레오 매칭(1번 단계)은 **무늬가 없는 흰 벽**이나 **어두운 환경**에서 실패하기 쉽다. 매칭할 특징점이 없기 때문. Pro 모델은 **IR 레이저 도트 프로젝터 + IR illumination LED**를 탑재해, 보이지 않는 점 패턴을 표면에 투사한다.
→ 무특징·저조도 환경에서도 인공 특징점을 만들어 disparity를 안정적으로 계산.

## 다른 개념과의 연결

- **Depth/RGB alignment**: 위에서 구한 depth는 스테레오 카메라 좌표계 기준. RGB detection 결과와 거리를 매칭하려면 정렬 필요 → [depth_rgb_alignment.md](depth_rgb_alignment.md)
- **OAK-D Pro 하드웨어/YAML 파라미터**: depthai-ros에서 stereo·extended disparity 등 설정 → [oakd_pro_yaml_params.md](oakd_pro_yaml_params.md)
- **이미지 토픽 구조**: depth는 `image_raw`로 발행되는 이유 → [oakd_image_transport_topics.md](oakd_image_transport_topics.md)
- **카메라 캘리브레이션**: `f`(focal length)와 distortion을 구하는 전제 단계

## 의문점 / 나중에 파고들 것

- extended disparity / subpixel 모드가 정확도와 MinZ에 미치는 영향 구체 수치
- baseline이 더 길면 원거리 정확도가 올라가지만 MinZ도 멀어지는 trade-off
- disparity → depth 변환 시 subpixel 보간이 1픽셀 오차 증폭을 얼마나 완화하는가

---

> 검증: [Luxonis OAK-D Pro hardware docs](https://docs.luxonis.com/hardware/products/OAK-D%20Pro) — baseline 75mm, 동작 범위 0.8~12m, 거리별 정확도(4m<2%, 4~7m<4%, 7~10m<6%) 일치
> 검증: [TurtleBot4 User Manual – Features](https://turtlebot.github.io/turtlebot4-user-manual/overview/features.html) — OAK-D Pro, OV9282 스테레오 센서, IR 도트 프로젝터·IR LED 일치
