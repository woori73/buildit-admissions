# 2028학년도 대입·수능 유튜브 분석 DB — 1차 보고서 (Qoder B)

- 작업 브랜치: `qoder-b/youtube-analysis` (Qoder A의 공식 입시자료 작업 트리와 분리, 침범 없음)
- 산출물: `data/youtube/videos.json`, `data/youtube/analyses.json`, `data/youtube/topics.json`, `data/youtube/conflicts.json`, `scripts/youtube/`
- 검증: `python scripts/youtube/yt_validate.py` → `data/youtube/validation_report.json` (아래 모든 숫자는 이 스크립트가 파일에서 실시간 산출)
- 생성일: 2026-10-13 / 수집·분석 주체: `qoder-b`
- 모든 행의 `verification_status = NORMALIZED` (§8에 따라 **APPROVED 처리 없음** — 사람 승인 전 운영 상담 검색에 반영 금지)

---

## ① 조사 채널 수·영상 수

| 단계 | 영상 | 채널 | 비고 |
|---|---|---|---|
| 검색 풀 (2028 대입·수능 키워드 10종 + 관련 회수) | 271 | 112 | `work/candidates_raw.json` (비커밋 캐시) |
| 1차 선별·메타 수집(심층 fetch) | 78 | 36 | `data/youtube/videos.json`, 발표자(교수·강사·교사·컨설턴트) 33명 특정 |
| 내용 분석 대상 | 72 | — | `analysis_status=CONTENT_ANALYZED` |

채널 구성(선별 78): EBS 계열 15, 사교육 컨설팅 19, 입시미디어 6, 학원 네트워크 6, 개인 크리에이터 5+전문가 5, 공교육 방송 8, 공교육 기관(교육청·진로교육원) 4, 입시연구기관 4, AI학습 플랫폼 2, 방송 연예 1, 교육 저널리즘 1 등.

신뢰 등급(출처 기반으로 부여, **조회수 미사용**): TIER_1 12 / TIER_2 30 / TIER_3 36.
- TIER_1: 정부·시도교육청·공교육 방송(직접 제작)
- TIER_2: EBS 계열, 대학 입학전형 연구기관, 현직 진학지도 교사, 전 입학사정관
- TIER_3: 학원가·개인 컨설팅·개인 크리에이터

## ② 실제 내용 분석 완료 영상 수

- 내용 분석 완료: **72** (발표자·주제·근거·해석·상담 시 주의까지 구조화)
- 제외: **6** (`METADATA_ONLY`) — 설명란이 비었거나 제목만 있어 주장의 근거를 확인할 수 없는 영상. `analyst_note`에 제외 사유를 기록했고 분석 항목(analysis)을 만들지 않았다.
- 분석 항목: **127** (영상 72개 전수 커버, 항목당 앵커·근거·공식 대조 상태·상담 규칙 부여)
  - classification: EXPERT_ANALYSIS 69 / STRATEGY 24 / DISPUTED 14 / OFFICIAL_FACT 10 / PREDICTION 7 / OUTDATED 3
  - confidence: HIGH 5 / MEDIUM 107 / LOW 15
  - 적용 학년도: 2028 118 / 2027 7 / 2026 2

### 근거 수준 표시 — `evidence_basis` (실제 발언 vs 라벨 기반 복원)

자막을 확보한 영상이 0건이므로, 127개 항목 전부에 `evidence_basis`와 `speech_verified:false`를 부여했다(`scripts/youtube/yt_mark_evidence_basis.py`가 `anchor.src` + 해당 영상의 `content_evidence`에서 결정적으로 파생. 재분석 아님).

| 근거 수준 | 항목 | 의미 |
|---|---|---|
| `AS_PUBLISHED_TEXT` | 8 | 채널이 설명란에 공개한 문언 자체를 근거로 함(발언 청취는 아님) |
| `INFERRED_FROM_TIMELINE_LABEL` | 66 | 설명란 타임스탬프·챕터 라벨의 어휘로 주장 복원, 발화 내용 미청취 |
| `INFERRED_FROM_DESCRIPTION_SUMMARY` | 46 | 채널 제공 설명란 요약문·해시태그 근거, 발화 내용 미청취 |
| `INFERRED_FROM_CHAPTER_LABEL` | 1 | YouTube 챕터 제목 라벨만 근거, 발화 내용 미청취 |
| `INFERRED_FROM_METADATA` | 6 | 제목·채널·일시 등 메타데이터 기반 복원, 발화 내용 미청취 |

- **라벨 기반 복원 119건 / 공개 문언 근거 8건 / 발언 직접 확인 0건.** 상담 시 `INFERRED_*` 항목은 전문가의 확정 발언으로 인용하지 말도록 `usage_rules`에 규칙을 추가했다.
- 근거 수준과 맞지 않는 확실성 라벨을 제거: `INFERRED_*`인데 `confidence=HIGH`였던 **29건**을 MEDIUM으로 하향(항목에 `confidence_capped:true` 기록). 결과 HIGH 34→5, 남은 HIGH 5건은 전부 `AS_PUBLISHED_TEXT`. 검증기가 `INFERRED_* + HIGH`를 오류로 차단한다.
- 발언 행위를 서술한 문구 1건(YT-A085 "발표자는 … 해설했다")을 "챕터 제목 순서가 대학 공개 자료의 체계와 일치 → 해설 구성 추정(발음 내용 미청취)"으로 바꿔, 듣지 않은 내용을 확정 진술로 남기지 않았다.

**자막 확보 한계(중요)**: 본 네트워크에서 YouTube `timedtext`가 HTTP 200 + 본문 0바이트(bot attestation `pot`/`xoaf`)로 차단되어 자막 전문을 확보하지 못했다(`/player` 응답도 UNPLAYABLE). 따라서 근거 계층은 ①공식 설명란의 타임스탬프(챕터 앵커) ②`/next` 챕터 제목 ③EBS 뉴스 등 설명란에 전문이 게시된 경우이며, 각 행의 `content_evidence`에 확보 수준을 명시했다. 자막 원문은 저장·재배포하지 않았다(§8).

## ③ 주제별 핵심 변화와 전략 (topics.json T01–T10)

항목 수: T05 62, T03 47, T09 25, T08 21, T02 19, T06 19, T04 16, T07 14, T10 12, T01 8.

- **T01 2022 개정 교육과정**: 2028은 개정 교육과정·고교학점제 전면 적용 첫 해. 교과군·과목명 변화(통합사회/통합과학), 일반선택→진로·융합선택 위계가 상담의 기본 골격.
- **T02 통합형 수능**: 국어·수학·영어 선택과목 폐지, 탐구는 통합사회·통합과학 각 25문항·40분·50점(이지영·EBS 진술 ↔ 확정안/보도 대조 확인). 심화수학(미적분Ⅱ·기하)은 수능 출제 범위에서 제외.
- **T03 내신 5등급**: 등급 자체의 변별력은 약화, 대학은 정성평가·출결·세특·면접·수능최저로 보완. 9등급 입결과 환산 비교가 최대 쟁점(→YT-C002).
- **T04 고교학점제·과목 선택**: 소인수 과목의 등급 산출 인원 문제가 등급 변동성으로 직결. "흥미·적성/위계성, 진로 연계성, 성취의 질" 3축(이재영 교사)이 공교육 표준 프레임.
- **T05 수시·정시**: 2028 전체 모집 348,789명, 수시 281,895명(80.8%)·정시 66,894명(19.2%) — 대교협 시행계획 공표 기준으로 OFFICIAL_CONFIRMED. 정시에서도 학생부 반영이 확산("수시·정시 경계 붕괴")이 다수 채널 공통 결론.
- **T06 권장과목**: 서울대·숙명여대·경희대 등 발표(설명란에 원문 링크 존재). "권장 ≠ 필수" 구분이 상담 필수 문구.
- **T07 과목별 학습 전략**: 통합사회·통합과학 신규 체제 대비, 국·수·영 공통화. EBSi/공교육 자료 우선 권고.
- **T08 성적대별 전략**: 최상위권(올 1등급 희소성·내신 방어), 중위권(3등급 회피+특목 과목 1등급 제작·병행형), 하위권(이수 과목 연계 틈새 학과). 단, 등급 라인·컷 예측 항목은 전부 LOW~MEDIUM.
- **T09 대학별 2028 전형계획**: 서·연·고·서강·한양·성균관·중앙·경희·동국·인하·경기대 등 개별 독해. 세부 반영비율은 원문 미확보(→YT-C001).
- **T10 2027 vs 2028**: 2027은 현행(9등급·선택과목) 마지막 체제, 2028부터 전환. 재수 리스크·일부 채널의 2027 자료 인용 오류(→YT-C004, YT-C008, YT-C012).

## ④ 전문가 공통 의견과 차이

**공통(다수 독립 채널 + 공교육 출처 일치)**
1. 2028은 "내신 등급 숫자의 가치 하락 + 평가 자료 다변화" 국면 (교과전형의 서류·면접 반영, 수능최저 확대).
2. 정시에도 학생부가 들어오므로 수능 단독 올인 전략은 위험.
3. 통합사회·통합과학이 최상위권 변별 과목으로 부상.
4. 권장과목은 "사실상 필수"처럼 작동할 수 있으나 법적 요건은 아님.

**차이(확정 불가 — conflicts.json)**
- 변별력 약화 vs 충분 (YT-C003): 전제(등급 구간·분포) 해석 차이.
- '교과전형=학종화' 라벨의 적정성 (YT-C005).
- 고교학점제를 선택권 확대 vs 허상으로 보는 시각 (YT-C011).
- 체제 전환 연도의 재수 유리·불리 (YT-C008).
- 과거(2026·2027) 입결을 2028에 외삽할 수 있는가 (YT-C004).

## ⑤ 공식자료 대조 검증 결과

`official_ref.status` 분포: OFFICIAL_CONFIRMED 10 / CONSISTENT_WITH_OFFICIAL 32 / NEEDS_OFFICIAL_DOC 61 / CONFLICT 12 / UNSUPPORTED 12. 원문 URL을 가진 항목 60건.

- **URL 없는 "대조 완료" 라벨 제거**: 기존에 `CONSISTENT_WITH_OFFICIAL`이면서 `official_ref.url`이 없던 **20건**을 `NEEDS_OFFICIAL_DOC`으로 강등했다. 문서 대조를 완료한 항목만 원문 URL과 함께 대조 상태(CONSISTENT_WITH_OFFICIAL / OFFICIAL_CONFIRMED)를 유지하며, 검증기가 URL 없는 대조 상태를 오류로 차단한다.
- 원문 링크 보전 예: YT-A077은 영상 설명란에 게시돼 있던 경희대 입학처 페이지·숙명여대 권장과목 PDF URL을 `official_ref.url`/note로 채취해 기록하되, 본문 대조는 미완료이므로 상태를 `NEEDS_OFFICIAL_DOC`으로 유지했다(추측 URL 사용 금지).
- `official_ref.url` 필드 의미 고정: 실제 URL이 아닌 자료명 서술 27건을 note로 이동하고 필드를 비웠다. 검증기가 `url`이 http가 있으면 오류로 차단하므로, URL이 비어 있으면 "대조 원문 미확보"를 의미한다.

- 확인 예: 348,789명·80.8%·19.2%(대교협 공표 전한 교육부 보도자료· kyobit 보도), 통합사회·통합과학 25문항·40분, 내신 5등급·선택과목 폐지(교육부 2023-12-27 확정안), 고3까지 내신 반영.
- 미해결(원문 필요): 대학별 정시 학생부 반영비율(서울대 20→40% 등), 5등급 구간·9등급 환산표(「학교생활기록 작성 및 관리지침」), 탐구 반영 방식 집계, 학종 비중(23.7%) 분류 기준.
- 자동 정답 금지 원칙: 공식과 다른 진술은 `CONFLICT`로 태깅하고 `conflicts.json`에 **차이와 그 이유**만 기록했다 (12건: YT-C001~C012; 유형별 OFFICIAL_VS_ANALYSIS 5, ANALYST_VS_ANALYST 4, TEMPORAL_DRIFT 1, SELF_CORRECTION 1, METADATA_MISMATCH 1). 상태: UNRESOLVED_PENDING_DOC 6, UNRESOLVED_LEGITIMATE_DISPUTE 5, RESOLVED_BY_CORRECTION 1.
- 대표 사례: 휴브레인이 서울대 지역균형 "1단계 2→3배수" 발언을 스스로 정정(실제 변경은 추천인원 2→3명) → YT-C009 `RESOLVED_BY_CORRECTION`, 정정 전 문구는 어떤 항목에도 사용하지 않음.
- 충돌 연결 항목: 127개 중 87개.

## ⑥ DB에 저장된 분석 항목 수

- videos 78 / analyses **127** / topics 10 / conflicts **12**
- 외래키·무결성 검증 통과(`errors=0`): `analysis.video_id ∈ videos`, `analysis.topics ⊆ video.topic_ids`(union 적용), `conflict_ids ∈ conflicts`, `conflict.side_*.analysis_ids ∈ analyses`, 앵커 `t1 ≤ video.duration_sec`, 열거형 유효, METADATA_ONLY 영상의 analysis 금지, `APPROVED` 행 금지, CJK 혼입 문자 0건(항목 + 헤더).
- 근거 수준 무결성(추가): `evidence_basis`가 저장 필드(`anchor.src`, `content_evidence`)에서 재계산한 값과 일치, `speech_verified = video.caption_available`(전건 false), `INFERRED_*`인데 `confidence=HIGH`이면 오류, `OFFICIAL_CONFIRMED`·`CONSISTENT_WITH_OFFICIAL`인데 URL이 없으면 오류, 헤더에 `evidence_basis_definitions` 필수.

## ⑦ GitHub 브랜치·PR·파일 경로

- 브랜치: `qoder-b/youtube-analysis`
- 파일: `data/youtube/{videos,analyses,topics,conflicts}.json`, `data/youtube/validation_report.json`, `docs/YOUTUBE_ANALYSIS_REPORT.md`, `scripts/youtube/{yt_build_videos.py,yt_mark_evidence_basis.py,yt_validate.py}` (+ 수집 스크립트 일체)
- Qoder A 경로(`data/meta/**`, `data/parsed/**`, `data/seed/**`, `docs/FIRST_PASS_REPORT.md`, `docs/SOURCE_REGISTRY.md`, `docs/schema/V1064~V1067`, 기존 `scripts/*.py`)는 수정·삭제하지 않았으며 커밋 범위에 포함하지 않음.
- 스키마 재사용: `verification_status` 5단계, `content_class`, `redistribution`, `access_method`, `url_hash(sha256)` 어휘를 Qoder A의 `ipsi_*` 정의와 동일하게 사용.

## ⑧ 추가 조사 필요 항목

1. 대학별 2028 입학전형 시행계획 **첨부 PDF/기타파일** 원문: 서울대·연세대·고려대·한양대·성균관대·서강대·경희대·동국대(경주 포함)·중앙대·인하대·경기대, 의대 6곳 → YT-C001/C007 수치 확정.
2. 「학교생활기록 작성 및 관리지침」 훈령 최신본 → 5등급 구간·소인수·예외과목 표기 규정 (YT-C002).
3. 한국교육과정평가원 2028 수능 시행계획·출제계획 → 통합탐구 문항·배점·시간 공식 확인.
4. 수능 최저 충족률 원자료(발표자 인용 수치의 1차 소스) → YT-C004/C006.
5. EBSi 겨울방학 설명회 '2027 × 통합사회' 라벨 경위 (YT-C012).
6. 자막 확보 가능한 다른 합법 경로(공식 요약·자료집 PDF·채널 제공 스크립트) 확보 시 Low-confidence 항목 재검증.
7. 2028 시행계획 '최종' 모집요강(2026년 5월경 대학별 공지) 대비 1차 시행계획 변경분 반영.

---

### 상담 활용 규칙 (analyses.json 헤더·topics.json usage_rule과 동일)
1. 공식 규정 우선: `OFFICIAL_FACT` 또는 `OFFICIAL_CONFIRMED`를 기준 답변으로 사용.
2. 전문가 해석·전망은 문구에 '해석/전망'임을 반드시 표기(`EXPERT_ANALYSIS`, `PREDICTION`, `STRATEGY`).
3. `DISPUTED`·`OUTDATED`·`UNSUPPORTED` 또는 `conflict_ids`가 있는 항목은 단일 근거 결론 금지 — 차이와 확인 경로를 함께 안내.
4. `confidence=LOW`는 개인 합격·불합격 배치에 사용하지 않음.
5. `verification_status != APPROVED` 데이터는 운영 상담 검색에 자동 반영하지 않음(§8).
6. `evidence_basis=INFERRED_*`(119건)·`speech_verified=false` 항목은 전문가의 확정 발언으로 인용하지 말고 '설명란·챕터 라벨 기반 복원'임을 함께 표기.
7. 원문 URL이 없는 항목은 `NEEDS_OFFICIAL_DOC`/`UNSUPPORTED`이므로 "공식 확인 완료"로 말하지 않음.
