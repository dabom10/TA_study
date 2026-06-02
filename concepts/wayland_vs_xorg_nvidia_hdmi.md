# Wayland vs Xorg + NVIDIA 하이브리드 노트북 외부 모니터(HDMI) 이슈

## 한 줄 요약
Xorg와 Wayland는 디스플레이 서버 아키텍처가 다르며, NVIDIA Optimus 노트북에서 **dGPU에 직결된 HDMI 출력**은 Xorg(PRIME)에서는 잘 뜨지만 Wayland에서는 NVIDIA 드라이버의 멀티 GPU 지원 미비로 안 뜨는 경우가 많다. GDM 로그인 화면에 어떤 세션이 뜨는지는 NVIDIA 드라이버 설치/버전에 따라 udev 규칙(`61-gdm.rules`)이 자동으로 정한다.

> 검증: `/usr/lib/udev/rules.d/61-gdm.rules` (로컬, Ubuntu 24.04 GDM) — 일치
> 검증: `lspci -k`, `/sys/class/drm/card*` (로컬) — HDMI-A-2 커넥터가 NVIDIA dGPU(card0, 0000:01:00.0)에 직결 확인
> 검증: NVIDIA Developer Forums / GNOME mutter issue #1891 — Optimus + Wayland 외부 모니터 미동작 알려진 이슈, 일치

---

## 1. Xorg vs Wayland 개념 차이

| 항목 | Xorg (X11) | Wayland |
|------|-----------|---------|
| 구조 | X 서버라는 **중앙 프로세스**가 모든 클라이언트의 그리기 요청을 중계. 합성기(compositor)는 별도 | **compositor가 곧 디스플레이 서버**. 클라이언트가 자기 버퍼를 직접 그려 compositor에 전달 |
| 등장 | 1984년 X11, 레거시 누적 | 2008년~, X11을 대체하려는 현대적 설계 |
| 보안 | 모든 클라이언트가 다른 창의 입력/화면을 엿볼 수 있음(키로깅 등) | 클라이언트 간 격리. 스크린샷/화면공유는 별도 portal 필요 |
| 멀티 GPU / 하이브리드 | PRIME offload·reverse PRIME으로 성숙 | mutter+NVIDIA 조합에서 dGPU 출력 처리에 결함이 많았음 |
| NVIDIA 독점 드라이버 | 오래 안정적 | 470 이전엔 사실상 불가, 이후 개선 중이나 Optimus 외부출력 등 미흡 |

핵심: **X11은 "서버가 중계", Wayland는 "compositor가 직접 합성"**. Wayland가 더 단순·안전하지만, NVIDIA 독점 드라이버의 하이브리드 지원이 늦어 노트북에서 문제가 잦았다.

---

## 2. "드라이버 설치하면 Xorg 로그인 권한이 생긴다"는 오해 정리

권한(permission) 개념이 아니다. 두 개의 **독립된 메커니즘**이 합쳐진 결과다.

### (A) GDM 로그인 화면에 뜨는 세션 선택지 — `61-gdm.rules` udev 규칙이 결정
부팅 시 NVIDIA 커널 모듈이 로드되면 udev가 이를 감지해 GDM 동작을 자동 변경한다. 검증한 규칙 요약:

- **드라이버 470 미만** → `WaylandEnable false`로 **Wayland 완전 비활성화** (Xorg만 남음)
- **드라이버 470 이상**(현재 이 PC는 580) → `PreferredDisplayServer xorg`, 즉 **Xorg를 기본/우선**으로 두되 Wayland도 선택 가능
- **`nvidia_drm modeset != Y`** → Wayland 비활성화
- **nomodeset 커널 파라미터** → Wayland 비활성화
- 특정 Dell SKU 등 일부 기종만 예외적으로 `GDM_PREFER_WAYLAND`

즉 "Xorg로 로그인 못 하다가 뭔가 설치 후 reboot하니 됐다"는 것은 → **NVIDIA 독점 드라이버를 설치/활성화**하면서 (1) udev 규칙이 Xorg 세션을 우선/노출시키고, (2) 그제서야 X 서버가 dGPU를 제대로 구동해 세션이 정상 시작된 것으로 해석된다. (nouveau/드라이버 미설치 상태에서는 Xorg 세션이 검은 화면·크래시로 사실상 로그인 불가였을 가능성)

> 미검증: 설치 직전의 정확한 과거 상태(어떤 드라이버였는지)는 재현 불가 — 위는 규칙 기반 추론

#### 중요: Xorg도 Wayland도 GPU 드라이버가 설치하는 게 아니다
드라이버 설치 전에도 **둘 다 이미 깔려 있다.** 두 세션 모두 우분투 데스크탑 기본 패키지에서 제공된다(드라이버 무관). 로컬 확인:

```
ubuntu-session  →  /usr/share/xsessions/ubuntu-xorg.desktop      (Xorg 세션)
ubuntu-session  →  /usr/share/wayland-sessions/ubuntu.desktop    (Wayland 세션)
gnome-shell / mutter (Wayland compositor) → 기본 설치, nvidia 의존성 없음
xserver-xorg-core → 기본 설치 (X 서버 본체)
```

- **Wayland**: 별도 설치·설정 대상이 아님. mutter(gnome-shell)에 내장되어 기본 설치되며, Ubuntu 21.04+에서 지원 하드웨어 기본 세션. 로그인 화면 톱니 ⚙ → "Ubuntu"(on Xorg 아닌 것) 선택.
- **NVIDIA 드라이버가 추가하는 것**: Xorg 본체가 아니라 **Xorg에 꽂히는 비디오 모듈** `xserver-xorg-video-nvidia-580` 하나뿐. 이미 있던 `xserver-xorg-core`에 플러그인으로 붙는다.

→ 따라서 "드라이버 깔고 Xorg 로그인이 됐다"는 Xorg 신규 설치가 아니라, (1) NVIDIA 비디오 모듈로 X 서버가 dGPU를 구동 가능해지고 (2) udev 규칙이 Xorg를 기본으로 올린 결과다.

> 검증: `dpkg -S`, `dpkg -l mutter/gnome-shell`, `apt-cache rdepends xserver-xorg-core` (로컬) — 일치

### (B) 외부 HDMI 모니터가 뜨는가 — HDMI 포트가 물리적으로 어느 GPU에 붙어 있는지 + 디스플레이 서버의 멀티 GPU 지원
이 PC(MSI Meteor Lake + RTX 4070 Laptop) 확인 결과:

```
card0: PCI=0000:01:00.0 driver=nvidia   ← HDMI-A-2 커넥터가 여기 직결
card1: PCI=0000:00:02.0 driver=i915      ← Intel Arc iGPU, HDMI-A-1
```

HDMI 출력이 **NVIDIA dGPU에 직결**되어 있으므로, 외부 모니터를 켜려면 NVIDIA 경로가 화면을 합성해 그 포트로 스캔아웃해야 한다.

- **Xorg**: PRIME(`xrandr --listproviders`에 NVIDIA-0 Source Output + modesetting Sink/Offload)으로 dGPU 출력이 잘 처리됨 → HDMI 정상.
- **Wayland**: mutter+NVIDIA 조합에서 dGPU에 붙은 외부 출력이 감지되어도 검은 화면이거나 아예 안 뜨는 알려진 버그. → 이래서 Wayland 로그인 시 HDMI가 안 떴던 것.

---

## 3. 정리: 사용자의 두 관찰에 대한 답

1. **"Xorg 로그인이 처음엔 안 됐는데 뭔가 설치 + reboot 후 됐다"**
   → NVIDIA 독점 드라이버 설치가 트리거. `61-gdm.rules`가 드라이버 감지 후 Xorg를 우선 노출하고, X 서버가 dGPU를 정상 구동하게 됨. **GPU 드라이버 설치 여부가 GDM 세션 선택지에 영향을 주는 것은 맞다**(단 "권한"이 아니라 udev 자동 설정).

2. **"Xorg에선 HDMI 외부 모니터가 뜨고 Wayland에선 안 떴다"**
   → HDMI 포트가 NVIDIA dGPU 직결이고, NVIDIA Optimus + Wayland의 외부 출력 미동작은 잘 알려진 이슈. Xorg(PRIME)에서만 정상.

### 확인용 명령어
```bash
echo $XDG_SESSION_TYPE                     # 현재 세션이 x11 / wayland
lspci -k | grep -A3 -iE "vga|3d"           # GPU와 사용 드라이버
for h in /sys/class/drm/card*-HDMI*; do echo $h; done   # HDMI 커넥터 소속 card
xrandr --listproviders                     # (Xorg) PRIME provider
cat /sys/module/nvidia_drm/parameters/modeset   # Y면 KMS 활성
```

---

## 다른 개념과의 연결
- GPU/드라이버 계층: [[cpu_core_gpu_concepts]]
- Ubuntu 버전별 환경 차이 맥락: [[humble_vs_jazzy_python_env]]

## 의문점 / 나중에 파고들 것
- Wayland에서 dGPU HDMI를 강제로 띄우는 방법(`__GLX_VENDOR_LIBRARY_NAME`, nvidia-drm modeset, kernel 파라미터)이 최신 드라이버 580대에서 개선됐는지
- 이 노트북의 MUX 스위치(Advanced Optimus / dGPU-only 모드) 유무에 따른 동작 차이

## 출처
- 로컬: `/usr/lib/udev/rules.d/61-gdm.rules`, `lspci -k`, `/sys/class/drm/`
- https://gitlab.gnome.org/GNOME/mutter/-/issues/1891
- https://forums.developer.nvidia.com/t/external-monitor-doesnt-work-on-wayland/214090
- https://bbs.archlinux.org/viewtopic.php?id=285920
