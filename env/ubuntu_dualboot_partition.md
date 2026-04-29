# Ubuntu 듀얼부팅 파티션 설정

## 환경

- 디스크: NVMe SSD (~953 GiB)
- 기존 파티션: EFI(512M) + Linux filesystem (전체 용량 점유)
- 목표: Ubuntu 24.04 LTS 추가 설치

## 문제 상황

`sudo fdisk /dev/nvme0n1`에서 파티션 3 추가 시도 → `Value out of range` 에러

```
Last sector, +/-sectors or +/-size{K,M,G,T,P} (34-2047, default 2047): +100G
Value out of range.
```

## 원인

디스크 전체가 기존 파티션에 할당되어 있어 여유 공간 없음.
fdisk가 제안한 범위 `34-2047`은 파티션 1 앞의 ~1MB 빈 공간(실제 사용 불가).

```
/dev/nvme0n1p1    2048    1050623    1048576   512M EFI System
/dev/nvme0n1p2 1050624 2000408575 1999357952 953.4G Linux filesystem
```

## 진단 순서

1. `sudo fdisk -l /dev/nvme0n1`로 파티션 레이아웃 확인
2. unallocated 공간 유무 확인 (`F` 명령어 또는 GParted)
3. 여유 공간 없으면 기존 파티션 축소 필요

## 해결 방법

### 방법 1: Ubuntu 설치러 자동 처리 (권장)

Ubuntu 24.04 부팅 USB로 부팅 → 설치 유형 선택 화면에서 **"Install Ubuntu alongside ..."** 선택.
슬라이더로 각 OS 용량 조정 → 설치러가 파티션 축소·생성·GRUB 설정까지 자동 처리.

### 방법 2: GParted 수동 처리

라이브 USB 환경에서:
1. GParted 실행 → `/dev/nvme0n1p2` 우클릭 → Resize/Move
2. 원하는 만큼 축소 후 Apply
3. 생긴 unallocated 공간에 새 파티션 생성

### 방법 3: CLI (parted + resize2fs)

```bash
sudo e2fsck -f /dev/nvme0n1p2        # 파일시스템 체크 (필수)
sudo resize2fs /dev/nvme0n1p2 853G   # 파일시스템 축소
sudo parted /dev/nvme0n1
  resizepart 2 900GB                 # 파티션 경계 축소
  quit
sudo fdisk /dev/nvme0n1              # 새 파티션 생성
```

### 주의사항

- `fdisk`는 파티션 축소 불가 (삭제/재생성만 가능)
- **현재 부팅 중인 파티션은 온라인 축소 불가** → 반드시 라이브 USB 환경에서 작업
- 교체 설치라면 "Erase disk and install Ubuntu" 선택으로 파티션 불필요

## 파티션을 나누는 이유

| 목적 | 설명 |
|------|------|
| 듀얼부팅 | OS마다 독립된 영역 필요 |
| `/home` 분리 | OS 재설치 시 사용자 데이터 보존 |
| `swap` 분리 | 메모리 부족 시 사용하는 가상 메모리 공간 |

단순히 Ubuntu 하나만 쓸 거라면 파티션 분리 없이 "Erase disk and install" 가능.

## 참고

> 검증: 사용자 제공 fdisk 출력 — 디스크 레이아웃 직접 확인
