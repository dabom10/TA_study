# apt update vs apt upgrade

## 한 줄 요약

`update`는 패키지 목록 새로고침, `upgrade`는 실제 설치. 항상 세트로 사용.

---

## 차이

| 명령 | 동작 | 실제 설치 |
|------|------|-----------|
| `sudo apt update` | 저장소에서 최신 패키지 목록 다운로드 | 없음 |
| `sudo apt upgrade` | 설치된 패키지를 최신 버전으로 업그레이드 | 있음 |
| `sudo apt full-upgrade` | upgrade + 필요시 기존 패키지 제거도 허용 | 있음 |

---

## 세트로 쓰는 이유

```bash
sudo apt update && sudo apt upgrade
```

`update` 없이 `upgrade`만 하면 apt가 가진 오래된 목록 기준으로 업그레이드 → 최신 버전을 놓침.

---

## full-upgrade 주의

```bash
sudo apt full-upgrade   # 쓸 때 주의
```

기존 패키지를 제거하면서까지 업그레이드 진행. ROS2 환경에서는 의존성이 꼬일 수 있어 함부로 쓰지 않는 게 좋음.

---

## 참고

> 검증: [Ubuntu 공식 man page (jammy)](https://manpages.ubuntu.com/manpages/jammy/man8/apt.8.html) — 확인
