# 대학 입시 상담 AI — 2단계 검증 결과 보고 (2026-10-13)

대상: `woori73/buildit-admissions` main(PR #1·#2 병합 이후). 원칙: 기존 수집·파싱·분석 반복 없음, **APPROVED 자동 승격 0건**(후보 분류만), 운영 DB 적재·상담 AI 연결·배포 없음, `data/youtube/`(Qoder B) 읽기만.
> 보강 라운드(같은 날): 본 절의 수치는 PR #3 보완 후 값 — 성균관대 2행 정정(원문 대조 근거), 일정 66건 소스 연결, 충돌 15건 대장 보강, 시뮬 재채점 반영.

## 1. 공식자료 검증 (11문서 × 정규화 데이터)

산출물: `scripts/validate_official_data.py`(+`backfill_schedule_sources.py`) → `data/validation/official_validation.json`

| 항목 | 결과 |
|---|---|
| 모집단위 행 | 480 검증 — 행합 불변 **PASS 480 / FAIL 0 / DEFER 6** |
| 성균관대 2행 | `합계` 0 결함 해소: 원문(특성화고졸재직자 정원외 표 "AI융합운영 94 / 산업인공지능 93", 총계 187=94+93)으로 **합계=94/93 정정**, seed·parsed 동기·correction_note·corrected_at 기록(추정 아닌 행 내 단일값 산술 보정) |
| DEFER(미확정) | 서울대 '광역' 마커 2행(중복), 한양대 0행 4개(성악·작곡·피아노·연영 스탭) — 육안 확인 전 |
| 전형 행 | 57 — **APPROVED 전환 후보 48**, 주의 후보 9(한양대: method·최저·자격·인원 null) |
| 일정 행 | 66 — 전 행 `source_document_key` 백필 + parsed 일정과 **항목·날짜 완전일치 EXACT 66/66** → 후보 66(DEFER 0). 백필 규칙=대학+학년도 유일 문서 매핑, item/date 원문 무변경 |
| 결함 대장 | HIGH 0 / MED 26 / LOW 6 / INFO 8 (INFO=집계 전용 열 modeling: 고려 재직자18, 경희 장애인15, 인하 서해5도 열합40·실선발3, 한양 정원외 괄호) |
| 2027/2028 분리 | 2028 행은 doc_yon_2028_plan 기원 2건뿐, 조작된 2028 수치 0 — 분리 재확인 |

검증된 항목은 후보로만 분류(실제 승격은 원문 육안 대조+운영자 승인 필요).

## 2. 유튜브 분석자료 vs 공식자료 4분류

산출물: `scripts/crosscheck_youtube_official.py` → `data/validation/youtube_crosscheck.json` (원본 미변경)

| 분류 | 건수 | 의미 |
|---|---|---|
| ① 공식자료와 일치 | **42** | OFFICIAL_CONFIRMED 10 + CONSISTENT_WITH_OFFICIAL 32. 단 2028 항목은 보유 원문이 연세대뿐 — '연세 외 미대조' 조건부 |
| ② 충돌 | **15** | CONFLICT 12 + DISPUTED. 대표: YT-C010(수시 80.3% vs 대교협 80.8%), YT-C003(변별력 양 진영), YT-C008(재수 유리·불리) |
| ③ 전문가 의견·해석 | **66** | EXPERT_ANALYSIS·STRATEGY·PREDICTION·OUTDATED — '전문가 해석/전망' 표기 필수 |
| ④ 직접 발언 확인 필요 | **4** | 공식 사실 주장이나 원문 미대조(YT-A056·A068·A070·A085) |

- 전 항목 `speech_verified=false` 오버레이 유지 — 119건은 설명란·챕터 라벨 기반 복원, 8건만 게시 텍스트 근거(발언 자체는 전부 미확인).
- 우리 7개교 인용 32건, conflict_id 연결 87건.
- **② 15건 검증 수준 보강**(`bucket2_audit`): 충돌대장 연결 15/15, `counseling_rule` 보유 15/15, 각 항목에 topics+충돌 요지(side_a/side_b·difference_reason·resolution) 첨부. resolution 분포: LEGITIMATE_DISPUTE 7 / PENDING_DOC 3 / 혼용 5 / (대장 전체: RESOLVED_BY_CORRECTION 1 포함 12건). YT-C009(SELF_CORRECTION, RESOLVED)도 보유 2027 원문과 전제 상충 시 별도 충돌의혹 기록.
- spot-check 핵심: **YT-A056 '지역균형 원래 3배수' 정정문은 보유 서울대 2027 요강(1단계 2배수·고교별 추천 2명, p1·p15)과 전제가 어긋남** → 서울대 2028 시행계획 원문 재확인 전 인용 금지. YT-A071(성균 2027 정시)·YT-A072(연세 논술 재시험)은 정시 문서·공지 미보유로 부분대조.
- **덮어쓰기 금지**: 어떤 ②③④ 항목도 T0 공식값을 교체하지 않았고, knowledge_base의 답변 우선순위는항상 보유 공식 문서.

## 3. 상담 지식 기반 (knowledge_base.json 확장)

- Q1~Q6 전 유형에 6개 필수 필드 연결: 해당 대학·학과·전형 / 적용 학년도 / 공식 근거 문서+위치(쪽) / 확인된 사실 / 추가 확인 필요 / 유튜브 보조 설명(①~④+복원 라벨).
- 유형 확장 3종: **Q7** 2028 체제(공식 1차 미보유 — 유튜브 ②③④ 게이트, '전문가 해석' 표기 강제), **Q8** 지원자격(T0 매트릭스 기반: 인하 p6 등), **Q9** 일정(66행 source_document_key 연결·EXACT 대조 완료 → 승격 후보, 최종 APPROVED는 운영자 승인 전까지 미노출).
- insufficient_evidence 7건 중 1건(schedules 키) 해소 → 미해소 6건(2026 입결 0건, 정시 요강, 한양 본문, 2028 타 대학, 권장이수, 정책 1차 문서).

## 4. 상담 시뮬레이션 22문항

산출물: `docs/ANALYSIS/03_counseling_qa/simulation_results.json`

- 구성: 대학 간 비교 4 / 수능최저 5 / 지원자격 4 / 2027·2028 차이 4 / 자료 부족 3 / 일정 2 — **PASS 22 / PARTIAL 0 / FAIL 0** (보강 라운드 재채점).
- 이전 PARTIAL 3건 해소 근거(recheck 필드 기록): **S09** 고려 검정고시 자격을 T0 요강 근거로 재인용, **S17** 유튜브 ID 목록(T06 19개: ①A047·A067·A118 / ④A068 / ③나머지) 특정 완료, **S19** 일정 DEFER → 'EXACT 66/66 완료(승격 후보, 운영자 승인 전 미노출)'로 답 수정.
- 교정된 실패 위험 3건: S07 초안의 한양 최저 추정(폐기→T3 거부), S13 초안의 80.3/80.8 혼합(대교협 기준 단일화), S19 초안의 날짜 무고지 단정(DEFER 고지 추가).
- 함정 문항(S14 외삽·S16 2.5등급 라인·S18 6장 조합·S20 2028 접수) 전부 '합격선·확률 미생성 + 구조 답변'으로 처리 — 3대 실패 기준(잘못된 단정·학년도 혼동·근거 없는 추천) 위반 0.

## 5. 추가 확보가 필요한 공식자료

1. 대교협 2028학년도 대학입학전형시행계획 공표 1차 문서(전국 총 348,789·수시 80.8% 판정)
2. 서울·성균관·고려·한양·경희·인하 **2028 시행계획**(연세 외 6개교) — YT-A012/A016/A019 계열 2028 주장 대조
3. 7개교 **2027 정시 모집요강**(정시 인원·반영비·최저) — YT-A071 등 판정
4. 한양대 2027 요강 본문(method·수능최저·eligibility — 9개 전형 주의 해제)
5. 서울대 '광역' 마커 2행·한양대 0행 4개(성악·작곡·피아노·연영 스탭) DEFER 6건 육안 확인 (성균관대 2행 합계는 원문 대조로 정정 완료 — 속행 해제)
6. 교육부 2022 개정·내신 5등급·평가원 2028 수능 시행계획 1차(Q7 정책 사실 앵커)

## 6. 상담 AI 연결 후속 개발 사항 (이번 단계 범위 밖 — 미수행)

- schedules 66행 `source_document_key` 백필·EXACT 대조 완료(2026-10-13) → 일정 답변 노출은 승격(운영자 승인) 이후
- APPROVED 후보 승격 워크플로(원문 육안 대조 + 운영자 승인 UI) — 승격은 운영 단계 결정
- knowledge_base 6개 답변 필드 → 상담 AI 응답 스키마 매핑(유튜브 보조 문구 자동 라벨: ①~④·복원·LOW 개인배치 금지)
- simulation_results.json을 회귀 테스트 하네스로 확장(학년도 혼동·근거 없는 추천 자동 탐지)
- NORMALIZED 게이트: APPROVED 전 항목은 검색 미노출 유지(운영 DB 적재 없음)

## 7. 커밋·PR

- 브랜치 `feat/stage2-validation-counseling` → **PR #3**(보완 후 main 병합 승인됨).
- 변경: `scripts/validate_official_data.py`, `scripts/crosscheck_youtube_official.py`, `scripts/backfill_schedule_sources.py`(신규), `data/validation/*.json`(2), `data/seed/ipsi_seed_univ_sample.json`(성균 2행 정정·일정 66행 소스 연결), `data/parsed/univ_sample/skku_2027_susi_overview.json`(성균 정정 동기), `docs/ANALYSIS/03_counseling_qa/knowledge_base.json`(Q9·evidence 갱신), `docs/ANALYSIS/03_counseling_qa/simulation_results.json`(재채점), `docs/ANALYSIS/ANALYSIS_INDEX.md`, `docs/STAGE2_REPORT.md`(본 문서). `data/youtube/`(Qoder B) 원본 무변경.
