# Stereo Depth 원리 (OAK-D Pro)

## 한 줄 요약

OAK-D Pro는 **75mm 떨어진 두 개의 스테레오 카메라**로 같은 물체가 좌/우 영상에서 어긋난 정도(disparity)를 재서 거리를 **mm 단위**로 계산한다. `거리 ∝ 1/disparity` 관계 때문에 **멀어질수록 정확도가 급격히(거리의 제곱에 비례) 떨어진다.**

## 핵심 내용

### 1. 왜 카메라가 2개인가 — 삼각측량(triangulation)

사람이 두 눈으로 거리감을 느끼는 원리와 동일하다. 같은 물체라도 가까우면 좌/우 시야에서 많이 어긋나 보이고, 멀면 거의 안 어긋난다. 이 어긋난 픽셀 양이 **disparity(시차)**.

- OAK-D Pro의 두 스테레오 센서는 **75mm(baseline, 기준선)** 간격으로 나란히 배치
- TurtleBot4(Pro)에 달리는 OAK-D Pro의 스테레오 센서는 **OV9282**, 컬러 센서는 4K IMX214

> **baseline이란?** 스테레오 카메라 **두 렌즈 사이의 거리**. 사람의 **양쪽 눈 간격(≈6.5cm)**에 해당. 이 간격이 있어야 같은 물체를 서로 다른 각도로 보게 되고, 그 차이(disparity)로 거리를 잴 수 있다. OAK-D Pro는 75mm 고정.

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

### 5. baseline을 늘리면 정확도는? — trade-off

> ⚠️ **baseline은 하드웨어 고정값.** 두 센서가 PCB에 75mm 간격으로 납땜되어 있어 **소프트웨어로 못 바꾼다.** 아래 trade-off는 한 대를 튜닝하는 얘기가 아니라 **카메라 모델을 고를 때**의 설계 선택이다 (근접용 OAK-D SR 2cm vs 범용 OAK-D Pro 7.5cm).

거리 오차를 공식으로 보면 (Z를 d로 미분):

```
        Z²
  ΔZ ≈ ────── × Δd      (Δd = 매칭 1픽셀 오차, 고정)
        f × B
```

분모에 `B`가 있으므로 **B를 키우면 ΔZ(거리 오차)가 작아진다.** 직관적으로는 baseline이 길수록 같은 물체라도 좌/우 영상에서 더 많이 어긋나(disparity↑) 보여서, 1픽셀 오차가 차지하는 비중이 줄어 거리가 안정적이다. 하지만 공짜가 아니다:

| 항목 | baseline **길게** | baseline **짧게** |
|------|------|------|
| 원거리 정확도 | **좋음** (오차% ↓) | 나쁨 |
| MinZ (최소 측정 거리) | 멀어짐 (가까운 거 못 봄) | **가까워짐** |
| MaxZ (최대 범위) | **넓음** | 좁음 |
| occlusion(가림) | 많음 | 적음 |
| 적합 용도 | 실외·장거리 센싱 | 근접 정밀 작업 |

- **MinZ = f × B / max_disparity** → B가 분자에 있어 **B↑ → MinZ↑** (너무 가까우면 disparity가 최대 한계 초과로 측정 불가). OAK-D Pro 75mm → MinZ 약 70~80cm.
- **MaxZ = (B/2) × tan(...)** → B↑ → 더 먼 거리까지 측정 (OAK-D 7.5cm ≈ 38m, OAK-D-CM4 9cm ≈ 46m).
- occlusion: 두 카메라가 멀수록 한쪽에서만 보이는 영역이 커져 물체 가장자리에 depth 구멍 증가.

→ Luxonis 권고: **측정하려는 거리에 맞춰 baseline을 고른다.** 근접용 OAK-D SR은 baseline을 2cm로 줄여 1m 이내 정밀도를 택함.

### 6. focal length(f)의 영향 — baseline과 뭐가 다른가

`f`와 `B`는 둘 다 정확도 공식 `ΔZ ≈ Z²/(f·B)·Δd`의 분모에 있어 **각각 키우면 정확도가 좋아진다.** 단 성격과 부작용이 다르다.

| | **focal length (f)** | **baseline (B)** |
|---|---|---|
| 무엇 | 카메라 **1개**의 속성 (렌즈↔센서 거리) | 카메라 **2개 사이** 거리 |
| 비유 | 한쪽 눈의 렌즈 배율(줌) | 양쪽 눈 사이 간격 |
| 정확도 키우는 부작용 | **화각(FOV)이 좁아짐** (좁은 영역만 봄) | **MinZ 멀어짐** (가까운 거 못 봄) |

**focal length의 영향 2가지:**
1. **화각 결정** — f 길면(망원) 좁고 멀리 자세히, f 짧으면(광각) 넓게.
2. **depth 정확도** — f 클수록 ΔZ↓ → 원거리 정확도↑. 대신 화각이 좁아지는 trade-off.

> `focal_length_in_pixels`는 **해상도를 바꾸면 스케일**된다(800P→400P 등). 물리 렌즈(mm)는 그대로지만 픽셀 환산값이 달라지는 것 — driver가 현재 해상도 기준으로 자동 처리.

**yaml에 focal length 파라미터는? → 없다.** focal length는 튜닝값이 아니라 **공장 캘리브레이션 측정값**으로, 디바이스 EEPROM에 저장된 값을 driver가 읽어 `camera_info`(fx, fy, cx, cy)로 발행한다. 굳이 바꾸려면(재캘리브레이션 시):

| 방법 | 설명 |
|------|------|
| `i_calibration_file` | 커스텀 캘리브레이션 파일 경로 지정 → 디바이스 기본값 대신 사용 |
| `set_camera_info` 서비스 | 각 이미지 스트림마다 런타임에 camera_info 오버라이드 |

→ yaml에서 만지는 건 해상도·fps·stereo 모드뿐. **f와 B 둘 다 "주어지는 값"이고, 실시간으로 변하는 건 disparity(d) 하나뿐.** (차이: baseline은 물리 구조라 재캘리브레이션으로도 불변, focal length는 캘리브레이션 파일로 보정값 교체 가능)

## 다른 개념과의 연결

- **Depth/RGB alignment**: 위에서 구한 depth는 스테레오 카메라 좌표계 기준. RGB detection 결과와 거리를 매칭하려면 정렬 필요 → [depth_rgb_alignment.md](depth_rgb_alignment.md)
- **OAK-D Pro 하드웨어/YAML 파라미터**: depthai-ros에서 stereo·extended disparity 등 설정 → [oakd_pro_yaml_params.md](oakd_pro_yaml_params.md)
- **이미지 토픽 구조**: depth는 `image_raw`로 발행되는 이유 → [oakd_image_transport_topics.md](oakd_image_transport_topics.md)
- **카메라 캘리브레이션**: `f`(focal length)와 distortion을 구하는 전제 단계

## 의문점 / 나중에 파고들 것

- extended disparity / subpixel 모드가 정확도와 MinZ에 미치는 영향 구체 수치
- disparity → depth 변환 시 subpixel 보간이 1픽셀 오차 증폭을 얼마나 완화하는가

---

> 검증: [Luxonis OAK-D Pro hardware docs](https://docs.luxonis.com/hardware/products/OAK-D%20Pro) — baseline 75mm, 동작 범위 0.8~12m, 거리별 정확도(4m<2%, 4~7m<4%, 7~10m<6%) 일치
> 검증: [TurtleBot4 User Manual – Features](https://turtlebot.github.io/turtlebot4-user-manual/overview/features.html) — OAK-D Pro, OV9282 스테레오 센서, IR 도트 프로젝터·IR LED 일치
> 검증: [Luxonis StereoDepth node docs](https://docs.luxonis.com/software/depthai-components/nodes/stereo_depth/) — baseline↑ → 원거리 정확도↑·MinZ↑ trade-off 일치
> 검증: [Luxonis Configuring stereo depth](https://docs.luxonis.com/hardware/platform/depth/configuring-stereo-depth/) — MinZ=f·B/max_disparity, MaxZ=(B/2)·tan(...), baseline 고정 하드웨어, focal_length_in_pixels 해상도 스케일 일치
> 검증: [depthai-ros driver 파라미터 문서](https://docs.luxonis.com/software/ros/depthai-ros/driver/) — focal length 직접 설정 파라미터 없음, `i_calibration_file`/`set_camera_info`로만 오버라이드 가능 일치
