# Claude Code 활용 패턴 기록

## 한 줄 요약
Claude Code(CLI)로 실제 작업하며 익힌 사용 패턴 — 해커톤 가이드 기반, 실습 사례 포함

## 핵심 개념

### 작업 디렉토리 고정
Claude Code는 **실행 시점의 디렉토리**가 고정된다.
채팅 안에서 `cd` 입력은 다음 명령에 적용되지 않는다 (각 bash 호출이 독립 세션).
```bash
# 올바른 방법: 먼저 이동 후 실행
cd ~/howtouse_claude
claude
```

### /init — 세션 시작 필수 의식
프로젝트 폴더에서 `claude` 실행 후 `/init` 치면 CLAUDE.md 자동 생성.
Claude가 매 세션마다 이 파일을 읽어 프로젝트 맥락을 파악한다.
- CLAUDE.md는 **50~100줄** 적당. 너무 길면 핵심 규칙을 무시함.
- "이 규칙을 빼면 Claude가 실수하는가?" 기준으로 내용 선별.

### /clear — 작업 전환 시 필수
주제가 바뀔 때 반드시 실행. 오염된 컨텍스트는 버그의 원인.
→ "하나의 세션 = 하나의 작업"

### Plan Mode vs Accept Edits On
| | Plan Mode (Shift+Tab) | Accept Edits On |
|---|---|---|
| 역할 | 설계/분석만, 코드 수정 없음 | 파일 편집 자동 승인 |
| 용도 | 복잡한 기능 구현 전 설계 | 매번 뜨는 승인 프롬프트 생략 |
| 순서 | Plan Mode로 설계 → 끄고 구현 | 빠른 구현 단계에서 켜둠 |

### /compact — 컨텍스트 70%에서 수동 실행
95%까지 기다리면 자동 압축 → 중요 정보 손실 가능.
`/status`로 수시 확인.

---

## 서브에이전트 패턴 (Physical AI 해커톤 기준)

| 패턴 | 난이도 | 핵심 | 프롬프트 핵심 |
|------|--------|------|--------------|
| Safety Checker | ★☆☆ | 위험 명령 거부 | 안전 규칙 목록 → status: refused |
| Conversation | ★☆☆ | 질문에 자연어 응답 | not_command일 때 안내 메시지 |
| Multi-step Planner | ★★☆ | 복합 명령 단계 분해 | steps 배열 반환, 순차 실행 |
| Feedback Agent | ★★☆ | 완료 후 결과 보고 | 완료 알림 → 메시지 생성 |
| Memory Agent | ★★☆ | 이전 명령 기억/재실행 | 대화 히스토리 → context 포함 |
| Inventory Tracker | ★★★ | 현재 상태 추적 | state_db dict 관리 |

**핵심 원칙:** 코드 구조는 동일, LLM 프롬프트 안 도메인 단어만 바꾸면 어떤 로봇에도 적용.

---

## API 비용 최적화 핵심

- **Mock 모드 먼저 개발** — API 키 없어도 전체 흐름 테스트 가능
- `max_tokens=300` — JSON 응답은 100~200 토큰이면 충분, 기본값(8192) 두면 낭비
- `response_mime_type: application/json` — JSON만 강제, 텍스트 섞임 방지
- few-shot 예시는 3개만 — 5개 이상은 오히려 과적합
- Gemini 2.5 Flash 무료 티어: 250건/일, 10건/분

---

## 실습 사례: 자연어 TurtleBot4 네비게이터 (2026-05-18)

**프로젝트 위치:** `~/howtouse_claude/`

**구조:**
```
llm_parser.py        ← 자연어 → JSON goal (Safety Checker + Mock/Gemini)
natural_navigator.py ← ROS2 노드, nav2_simple_commander 기반
```

**적용한 패턴:**
- Safety Checker: `UNSAFE_KEYWORDS` 목록 → `{"status": "refused"}`
- Conversation: 인식 불가 입력 → `{"status": "not_command", "message": ...}`
- Mock 우선 개발: `GEMINI_API_KEY` 없으면 키워드 매칭으로 자동 폴백

**Multi-step Planner 설계 중** (Plan Mode 활용):
- `steps: [{x, y, yaw, label}, ...]` 배열로 JSON 스키마 확장
- `natural_navigator.py`에서 steps 있으면 순회, 없으면 단일 처리

**Claude Code 활용 포인트:**
- `cd ~/howtouse_claude && claude` 로 시작 → `/init` 실행
- CLAUDE.md에 웨이포인트·실행 명령 명시 → 매 세션마다 컨텍스트 유지
- Plan Mode로 Multi-step 설계 후 Normal Mode에서 구현

---

## 효과적인 프롬프트 작성법 (3C 원칙)

**Concise(간결) + Contextual(맥락) + Constrained(제약)**

| 상황 | 나쁜 예 | 좋은 예 |
|------|---------|---------|
| 기능 추가 | "Safety Checker 추가해줘" | "기존 parse() 함수 시스템 프롬프트에 안전 규칙 추가. 유리·칼날→refused, JSON 스키마에 refused 상태 추가" |
| 버그 수정 | "에러나요" | "json.loads()에서 JSONDecodeError. Gemini 응답에 텍스트 섞임. response_mime_type 설정 확인·수정" |

---

## 다른 섹션과의 연결
- ROS2 실행 환경: [[ros2_workspace_and_package]]
- nav2_simple_commander 사용: [[nav2_amcl_tf_tree]]
- Gazebo 시뮬: nav2_minimal_tb4_sim (depot.sdf, warehouse.sdf)
