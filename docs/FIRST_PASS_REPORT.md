# BuildIt AI 입시상담 DB — 1차 결과 보고서 (2026-10-13)

범위: 작업지시 5단계 1차(소스 목록 / 2027·2028 수집 / 수집기·파서 / DB 스키마 / 샘플 적재 / dedup·누락·학년도·출처 검증 / 수집·실패 카운트).
격리: BuildIt **운영 저장소·운영 DB와 분리된 개발 환경**에서 진행. **운영 DB 변경·기존 서비스 수정·main 병합·운영 배포 없음.**

> 핵심 원칙 재확인 — **"자료 수집 = 검증완료 아님."** 아래 확보 자료는 전부 `COLLECTED/EXTRACTED` 단계이며,
> 원문과 구조화 결과의 일치 확인(검증·승인)을 거치기 전에는 상담 검색에 노출되지 않는다(APPROVED-only 게이트).

---

## 1. 사이트별 접근성·수집 가능 여부

상세 근거는 [SOURCE_REGISTRY.md](SOURCE_REGISTRY.md) 참조. 요약:

| 출처 | 접근 | 자동수집 | 처리 |
|---|---|---|---|
| kcue.or.kr | HTTP_STATIC | ✅ | 본문·첨부 후보 확보 |
| moe.go.kr | HTTP_STATIC | ✅(게시판 행 JS 한계) | 공공누리 OPEN, 후보 확보 |
| ebsi.co.kr | HTTP_STATIC | ✅ | NON_OFFICIAL_RULE로 분리 |
| library.kcue.or.kr | JS_REQUIRED | ⚠ 목록 ajax | 브라우저/API 이월 |
| adiga.kr(/archiveView) | METADATA_ONLY | ❌ robots 차단 | 메타·링크만 |
| suneung.re.kr(/search) | METADATA_ONLY | ❌ robots 차단 | 메타·링크만(로그인벽 금지) |
| 대학별 입학처 | URL별 | 개별 판정 | 1차 미확장(스캐폴드) |

이용약관/저작권/재배포: robots.txt + 공개 페이지 실측 basis. 재배포 제한 자료는 **원문 미저장, 메타+공식링크만** 보관.

## 2. 실제 확보 문서 및 건수

수집 파이프라인(discover → parse) 실행 결과:
- 크롤링 소스 3 / 게시판 6 fetched / blocked 0 / failed 0
- **후보 문서 36건** — kcue 16 · moe 1 · ebsi 19
- 그중 **본문 파싱(EXTRACTED) 4건** (kcue 공지/보도 상세; 첨부 PDF/HWP 링크 검출, 예: "2029학년도 대학입학전형기본사항(안)_전문.pdf" 등)
- 정규화 시드(`build_ipsi_seed.py`, url_hash dedup 후): `ipsi_sources 7 / ipsi_documents 36 / versions 36`

## 3. 대학·학과·전형 정보 빌드 상태

- **스키마·DB 계층 구현 완료 & 검증됨.** `docs/schema/`의 V1064~V1067(9 테이블) 기준으로 저장(dedup·버전보존)·검색(APPROVED 게이트·확인불가 경로) 로직을 구현하고 단위검증(H2 임베디드)으로 통과. 애플리케이션 구현 코드는 BuildIt 비공개 앱에서 관리(이 공개 저장소에는 미포함).
- **실 데이터 적재: 0건(1차 의도).** `ipsi_universities/departments/admission_types/prior_results`는 아직 빈 상태. 후보 PDF/HWP **전문 파싱→전형행 정규화**가 2단계 확장 작업(아래 7). 샘플대학 PoC를 통과해야 전국 확대로 진행한다는 지시대로, 확장은 검증 후에.

## 4. 자료별 검증 상태

| 단계 | 건수 | 상담검색 노출 |
|---|---|---|
| COLLECTED(발견만) | 32 | ❌ |
| EXTRACTED(본문추출) | 4 | ❌ |
| NORMALIZED / REVIEW / APPROVED | 0 | APPROVED만 ✅ |

`verification_status`는 `COLLECTED→EXTRACTED→NORMALIZED→REVIEW→APPROVED`로만 승격(내리막 금지, 엔티티 강제).
적용학년도·출처 누락 자료는 검색 제외: 시드에서 **적용학년도 누락 34 / 출처URL 누락 0**. → 누락분은 전문 파싱·검증에서 학년도를 확정해야 상담 후보가 된다.

## 5. 저작권·이용 제한 정리

- 자동수집 금지(robots): **adiga.kr, suneung.re.kr** → 메타·공식링크만. `search.suneung`=로그인·개인정보 절대 우회 금지.
- JS로만 열람: library.kcue → 브라우저/검색 API 필요(강제 크롤링 금지).
- 재배포 정책: 교육부=OPEN(공공누리, 본문·검색텍스트 저장 가능), 그 외=METADATA_PRIORITY(원문 전문 미저장, 링크·서지만). 시드가 이를 반영(EBS/kcue 메타의 search_text/raw 미채움).
- EBS 해설·전략은 공식 전형규정과 **별도 content_class(NON_OFFICIAL_RULE)** — 상담 답변에서 공식 규정으로 인용 금지, 기본 검색 제외(opt-in).

## 6. DB 구조 + 검색 설계

- 테이블(9): `ipsi_sources` → `ipsi_documents` → `ipsi_document_versions`(버전보존, 원본/구조화/검색텍스트 분리) / `ipsi_universities`·`ipsi_departments` / `ipsi_admission_types`(핵심 전형)·`ipsi_recommended_subjects`·`ipsi_schedules`·`ipsi_prior_results`. 모든 레코드에 원문URL·기관명·문서명·발표일·적용학년도·수집일·검증상태.
- **RAG 2계층 결합**: (a) 구조화 조건 검색(학년/대학/수시·정시/전형 키워드 → `ipsi_admission_types`·`ipsi_prior_results`), (b) 문서 근거 검색(APPROVED 현재버전 + 공식 `content_class` + 원문URL → `ipsi_documents`). (c) 적재 단계는 `content_hash` 동일 시 새 버전을 만들지 않고 변경 시에만 버전을 추가(버전 보존).
- 답변 계약(작업지시 4단계): 검색 결과는 **대학명·적용학년도·기관명·공식문서명·원문링크**를 반드시 담고, 근거 없으면 `found=false` + `"확인 불가"`(추측 금지). 세 경로(승인노출/비공식분리/확인불가) 모두 검증.
- 백엔드: MySQL 8 + Flyway로 스키마 관리. 벡터인프라 없이 기존 검색(LIKE/JSON 코퍼스) 패턴을 계승하며, 임베딩/RAG 랭킹 고도화는 확장 단계.

## 7. 누락 자료 + 다음 수집 계획

**누락/미해결**
- 2028학년도 **대학입학전형 시행계획 모음집** 전문(library.kcue = JS/검색 API), 2028 대입 **확정안** 교육부 전문(게시판 행 JS 라우팅), 2028 수능 시행기본계획(suneung robots 차단 → 링크만).
- 대학별 **최신 모집요강(2027/2028)·전년도 경쟁률·권장과목**: 대학 입학처 미스캐폴드.
- 후보 문서의 **적용학년도 확정**(34건 누락)과 첨부 **PDF/HWP 텍스트 추출** 미구현.

**다음 계획(확대는 PoC 검증 통과 후, 운영 write/deploy는 별도 승인)**
1. PDF/HWP 전문 추출기(`pdfminer`/`hwp5` 등) + 시행계획·모집요강 표→`ipsi_admission_types` 정규화 매퍼.
2. library.kcue·교육부는 허용된 검색 API/브라우저 세션으로 목록 확보(robots·로그인 준수의 범위 내에서만).
3. 샘플 대학 3~5곳 입학처 robots 개별 판정 후 모집요강/경쟁률 파일럿 적재 → dedup·검증·승인 흐름 실데이터로 확인.
4. 검증·승인 워크플로(REVIEW 격리, 상충자료 처리) UI/쿼리 + `NORMALIZED→REVIEW→APPROVED` 승격 절차 확정.
5. 전국 2027·2028 확대로 전환(사이트 이용조건 준수, 운영 DB 반영·배포는 사전 승인).

---
### 저장소 구조 (이 공개 저장소)
- 수집·검증 스크립트: `scripts/{ipsi_fetch,source_registry,discover_docs,parse_article,build_ipsi_seed}.py`
- 공식자료 메타데이터(출처·적용학년도·원문링크/수집 provenance): `data/parsed/*`(discovery·articles), `data/meta/*`, `data/seed/{ipsi_seed.json,build_report.json}`
- DB 스키마(DDL): `docs/schema/V1064__..V1067__*.sql` (9 테이블)
- 운영 문서: `docs/SOURCE_REGISTRY.md`, 본 보고서
- 재배포 권한이 없는 원문(HTML/PDF/HWP 전문)은 커밋하지 않는다(`data/raw/`는 gitignore). 회원 원문 본문은 메타+링크만 보관.
- **주의**: 이 저장소는 수집·스키마·메타데이터·검증 결과만 담는다. DB/RAG 애플리케이션 구현(엔티티·서비스·검색 코드·마이그레이션 적용)은 BuildIt privately-managed 애플리케이션에서 개발·버전 관리되며, 공개 저장소에는 포함하지 않는다.
