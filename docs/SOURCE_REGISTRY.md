# 입시상담 공식 출처 레지스트리 (SOURCE_REGISTRY)

> 단일 정본은 Python `scripts/source_registry.py`(SOURCES)이며, 이 문서와
> 최종적으로 `ipsi_sources` 테이블(V1064)로 적재된다. robots 판정·실측 근거는 **2026-10-13 curl 기준**.
> 실제 수집 시 `ipsi_fetch.RobotsGate`가 요청마다 robots.txt를 재검증하고 위반 요청을 차단한다(하드 코딩 우회 없음).

## 1. 사이트별 접근·수집 가능 여부

| # | 사이트 / URL | 기관 | 접근방식 | robots(우리 UA) | 자동 본문 수집 | 재배포 정책 | 1차 상태 |
|---|---|---|---|---|---|---|---|
| 1 | adiga.kr (대입정보포털 '어디가') | 대교협 | METADATA_ONLY | **BLOCK** (`Disallow: /`, archiveView.do 개별 Disallow) | ❌ 금지 | METADATA_PRIORITY | 차단 — 메타·링크만 |
| 2 | adiga.kr archiveView.do (menuId=PCUCTCES1000) | 대교협 | METADATA_ONLY | **BLOCK** | ❌ 금지 | METADATA_PRIORITY | 차단 — 메타·링크만 |
| 3 | kcue.or.kr (대교협) | 대교협 | HTTP_STATIC | ALLOW (robots.txt 404=규칙없음) | ✅ 허용 | METADATA_PRIORITY | 수집(PoC: 후보 16) |
| 4 | library.kcue.or.kr (고등교육정보자료실) | 대교협 | **JS_REQUIRED** | ALLOW (robots 없음) | ⚠ 목록이 ajax/JS 로드 | METADATA_PRIORITY | 브라우저/검색 엔드 필요 — 대기 |
| 5 | moe.go.kr (교육부) | 교육부 | HTTP_STATIC | ALLOW (`/search`만 Disallow) | ✅ 허용 | **OPEN**(공공누리) | 수집(게시판 행은 JS 렌더 한계) |
| 6 | search.suneung.re.kr / suneung.re.kr (평가원) | 교육과정평가원 | METADATA_ONLY | **BLOCK** (`Disallow: /`) | ❌ 금지 | METADATA_PRIORITY | 차단 — 메타·링크만. **성적조회=로그인벽 절대 우회 금지** |
| 7 | ebsi.co.kr (EBSi) | EBS | HTTP_STATIC | ALLOW (`Allow: /`, 일부 ajax/Qna 차단) | ✅ 허용 | METADATA_PRIORITY | 수집( 후보 19) — **NON_OFFICIAL_RULE**로 분리 |
| — | 대학별 입학처 (샘플 확장) | 대학 | HTTP_STATIC | URL별 개별 판정 | 대학별 상이 | METADATA_PRIORITY | 1차 미확장(스캐폴드만) |

## 2. robots·이용약관·저작권 판정 근거 (실측)

- **adiga.kr**: robots.txt 최후 `User-agent: * / Disallow: /`. 우선대상 URL(`archiveView.do`)은 화이트리스트 봇에도 개별 Disallow → `RobotsGate`가 요청 BLOCK. → 자동수집 금지, 공식 링크·메타만 보관.
- **www.kcue.or.kr**: robots.txt가 404(파일 없음) → 규칙 없음, 전방 허용으로 간주(보수적: 파일 없음=허용 기록). 보도자료·공지 게시판 HTTP 정적 HTML에서 후보 확보.
- **library.kcue.or.kr**: robots 허용이나 목록 페이지가 ajax(JS) 로드 → 정적 HTML엔 내비만. `access_method=JS_REQUIRED`, 시드는 홈 1건. 2028 시행계획 모음집(PDF/HWP) 확보는 브라우저/검색 API 단계로 이월.
- **www.moe.go.kr**: robots `Disallow: /search`만. 게시판(`boardCnts/listRenew.do`) 본문 허용. 공공누리(KOGL) 자유이용 → redistribution=OPEN. 단 게시판 행이 onclick JS 라우팅이라 정적 추출기에서 상세 링크 확보에 한계(1건 확보).
- **suneung.re.kr**: `User-agent: * / Disallow: /`(HTTP 200, text/plain 실측) → 전봇 차단, `RobotsGate` index.jsp BLOCK 확인. `search.suneung.re.kr`은 성적조회=로그인·개인정보 → `exclude_urls`로 명시 금지. 수능 시행기본계획은 메타·공식링크만.
- **ebsi.co.kr**: `Allow: /` + 일부 차단(Qna/Epilogue/*.ajax/TotalSearch 등). EBS 해설·전략은 **공식 전형규정이 아니므로 content_class=NON_OFFICIAL_RULE**로 분리(작업지시 3단계). 저작권 주의 → METADATA_PRIORITY.

## 3. 재배포 제한 자료 취급 원칙

- `redistribution=METADATA_PRIORITY`또는`RESTRICTED`인 자료는 **원문 전문·본문을 DB에 저장하지 않고**, 메타데이터(기관명·문서명·발표일·적용학년도)+**공식 원문 링크**만 `ipsi_documents`/`ipsi_document_versions`에 보관한다. `search_text`/`raw_storage_key`는 `redistribution=OPEN`(교육부)일 때만 채운다(시드에서 검증됨).
- `robots=BLOCK`(adiga·suneung)인 사이트는 자동 요청 자체가 금지되며, 필요 시 사람이 공식 페이지를 직접 확인한 뒤 **링크·서지정보만** 수기 등록한다.

## 4. 분석 산출물 (2026-10-13, 저장 자료 재분석 — 신규 수집 없음)

- `docs/ANALYSIS/ANALYSIS_INDEX.md` — 근거 티어(T0 공식사실/T1 계산된비교/T2 분석적해석/T3 확인불가), 11문서 앵커, 전제·한계.
- `docs/ANALYSIS/00_universities/*.md` — 7개교 입시 구조(전형 비중·방법·수능최저·일정·표본 모집단위). 한양 method/csat는 T3(null).
- `docs/ANALYSIS/01_cross_university/department_strategy.md` — 유사 학과(경영·컴퓨터·반도체·의약학·인문) 교차 대조[T1] + 수능최저 매트릭스 기반 유불리[T2].
- `docs/ANALYSIS/02_year_change/2027_2028_changes.md` — 2027 확정 vs 2028 시행계획(연세만 확보), 정책(2022 개정·5등급제·통합수능) 정량 영향은 T3.
- `docs/ANALYSIS/03_counseling_qa/knowledge_base.json` — 상담 6 질문유형×답변, 항목별 source_document_key·학년도·티어 연결.
- 파생 스크립트: `scripts/digest_for_analysis.py`, `scripts/compare_for_analysis.py` (저장 JSON 읽기 전용, PDF 재파싱 없음).
- 상태: 전 행 NORMALIZED 유지, APPROVED 승격 0건. `data/youtube/`(Qoder B) 미변경·미합침.
