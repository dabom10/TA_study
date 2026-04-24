# sd_flash.sh dcfldd 없음 + dpkg 깨짐

## 환경

- OS: Ubuntu 22.04 (HWE 커널 6.8.0-107)
- 작업: TurtleBot4 SD 카드 플래싱 (`turtlebot4_standard_humble_1.0.4.img`)
- 스크립트: `sd_flash.sh` (Clearpath 공식 제공)

## 문제 상황

`sd_flash.sh` 실행 시 `dcfldd` 명령이 없어 플래싱 중단.

```
sudo: dcfldd: 명령이 없습니다
```

`sudo apt install dcfldd` 시도 → dpkg 깨진 상태로 설치 불가.

```
E: dpkg가 중단되었습니다. 수동으로 'sudo dpkg --configure -a' 명령을 실행해 문제점을 바로잡으십시오.
```

## 원인

**4월 22일 `apt upgrade` 도중 강제종료 또는 네트워크 끊김으로 중단.**

`/var/log/dpkg.log` 기준 타임라인:

| 시각 | 상태 |
|------|------|
| 04-22 09:21:42 | `linux-headers-6.8.0-110-generic` 설치 시작 → half-installed |
| 04-22 09:40:25 | `linux-hwe-6.8-headers-6.8.0-110` unpack 완료, headers 재개 → **이후 기록 없음 (중단)** |
| 04-24 오늘 | 처음으로 dpkg 활동 재개 |

결과적으로 `linux-headers-6.8.0-110-generic`이 control file(list, md5sums)이 없는 손상 상태로 남음.

**현재 패키지 상태 (`dpkg -l`):**

```
iHR  linux-headers-6.8.0-110-generic   → 손상 (control file 없음)
iU   linux-generic-hwe-22.04           → unpack됐지만 configure 불가 (headers 손상 때문)
ii   linux-headers-generic-hwe-22.04   → 107 설치됨 (110은 후보만)
```

> 검증: `dpkg --audit` 직접 실행 — list/md5sums control file 없음 확인
> 검증: `/var/log/dpkg.log` 직접 확인 — 04-22 중단 시점 특정
> 검증: `apt-cache policy linux-headers-generic-hwe-22.04` — 설치 107, 후보 110 확인

## 진단 순서

1. `sd_flash.sh` 실행 → `dcfldd: 명령이 없습니다`
2. `sudo apt install dcfldd` → dpkg 깨짐 에러
3. `sudo dpkg --configure -a` → 커널 헤더 버전 불일치로 configure 실패
4. `dpkg --audit` → `linux-headers-6.8.0-110-generic` 손상 확인
5. `dpkg -l | grep "linux-" | grep -v "^ii"` → iHR/iU 패키지 특정
6. `tail -50 /var/log/dpkg.log` → 04-22 중단 시점 확인
7. `apt-cache policy linux-headers-generic-hwe-22.04` → 버전 불일치 확인

## 해결 방법

> 미해결 — dpkg 수복 방향 확인 중

**우회 (dpkg 건드리지 않고 SD 플래싱만):**
```bash
lsblk  # /dev/sda가 SD카드인지 먼저 확인
sudo dd if=turtlebot4_standard_humble_1.0.4.img of=/dev/sda bs=4M status=progress && sync
```

> 검증: `dd --help` 직접 실행 — `if=`, `of=`, `bs=`, `status=` 옵션 확인

**dpkg 수복 방향 (미실행):**

손상된 패키지를 재설치해 중단된 업그레이드를 완성하는 방법.
새 의존성 추가가 아니라 이미 시도했던 설치를 완성하는 것.

```bash
sudo apt install --reinstall linux-headers-6.8.0-110-generic
sudo dpkg --configure -a
```

## 참고

- `dcfldd`는 `dd`에 진행률/해시 기능을 추가한 도구 — SD 플래싱 목적으로는 `dd`로 대체 가능
- iHR 상태: installed(i), Half-installed(H), Reinst-required(R) — 재설치가 필요한 손상 상태
