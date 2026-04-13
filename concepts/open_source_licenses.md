# 오픈소스 라이선스 종류

## 한 줄 요약
ROS2 기본은 Apache-2.0. 허용적(Permissive) vs 카피레프트(Copyleft)의 차이가 핵심.

---

## 허용적 라이선스 (Permissive) — ROS2에서 주로 사용

| 라이선스 | SPDX 식별자 | ROS2 사용처 | 핵심 조건 |
|---------|------------|------------|---------|
| **Apache 2.0** | `Apache-2.0` | ROS2 코어 전체 기본값 | 저작권 고지 유지 + 수정 시 변경 명시 + 특허권 보호 조항 포함 |
| **MIT** | `MIT` | 소규모 패키지 다수 | 저작권/라이선스 고지만 포함하면 끝 |
| **BSD 3-Clause** | `BSD-3-Clause` | rviz, 기존 패키지 다수 | MIT + "원작자 이름으로 홍보 금지" 조항 추가 |
| **BSD 2-Clause** | `BSD-2-Clause` | 일부 유틸리티 | BSD 3-Clause에서 홍보 금지 조항 제거 |
| **BSL 1.0** | `BSL-1.0` | Boost 라이브러리 계열 | MIT와 거의 동일, Boost 생태계에서 사용 |

---

## 카피레프트 라이선스 (Copyleft) — ROS2에서 드물게 사용

| 라이선스 | SPDX 식별자 | 핵심 조건 | ROS2 영향 |
|---------|------------|---------|---------|
| **LGPL 3.0** | `LGPL-3.0-only` | 동적 링크는 소스 공개 의무 없음, 정적 링크하면 소스 공개 필요 | 일부 하드웨어 드라이버 라이브러리 |
| **GPL 3.0** | `GPL-3.0-only` | 이 코드 사용/배포하면 전체 소스를 GPL로 공개해야 함 | ROS2 패키지에서 거의 안 씀 — 상업적 사용 제한 |
| **GPL 2.0** | `GPL-2.0-only` | GPL 3.0과 동일 원칙, v3와 호환 안 됨 | Linux 커널 관련 코드에서 등장 |

---

## 자유도 비교

```
자유도 높음 ←────────────────────────────→ 제약 많음

MIT ≈ BSD-2 < BSD-3 < Apache-2.0 < LGPL < GPL
 ↑                        ↑                 ↑
가장 단순           특허 보호 포함       소스 공개 강제
```

---

## Apache 2.0이 MIT보다 복잡한 이유

**특허 조항 포함:**
- 기여자가 자신의 특허를 사용자에게 자동 허가
- 사용자가 기여자에게 특허 소송 제기 시 라이선스 즉시 종료
- MIT에는 특허 관련 조항 없음
- 로봇/산업용 소프트웨어에서 Apache 2.0을 선호하는 이유

---

## package.xml 작성법

```xml
<license>Apache-2.0</license>      <!-- ROS2 신규 패키지 기본 -->
<license>MIT</license>
<license>BSD-3-Clause</license>
```

SPDX 식별자를 그대로 사용. `Apache License 2.0`처럼 풀네임도 가능하지만 SPDX 형식 권장.

---

## 검증

> 검증: Apache 2.0 조건 — [apache.org/licenses/LICENSE-2.0](https://www.apache.org/licenses/LICENSE-2.0) — 일치  
> 검증: MIT 조건 — [opensource.org/license/mit](https://opensource.org/license/mit) — 일치  
> 검증: BSD-3-Clause 조건 — [opensource.org/license/bsd-3-clause](https://opensource.org/license/bsd-3-clause) — 일치  
> 검증: ROS2 기본 Apache-2.0, rviz BSD — [ROS2 Developer Guide](https://docs.ros.org/en/humble/The-ROS2-Project/Contributing/Developer-Guide.html) — 일치  
> 미검증: GPL/LGPL 상세 조항 — GNU 사이트 접근 실패(429), SPDX 목록 기반
