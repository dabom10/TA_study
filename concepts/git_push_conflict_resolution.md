# Git Push 충돌 해결

## 한 줄 요약

`git push` 거부 시 원격 변경사항을 로컬에 먼저 합친 뒤 다시 push한다.

---

## 기본 개념

### non-fast-forward란

Git push는 **원격이 로컬의 연장선일 때만** 허용된다.

```
원격:  A → B → C          ← 내가 모르는 C가 생김
로컬:  A → B → D          ← 내가 만든 D
```

이 상태에서 push하면 C가 삭제된다. Git이 C를 먼저 가져오라며 거부하는 것이 non-fast-forward 에러.

---

### fetch / merge / pull

**fetch**: 원격 변경사항을 다운로드만 함. 내 작업 브랜치에는 합치지 않음.

```bash
git fetch origin
# origin/main 에 원격 커밋이 내려오지만, 내 main 은 그대로
```

**merge**: 두 갈래를 하나로 합침. merge 커밋이 새로 생긴다.

```
원격: A → B → C
로컬: A → B → D
merge 후: A → B → C → (merge 커밋)
                ↗
               D
```

**pull**: `fetch + merge` 단축 명령.

```bash
git pull origin main   # = git fetch origin + git merge origin/main
```

---

### rebase

내 커밋을 원격 커밋 위에 다시 쌓는 방식. merge 커밋 없이 일직선 히스토리가 된다.

```
원격: A → B → C
로컬: A → B → D

rebase 후: A → B → C → D'   ← D를 C 위에 다시 붙임
```

```bash
git pull --rebase origin main
```

---

### 충돌 마커 `<<<<<<< / ======= / >>>>>>>`

같은 줄을 양쪽이 다르게 수정하면 Git이 자동 합치기에 실패하고 파일에 마커를 삽입한다.

```
<<<<<<< HEAD          ← 내 버전 (로컬)
로봇 이름: TurtleBot
=======               ← 구분선
로봇 이름: Doosan
>>>>>>> origin/main   ← 원격 버전
```

마커 3줄을 포함해 원하는 내용만 남기고 저장하면 충돌 해결.

---

### `git commit` vs `git rebase --continue`

| 상황 | 명령 | 이유 |
|------|------|------|
| `git pull` (merge 방식) | `git add` → `git commit` | merge 완료를 새 커밋으로 확정 |
| `git pull --rebase` (rebase 방식) | `git add` → `git rebase --continue` | rebase가 커밋을 하나씩 처리 중이므로 "다음 커밋으로 계속" |

rebase 중에 `git commit`을 하면 rebase 흐름 밖에 커밋이 생겨버리므로 반드시 `--continue` 사용.

---

## 왜 충돌이 나는가

```
! [rejected] main -> main (non-fast-forward)
error: failed to push some refs to 'https://github.com/...'
hint: Updates were rejected because the remote contains work that you do
hint: not have locally.
```

원격 브랜치에 내 로컬에 없는 커밋이 생겼을 때 발생한다.  
Git은 덮어쓰기를 막기 위해 push를 거부한다.

---

## 상황별 해결 흐름

### 상황 1: 나 혼자 쓰는 브랜치, 단순 업데이트 차이

```bash
git pull origin main        # fetch + merge
git push origin main
```

`git pull`은 내부적으로 `git fetch` + `git merge`를 순서대로 실행한다.  
merge 커밋이 생기지만, 충돌이 없으면 자동으로 완료된다.

---

### 상황 2: 히스토리를 깔끔하게 유지하고 싶을 때 (rebase)

```bash
git pull --rebase origin main   # fetch 후 내 커밋을 원격 커밋 위에 재배치
git push origin main
```

merge 커밋 없이 선형 히스토리를 유지할 수 있다.  
팀 프로젝트에서 PR 전에 많이 쓴다.

---

### 상황 3: 충돌 파일이 생겼을 때 (merge 방식)

```bash
git pull origin main
# 충돌 발생 → CONFLICT (content): Merge conflict in <파일명>
```

1. 충돌 파일 열기 — Git이 표시한 마커 확인

```
<<<<<<< HEAD
내 변경 내용
=======
원격의 변경 내용
>>>>>>> origin/main
```

2. 원하는 내용으로 편집 (마커 `<<<<<<<`, `=======`, `>>>>>>>` 모두 삭제)

3. 해결된 파일 스테이징

```bash
git add <파일명>
```

4. merge 커밋 생성

```bash
git commit
```

5. push

```bash
git push origin main
```

---

### 상황 4: 충돌 파일이 생겼을 때 (rebase 방식)

```bash
git pull --rebase origin main
# 충돌 발생 → CONFLICT (content): ...
```

1. 충돌 파일 편집 (마커 제거 후 원하는 내용으로 수정)

2. 스테이징 (`git commit` 대신 `--continue` 사용)

```bash
git add <파일명>
git rebase --continue
```

3. 충돌이 여러 커밋에 걸쳐 있으면 위 과정 반복

4. push

```bash
git push origin main
```

---

### 상황 5: 내 로컬 커밋을 버리고 원격 기준으로 맞추고 싶을 때

```bash
git fetch origin
git reset --hard origin/main   # ⚠️ 로컬 커밋 삭제됨, 신중하게 사용
```

---

### 상황 6: 내 브랜치 히스토리를 강제로 덮어써야 할 때

> 혼자 쓰는 feature 브랜치에서만 사용. main/master에 force push 금지.

```bash
git push --force-with-lease origin <브랜치명>
```

`--force`와 달리 `--force-with-lease`는 내가 모르는 원격 커밋이 있으면 push를 거부한다.  
더 안전한 강제 push 방법이다.

---

## 충돌 해결 중 취소하는 법

| 상황 | 명령어 |
|------|--------|
| merge 중단 | `git merge --abort` |
| rebase 중단 | `git rebase --abort` |

실행하면 pull 이전 상태로 돌아간다.

---

## 요약 흐름도

```
git push 거부
    │
    ├─ 충돌 없음 ──► git pull → git push
    │
    └─ 충돌 있음
           │
           ├─ merge 방식: 파일 편집 → git add → git commit → git push
           │
           └─ rebase 방식: 파일 편집 → git add → git rebase --continue → git push
```

---

> 검증: [GitHub Docs - Resolving merge conflicts after a Git rebase](https://docs.github.com/en/get-started/using-git/resolving-merge-conflicts-after-a-git-rebase) — 일치  
> 검증: [GitHub Docs - Resolving a merge conflict using the command line](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/resolving-a-merge-conflict-using-the-command-line) — 일치  
> 검증: [Atlassian Git Tutorial - Merge Conflicts](https://www.atlassian.com/git/tutorials/using-branches/merge-conflicts) — 일치
