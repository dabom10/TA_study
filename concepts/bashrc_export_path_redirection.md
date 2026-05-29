# `.bashrc`에 PATH 추가 + 리다이렉션 원리

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

이 한 줄에 들어있는 셸 개념들 — 따옴표, append 리다이렉션, `export`, `PATH` 우선순위 — 정리.

## 한 줄 요약

`echo`로 만든 문자열을 `>>`로 `.bashrc` 끝에 덧붙여서, **새 셸이 시작될 때마다** `~/.local/bin`을 PATH 앞에 추가하도록 영구 설정한다.

## 명령어 분해

### 1. `echo '...'`
작은따옴표 안의 문자열을 표준출력으로 보낸다. **작은따옴표는 변수 펼치기를 막는다** — `$HOME`, `$PATH`가 지금 값으로 치환되지 않고 글자 그대로 남는다.

### 2. `>> ~/.bashrc`
- `>` : 덮어쓰기
- `>>` : 파일 끝에 **append**
- `~/.bashrc` : 홈 디렉토리의 bash 설정 파일

### 3. 추가되는 줄
```bash
export PATH="$HOME/.local/bin:$PATH"
```
- `export` : 자식 프로세스도 볼 수 있는 환경변수로 등록
- `PATH` : 셸이 실행 파일을 찾는 디렉토리 목록 (`:` 구분)
- `$HOME/.local/bin:$PATH` : 기존 PATH **앞에** 끼움 → 같은 이름의 실행파일이 있을 때 `~/.local/bin` 쪽이 우선

## 작은따옴표 vs 큰따옴표 (핵심)

| 형태 | 결과 |
|---|---|
| 작은따옴표 `'...$HOME...'` | `.bashrc`에 `$HOME` 글자 그대로 저장 → 매번 셸 시작 시 평가됨 ✅ |
| 큰따옴표 `"...$HOME..."` | 지금 시점의 값으로 치환되어 박힘 → 사용자/환경 바뀌면 깨짐 ❌ |

## 출력 동작

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```
→ **터미널에 아무것도 안 찍힌다.** `>>`가 stdout을 파일로 돌리기 때문. 정상 동작이면 무음.

확인:
```bash
tail -n 3 ~/.bashrc
```

## 적용 시점
`.bashrc`는 새 인터랙티브 셸이 시작될 때만 읽힌다. 현재 셸에 즉시 반영하려면:
```bash
source ~/.bashrc
```

## `echo` 없이 그냥 리다이렉션은 되는가?

**안 된다.** `>>`는 "어떤 명령의 출력을 파일로 보내라"는 뜻이라 **출력 소스가 필요**하다.

```bash
'export PATH=...' >> ~/.bashrc
# bash: export PATH=...: command not found
# → 작은따옴표 안 문자열을 명령어로 실행하려 함
```

### 대안

| 방법 | 명령 |
|---|---|
| Here-string (bash) | `cat <<< 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc` |
| Here-doc (여러 줄) | `cat << 'EOF' >> ~/.bashrc` ... `EOF` (작은따옴표 `'EOF'`로 변수 펼침 차단) |
| `printf` (이식성) | `printf '%s\n' 'export PATH=...' >> ~/.bashrc` |
| 에디터 직접 | `nano ~/.bashrc` |

## 주의사항

- 두 번 실행하면 같은 줄이 두 번 들어간다. 확인 후 추가:
  ```bash
  grep -q '.local/bin' ~/.bashrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  ```
- `~/.local/bin`은 `pip install --user`, `pipx`, 일부 `cargo`/`go` 도구가 설치되는 경로
- ROS 2 환경에서는 `source /opt/ros/<distro>/setup.bash`도 같은 방식으로 `.bashrc`에 들어가 있음

## 다른 섹션과의 연결
- [[ros2_workspace_and_package]] — `source install/setup.bash`와 PATH/환경변수 개념
- [[virtual_environment_concepts]] — venv 활성화 시 PATH 조작

## 참고 링크
- Bash Reference Manual (Redirections): https://www.gnu.org/software/bash/manual/html_node/Redirections.html
- Bash Reference Manual (Quoting): https://www.gnu.org/software/bash/manual/html_node/Quoting.html
