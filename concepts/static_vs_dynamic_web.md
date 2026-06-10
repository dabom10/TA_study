# 정적 HTML vs 동적 웹페이지 (클라이언트/서버 사이드)

> 검증: MDN — Client-Server overview (https://developer.mozilla.org/en-US/docs/Learn/Server-side/First_steps/Client-Server_overview) — 일치

## 한 줄 요약
HTML은 그 자체로는 **변하지 않는 마크업 문서**이며, 화면이 동적으로 바뀌려면 **브라우저에서 JS가 실행**(클라이언트 측)되거나 **서버가 요청마다 HTML을 새로 만들어 보내야**(서버 측) 한다.

---

## 1. HTML 자체는 정적

- HTML은 문서 구조를 기술하는 마크업 언어. 파일에 적힌 내용이 브라우저에 그대로 그려질 뿐, 스스로 계산·통신·갱신을 하지 않는다.
- 정적 사이트는 서버가 파일 시스템의 HTML을 그대로 반환 → 모든 사용자가 같은 페이지를 받는다.
- 상품 1,000개면 HTML도 1,000개 필요해지는 한계가 있다.

```
사용자 → GET 요청 → 웹 서버 → 파일에서 HTML 검색 → HTML 그대로 반환
```

---

## 2. 클라이언트 측 동적 (CSR, Client-Side Rendering)

**누가 바꾸나**: 내 **브라우저**에서 실행되는 JavaScript.

- 서버는 HTML 골격 + JS, 또는 JSON 같은 **데이터만** 보내고 끝.
- 브라우저가 JS를 실행하면서 DOM을 조작해 화면을 갱신한다.
- 페이지 전체 새로고침 없이 일부만 바뀐다 (SPA의 핵심).

```javascript
fetch('/api/products')
  .then(r => r.json())
  .then(data => {
    document.body.innerHTML = data.map(p => `<div>${p.name}</div>`).join('');
  });
```

**예시**: 좋아요 버튼 색 변경, 이미지 슬라이드쇼, 입력 글자수 카운트, 인스타 무한스크롤.

**장점**: 서버 부하↓, 빠른 페이지 전환
**단점**: 초기 로딩 느림, JS 실행 안 되는 크롤러에 SEO 불리

---

## 3. 서버 측 동적 (SSR, Server-Side Rendering)

**누가 바꾸나**: **서버**가 요청을 받을 때마다 HTML을 새로 조립.

- 같은 URL이라도 로그인한 사람·시간·DB 상태에 따라 **다른 HTML**을 만들어 보낸다.
- 웹 프레임워크(Django, Express, Spring, PHP 등)가 URL → 핸들러 → DB 조회 → 템플릿 렌더링 흐름을 담당.

```python
# Django 예시
def junior(request):
    list_teams = Team.objects.filter(team_type="junior")
    return render(request, 'index.html', {'list': list_teams})
```

**예시**: 네이버 로그인 후 "안녕하세요, 홍길동님", 쇼핑몰 재고 표시, 유튜브 추천 영상.

**장점**: SEO 우수(완성된 HTML), 초기 렌더 빠름
**단점**: 서버 부하↑, 페이지 전환 시 전체 새로고침

---

## 4. 비교표

| 구분 | 정적 HTML | 클라이언트 측 (CSR) | 서버 측 (SSR) |
|------|-----------|---------------------|---------------|
| 누가 바꾸나 | 아무도 | 브라우저 JS | 서버 |
| HTML 생성 위치 | 파일 시스템 (고정) | 브라우저 | 서버 |
| 데이터 소스 | 파일 | API (JSON 등) | DB |
| 새로고침 | - | 불필요 | 보통 필요 |
| SEO | 우수 | 약함 | 우수 |
| 초기 로딩 | 빠름 | 느림 | 중간 |
| 서버 부하 | 낮음 | 낮음 | 높음 |

---

## 5. 식당 비유

- **정적 HTML**: 벽에 붙은 인쇄 메뉴판 — 항상 똑같음
- **클라이언트 측 동적**: 태블릿 메뉴판 — 카테고리 탭 누르면 화면이 바뀌지만 주방에 안 물어봄
- **서버 측 동적**: 점원이 "오늘의 추천은요~" — 사람마다 다르게, 주방(서버)에서 정보를 가져옴

---

## 6. 현실에서는 섞어 쓴다

요즘 웹사이트는 SSR + CSR 혼합 (Next.js, Nuxt 등):
- 초기 페이지는 서버가 HTML로 렌더링 (SEO·초기 로딩)
- 이후 상호작용은 JS가 처리 (SPA 경험)
- 예: 쿠팡 상품 목록(SSR) + 장바구니 담기(CSR)

---

## 참고

- MDN — [Client-Server overview](https://developer.mozilla.org/en-US/docs/Learn/Server-side/First_steps/Client-Server_overview)
