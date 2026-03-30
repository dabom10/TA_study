# NVIDIA 드라이버 설치 후 HDMI 외장 모니터 블랙스크린 문제

## 환경

| 항목 | 내용 |
|------|------|
| 노트북 | MSI Pulse 16 AI |
| CPU | Intel Core Ultra 9 185H |
| GPU | NVIDIA GeForce RTX 4070 (노트북) |
| OS | Ubuntu (Wayland 세션) |
| 드라이버 | nvidia-driver-575 → 설치 후 580.126.09 확인 |

---

## 문제 상황

NVIDIA 드라이버 설치 후 HDMI로 연결된 외장 모니터에 **검은 화면(블랙스크린)** 이 출력됨.

- 노트북 내장 디스플레이: 정상 출력
- 외장 모니터: 전원은 켜지고 마우스 커서 이동은 되나 화면이 검게 보임
- `xrandr --query` 결과상 모니터는 `connected` 상태로 정상 인식됨

---

## 원인

**Wayland + NVIDIA 드라이버 조합 충돌**

Ubuntu 기본 세션은 **Wayland**를 사용하는데, NVIDIA 드라이버를 새로 설치하면 Wayland 환경에서 외부 모니터 렌더링이 제대로 동작하지 않는 경우가 있음.

`xrandr` 출력에서 디스플레이가 `XWAYLAND1`, `XWAYLAND7` 형태로 표시된 것이 Wayland 세션임을 나타냄.

---

## 진단 순서

### 1. dpkg 상태 복구 (apt 에러 발생 시)

드라이버 설치 도중 중단되어 아래 에러가 발생한 경우:

```
E: dpkg was interrupted, you must manually run 'sudo dpkg --configure -a' to correct the problem.
```

아래 명령어로 복구 후 재설치:

```bash
sudo dpkg --configure -a
sudo apt install nvidia-driver-575
```

### 2. GPU 및 드라이버 상태 확인

```bash
nvidia-smi
```

드라이버 버전, GPU 인식 여부, VRAM 상태 등을 확인.

### 3. 디스플레이 인식 상태 확인

```bash
xrandr --query
```

외장 모니터가 `connected`로 표시되는지 확인. 인식은 되나 블랙스크린이면 다음 단계로.

---

## 해결 방법

### Wayland 비활성화 → X11 세션으로 전환

```bash
sudo nano /etc/gdm3/custom.conf
```

파일 내에서 아래 줄을 찾아 주석(`#`) 제거:

```ini
# 변경 전
#WaylandEnable=false

# 변경 후
WaylandEnable=false
```

저장 후 재부팅:

```bash
sudo reboot
```

재부팅 후 X11 세션으로 전환되며 외장 모니터 정상 출력됨.

---

## 참고

- RTX 4070 노트북은 Intel iGPU + NVIDIA dGPU **하이브리드 구조**로, HDMI 포트가 NVIDIA dGPU에 직결되어 있어 드라이버 변경 시 외부 출력에 영향을 받을 수 있음.
- Wayland의 NVIDIA 지원은 지속적으로 개선 중이나, 안정성이 필요한 환경에서는 X11 사용을 권장.
