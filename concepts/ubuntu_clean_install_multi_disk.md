# Ubuntu 다중 디스크 환경에서 완전 초기화 후 단독 설치

> 검증: `man wipefs`, `man sgdisk`, `man efibootmgr` — 일치
> 검증: Ubuntu 24.04 installer (Subiquity 기반) 설치 옵션 — "Erase disk and install Ubuntu"는 선택한 단일 디스크만 초기화

## 배경

NVMe SSD 2개가 장착된 노트북에서 기존 Ubuntu 22.04를 밀고 24.04를 새로 설치했는데, 재부팅하니 22.04로 부팅됨.

### 원인

Ubuntu 설치 마법사의 **"Erase disk and install Ubuntu"** 옵션은 이름과 달리 **선택한 디스크 한 개만** 초기화한다. PC에 디스크가 2개 있을 경우:

- 디스크 A (기존): Ubuntu 22.04 — 설치 시 건드리지 않으면 그대로 남음
- 디스크 B (새로 선택): Ubuntu 24.04 — 새로 설치

결과적으로 두 OS가 각각 다른 디스크에 공존하고, EFI 부트 매니저에는 두 개의 ubuntu 엔트리가 등록된다. `BootOrder`에서 우선순위가 높은 쪽으로 부팅된다.

### 상태 진단 커맨드

```bash
lsblk -f                # 디스크 목록 + 파티션 + 파일시스템
df -h /                 # 현재 / 가 어느 파티션인지
cat /etc/os-release     # 현재 부팅된 OS 버전
sudo efibootmgr -v      # EFI 부트 엔트리 목록 + BootOrder
```

`efibootmgr` 출력 예시:
```
Boot0003* ubuntu  HD(1,GPT,...)/File(\EFI\ubuntu\shimx64.efi)  ← 디스크1의 22.04
Boot0004* Ubuntu  HD(1,GPT,...)/File(\EFI\ubuntu\shimx64.efi)  ← 디스크2의 24.04
BootOrder: 0003,0004,...                                      ← 22.04가 우선
```

---

## 두 디스크 모두 밀고 단독 설치하기

### 핵심 아이디어

설치 USB 마법사만으로는 두 디스크 동시 초기화가 불가능하다. 따라서:

1. USB로 부팅 → **"Try Ubuntu"** 라이브 세션 진입
2. 터미널에서 두 디스크를 **수동으로** 완전 초기화
3. 기존 EFI 부트 엔트리 제거
4. 그 다음 설치 마법사 실행 → 한 디스크에 단독 설치

### 1단계 — USB 부팅 후 Try Ubuntu

재부팅 시 **F9** (Victus 부트 메뉴) → USB 선택 → GRUB에서 "Try or Install Ubuntu" → 첫 화면에서 **"Try Ubuntu"** (설치 버튼 누르지 말 것).

### 2단계 — 디스크 식별

```bash
lsblk
```

- `nvme0n1`, `nvme1n1`: 내장 SSD
- `sda` 또는 `sdb`: 부팅 중인 USB (절대 건드리지 말 것)

### 3단계 — 마운트 해제

```bash
sudo umount /dev/nvme0n1* 2>/dev/null
sudo umount /dev/nvme1n1* 2>/dev/null
```

| 토큰 | 의미 |
|------|------|
| `umount` | 마운트 해제. 마운트된 채로는 디스크를 수정할 수 없음 |
| `/dev/nvme0n1*` | nvme0n1의 모든 파티션을 와일드카드로 한꺼번에 |
| `2>/dev/null` | stderr를 버림. 마운트 안 돼있어도 에러 메시지 안 띄움 |

### 4단계 — 파티션 시그니처 제거 (`wipefs`)

```bash
sudo wipefs -a /dev/nvme0n1
sudo wipefs -a /dev/nvme1n1
```

| 토큰 | 의미 |
|------|------|
| `wipefs` | 파일시스템·파티션 테이블·RAID·LVM의 **매직 시그니처**를 지움 |
| `-a` | all. 발견되는 모든 시그니처 제거 |
| `/dev/nvme0n1` | 디스크 전체 (파티션 아님). `p1`, `p2`도 같이 무효화됨 |

시그니처만 지워도 OS는 "빈 디스크"로 인식한다. 단, GPT 헤더 자체는 디스크 끝에 백업본이 남아있을 수 있어서 다음 단계가 필요하다.

### 5단계 — GPT 헤더 완전 제거 (`sgdisk`)

```bash
sudo sgdisk --zap-all /dev/nvme0n1
sudo sgdisk --zap-all /dev/nvme1n1
```

| 토큰 | 의미 |
|------|------|
| `sgdisk` | GPT 파티션 테이블 편집기 |
| `--zap-all` | GPT 주 헤더 + 백업 헤더 + MBR 모두 제거. 디스크를 공장 초기 상태에 가깝게 만듦 |

`wipefs`만으로는 GPT 백업 헤더가 남을 수 있어서, 둘을 같이 쓰면 확실하다.

### 6단계 — 결과 확인

```bash
lsblk
```

`nvme0n1`, `nvme1n1`만 보이고 그 아래 `p1`, `p2` 같은 파티션이 사라져 있으면 성공.

### 7단계 — EFI 부트 엔트리 정리

```bash
sudo efibootmgr           # 현재 엔트리 확인
sudo efibootmgr -b 0003 -B
sudo efibootmgr -b 0004 -B
```

| 토큰 | 의미 |
|------|------|
| `efibootmgr` | UEFI 펌웨어의 부트 엔트리 관리 |
| `-b 0003` | 대상 엔트리 번호 지정 |
| `-B` | 해당 엔트리 삭제 (Big B = Bye) |

> **주의**: Windows Boot Manager (`Boot0000`) 같은 다른 OS 엔트리는 지우지 말 것. 디스크를 밀었으면 어차피 작동 안 하지만, 듀얼부팅 시나리오에서는 보존 필요.

### 8단계 — 설치 마법사 실행

바탕화면의 **"Install Ubuntu 24.04"** 더블클릭 → 저장소 선택 단계에서:

- 설치할 디스크 하나 선택 (예: `nvme0n1`)
- **"Erase disk and install Ubuntu"** 선택
- 나머지 디스크는 비어있는 채로 둠

설치 완료 후 부팅되면 빈 디스크는 GParted 등으로 ext4 포맷해서 데이터용으로 마운트:

```bash
sudo mkfs.ext4 /dev/nvme1n1
sudo mkdir /mnt/data
sudo mount /dev/nvme1n1 /mnt/data
# /etc/fstab에 등록하면 부팅 시 자동 마운트
```

---

## 커맨드 요약표

| 단계 | 명령 | 효과 |
|------|------|------|
| 확인 | `lsblk -f` | 파티션·파일시스템·마운트 상태 |
| 확인 | `df -h /` | 현재 루트가 어느 파티션 |
| 확인 | `cat /etc/os-release` | 현재 OS 버전 |
| 확인 | `sudo efibootmgr -v` | EFI 부트 엔트리 목록 |
| 해제 | `sudo umount /dev/nvmeXnY*` | 디스크 마운트 해제 |
| 초기화 | `sudo wipefs -a /dev/nvmeXnY` | 파일시스템 시그니처 제거 |
| 초기화 | `sudo sgdisk --zap-all /dev/nvmeXnY` | GPT 헤더(주+백업)+MBR 제거 |
| 정리 | `sudo efibootmgr -b XXXX -B` | EFI 엔트리 삭제 |

---

## 참고

- `man wipefs`, `man sgdisk`, `man efibootmgr`
- Ubuntu Installation Guide: https://help.ubuntu.com/community/Installation
- 관련 메모: [[ubuntu_dualboot_partition]] — 듀얼부팅 파티션 분할 시 발생하는 fdisk Value out of range 에러 사례
