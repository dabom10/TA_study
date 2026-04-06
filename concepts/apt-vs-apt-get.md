# apt vs apt-get 차이

## 요약

| 항목 | `apt` | `apt-get` |
|------|-------|-----------|
| 출시 | 2014년 (신) | 구버전 |
| 대상 | 사람이 직접 사용 | 스크립트/자동화 |
| 진행률 바 | ✅ | ❌ |
| 컬러 출력 | ✅ | ❌ |
| 출력 안정성 | 버전마다 바뀔 수 있음 | 일정하게 유지됨 |

## 상세

`apt`는 `apt-get` + `apt-cache` 등 여러 명령어를 합친 **사용자 친화적 버전**이다.
기능 자체(패키지 목록 업데이트 등)는 동일하며, 둘 다 `/etc/apt/sources.list`를 참조한다.

## 언제 뭘 써야 하나

- **터미널에서 직접 입력할 때** → `apt`
- **Dockerfile, 쉘 스크립트, CI/CD 파이프라인** → `apt-get`
  - 출력 형식이 안정적으로 유지되어 파싱 신뢰성이 높음

## 예시

```bash
# 터미널에서 직접
sudo apt update
sudo apt install ros-humble-desktop

# Dockerfile 안에서
RUN apt-get update && apt-get install -y ros-humble-desktop
```