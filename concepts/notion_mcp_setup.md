# Notion MCP 연동 설정

## 한 줄 요약
Claude Code에 Notion MCP 서버를 등록해 Notion 페이지를 자연어로 읽고 쓸 수 있게 한다.

## 핵심 내용

### 사전 요건
- Node.js 설치 필요 (`npx` 포함)
- Ubuntu에서 Node.js 미설치 시:
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  sudo apt-get install -y nodejs
  node --version && npx --version  # 확인
  ```

### Notion API 토큰 발급
1. `https://www.notion.so/my-integrations` 접속
2. **New integration** 클릭 → 이름 입력 → Submit
3. **Internal Integration Token** 복사 (`ntn_...` 형태)

### 연동할 페이지에 Integration 권한 부여
Claude Code에서 접근할 각 페이지/데이터베이스마다:
- 페이지 우상단 `...` → **Add connections** → Integration 선택

### MCP 서버 등록
```bash
claude mcp add notion \
  -e OPENAPI_MCP_HEADERS='{"Authorization": "Bearer <YOUR_TOKEN>", "Notion-Version": "2022-06-28"}' \
  -- npx -y @notionhq/notion-mcp-server
```

> 검증: 이 대화에서 직접 실행 후 `✓ Connected` 확인 — 일치

**주의사항:**
- 명령어는 반드시 **한 줄**로 입력 (줄바꿈 시 오작동)
- 토큰을 대화창에 붙여넣지 말 것 (보안)
- 이미 등록된 경우 `claude mcp remove notion` 후 재등록

### 등록 확인
```bash
claude mcp list
# notion: npx -y @notionhq/notion-mcp-server - ✓ Connected
```

### 토큰 재발급이 필요한 경우
- `https://www.notion.so/my-integrations` → 해당 Integration → Secrets 탭 → **Regenerate token**
- 재발급 후 `claude mcp remove notion` → 새 토큰으로 재등록

## 다른 섹션과의 연결
- [[claude_code_usage_patterns]] — Claude Code MCP 전반 개념

## 의문점 / 나중에 파고들 것
- MCP 서버가 읽을 수 있는 Notion 데이터 범위 (Block API vs Search API)
- `claude mcp add` 시 `-s` 옵션으로 범위 지정 (local / user / project)
