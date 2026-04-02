# IBus 한글 전환 안 됨 (Ubuntu GNOME)

## 환경

| 항목 | 내용 |
|------|------|
| OS | Ubuntu 24.04 |
| DE | GNOME |
| IME | ibus-hangul 1.5.4 |

---

## 문제 상황

`ibus-hangul` 설치 및 GNOME 입력 소스에 한글 등록 완료 상태에서 `Alt_R` 키로 한/영 전환이 되지 않음.

---

## 원인

GNOME이 입력 소스 전환 이벤트를 먼저 처리하기 때문에 IBus 엔진의 `switch-keys` 설정(`Alt_R`)이 작동하지 않음. GNOME의 기본 입력 소스 전환 단축키는 `Super + Space`.

---

## 해결 방법

`Super + Space` 로 한/영 전환.

GNOME 설정에서 확인:
```
설정 → 키보드 → 입력 소스 전환: Super+Space
```

`Alt_R`도 함께 쓰고 싶은 경우:
```bash
gsettings set org.gnome.desktop.wm.keybindings switch-input-source "['<Super>space', '<Alt>Alt_R']"
```

---

## 참고

- IBus 엔진 전환키 확인: `dconf read /org/freedesktop/ibus/engine/hangul/switch-keys`
- GNOME 입력 소스 확인: `gsettings get org.gnome.desktop.input-sources sources`
