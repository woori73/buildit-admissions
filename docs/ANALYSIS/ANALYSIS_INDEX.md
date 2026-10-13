# 입시자료 분석 (stored-materials analysis) — 2026-10-13

범위: 이미 `buildit-admissions`에 수집·저장된 자료만 분석한다.
**새 수집·PDF 재다운로드·재파싱·통과 테스트 반복 없음** — `data/parsed/univ_sample/*.json`·`data/seed/ipsi_seed_univ_sample.json`·`docs/SAMPLE_ANALYSIS_REPORT.md`의 구조화 산출물을 그대로 재사용한다(스크립트: `scripts/digest_for_analysis.py`, `scripts/compare_for_analysis.py` — 저장 JSON 필드 읽기만 수행).
운영 DB 반영·배포·자동 APPROVED 승격 없음. 모든 행 검증 상태는 NORMALIZED(상담 검색 미노출 게이트 유지).

## 0. 근거 티어(모든 분석 결과에 명시)

| 티어 | 의미 | 요구 조건 |
|---|---|---|
| **T0 공식사실** | 원문 모집요강·시행계획에 직접 기재된 값 | 원본 문서 ID(`doc_*`) + 페이지 + 적용학년도 연결 |
| **T1 계산된비교** | 저장된 수치에서 산술 도출(합·비율·정렬·대조표) | 입력 행의 T0 근거 + 계산식 |
| **T2 분석적해석** | T0/T1 기반 상담 관점 해석·유불리 판단 | 근거 티어 명시, 확정 사실로 승격 금지 |
| **T3 확인불가** | 저장 자료로 뒷받침 불가(미추출·미발표·추정 금지) | 사유 기록, 추정치 금지 |

## 1. 분석 대상 전체 건수 (data/seed/ipsi_seed_univ_sample.json counts)

| 항목 | 건수 |
|---|---|
| 대학 | 7 (서울·연세·성균관·고려·한양·경희·인하) |
| 공식 문서 | 11 |
| 모집단위(학과) 행 | 480 |
| 전형 행 | 57 |
| 전형일정 행 | 66 |
| 전년도 입시결과 | 0 (T3 — 미추출) |
| APPROVED | 0 (전 행 NORMALIZED) |

수집 메타데이터 36건 분류(`collection_classification.json`): NON_OFFICIAL_RULE 19 / NOT_ADMISSIONS 13 / OFFICIAL_RULE_NATIONAL 2 / OFFICIAL_CONTEXT 1 / NON_DOCUMENT 1 — 이 중 본 분석의 T0 근거는 대학별 공식 요강·시행계획 PDF에서 구조화된 11개 문서에 한정.

## 2. 문서 ID · 출처 · 적용학년도 (근거 앵커)

| 문서 ID | 대학 | 적용학년도 | 원문 |
|---|---|---|---|
| doc_snu_2027_susi | 서울대 | 2027 | 수시모집 모집요강(2026-05-29) |
| doc_yon_2027_susi | 연세대 | 2027 | 수시모집 모집요강(2026-05-29) |
| doc_yon_2027_susi_part2 | 연세대 | 2027 | 수시모집 요강 Ⅱ부(모집단위별 인원) |
| doc_yon_2027_plan | 연세대 | 2027 | 서울캠퍼스 입학전형 시행계획(2026-04) |
| doc_yon_2028_plan | 연세대 | 2028 | 서울캠퍼스 입학전형 시행계획(2026-04) |
| doc_skku_2027_susi | 성균관대 | 2027 | 수시모집 모집요강(2026-08-13) |
| doc_skku_2027_overview | 성균관대 | 2027 | 수시모집 요강 02.모집인원 총괄표 |
| doc_korea_2027_susi | 고려대 | 2027 | 수시모집요강 서울캠퍼스(2026-05) |
| doc_hanyang_2027_susi | 한양대(서울) | 2027 | 수시모집 요강 총괄표 |
| doc_khu_2027_susi | 경희대(서울) | 2027 | 수시모집 요강(2026.5.13 최종본) |
| doc_inha_2027_susi | 인하대 | 2027 | 수시모집요강 전형별 모집인원 |

## 3. 산출물 구조

```
docs/ANALYSIS/
├── ANALYSIS_INDEX.md                      (본 문서)
├── 00_universities/                        대학별 입시 구조 분석
│   ├── SNU.md  YONSEI.md  SKKU.md  KOREA.md  HANYANG.md  KHU.md  INHA.md
├── 01_cross_university/
│   └── department_strategy.md              유사 학과 교차 비교 + 지원 전략
├── 02_year_change/
│   └── 2027_2028_changes.md                확정(2027) vs 시행계획(2028)
└── 03_counseling_qa/
    └── knowledge_base.json                 상담 질문 유형 × 답변 근거
```

## 4. 전제·한계 (T3 확인불가 — 전 대학 공통)

- **전년도(2026) 입시결과 0건**: 경쟁률·충원·권장이수과목 미추출 → "실제 합격 가능성"은 T3. 합격선·커트 추정도 T3(추정 금지).
- **정시(수능) 세부**: 대부분 요강 수시 총괄만 확보 — 정시 반영비율·등급은 T3.
- **한양대 전형방법·수능최저**: 요강 본문 미추출 → method/csat = null(T3).
- **2028 확정 요강**: 2028 수시요강은 각 대학 2027년 5월 발표 예정 → 연세대 2028 시행계획 외 T3(보충 추정 금지).
- 내신 산출식(변환등급·석차환산 가중치)·전년도 경쟁률은 본 수집범위에 없음.

## 5. Qoder B 유튜브 자료 분리

본 분석은 공식 문서 기반이다. `data/youtube/`(Qoder B 영역)의 전문가 의견·해설은 **별도 자료로 유지**하며, 여기서는 단 1건도 T0 공식사실로 합치지 않았다. 접점 금지 원칙: 전문가 해석 → 상담 참고용(비공식), 원문 수치 → T0.
