# 2027 정시 모집요강 수집·수시 보완 보고 (2026-11-02)

7개 대학(서울대·연세대·고려대·성균관대·한양대·경희대·인하대)의 2027학년도 **정시 모집요강**을 공식 원문에서 구조화하고, 기존 수시 시드의 빈 칸·오류를 원문으로 바로잡았다.

## 원칙
- 공식 원문만 사용: 각 대학 입학처, 또는 대교협 대입정보포털(adiga.kr)에 대학이 직접 올린 모집요강. 학원·언론 사본 미사용.
- 추측 금지: 원문에서 확인하지 못한 값은 null, 이유는 각 파일 `gaps`.
- 모든 값에 근거 쪽수(`evidence_pages`, PDF 실제 쪽).
- 학과별 인원 합 = 원문 합계·소계 대조(대학별 `verification`, 불일치 0건).
- 원문 PDF는 `data/raw/pdfs/`(gitignore, 커밋하지 않음).
- 접근: 성균관대(입학처 404)·인하대(연결 차단)는 adiga.kr 게시 공식 PDF 사용.

## 정시 파일
| 파일 | 문서 | 게시일 | 전형 | 학과 행 | 일정 | 원문 |
|---|---|---|---|---|---|---|
| `hanyang_2027_jeongsi.json` | 2027학년도 한양대학교 신입학 정시 모집요강 | 2026-08-31 | 12 | 61 | 15 | https://go.hanyang.ac.kr/file/pdfDown.do?menu=mojib&file_no=521&type=pdf |
| `inha_2027_jeongsi.json` | 2027학년도 인하대학교 정시모집요강 | 미확인 | 10 | 77 | 19 | https://www.adiga.kr/cmm/com/file/fileDown.do?fileId=00000000000000242995&fileSn=1&menuId=PCUVTINF2000&downLogYn=Y&unvCd=0000169&searchSyr=2027 |
| `khu_2027_jeongsi.json` | 2027학년도 경희대학교 정시 신입생 모집요강 | 2026-09-01 | 10 | 87 | 19 | https://iphak.khu.ac.kr/file/download.do?sfn=20260901092038766_2027+%ea%b2%bd%ed%9d%ac%eb%8c%80%ed%95%99%ea%b5%90+%ec%a0%95%ec%8b%9c+%ec%8b%a0%ec%9e%85%ec%83%9d+%eb%aa%a8%ec%a7%91%ec%9a%94%ea%b0%95_20260901_fv.pdf&ofn=2027+%ea%b2%bd%ed%9d%ac%eb%8c%80%ed%95%99%ea%b5%90+%ec%a0%95%ec%8b%9c+%ec%8b%a0%ec%9e%85%ec%83%9d+%eb%aa%a8%ec%a7%91%ec%9a%94%ea%b0%95_20260901_fv.pdf |
| `korea_2027_jeongsi.json` | 2027학년도 정시모집요강(서울캠퍼스) | 미확인 | 6 | 66 | 23 | https://oku.korea.ac.kr/attach/202609/1790733929908_0.pdf |
| `skku_2027_jeongsi.json` | 2027학년도 정시모집 모집요강 | 미확인 | 17 | 37 | 13 | https://www.adiga.kr/cmm/com/file/fileDown.do?fileId=00000000000000256733&fileSn=1&menuId=PCUVTINF2000&downLogYn=Y&unvCd=0000133&searchSyr=2027 |
| `snu_2027_jeongsi.json` | 2027학년도 대학 신입학생 정시모집(‘나’군) 안내 | 미확인 | 5 | 77 | 129 | https://admission.snu.ac.kr/webdata/admission/files/2027jungsi.pdf |
| `yonsei_2027_jeongsi.json` | 2027학년도 정시모집 모집요강(서울캠퍼스) | 2026-09-01 | 10 | 73 | 24 | https://admission.yonsei.ac.kr/seoul/upload/guide/20260901184445WSGU8N.PDF |
| `yonsei_2028_jeongsi_plan.json` | 2028학년도 연세대학교 서울캠퍼스 입학전형 시행계획 – 정시모집 부분 (시행계획(요강 아님)) | 2026-04 | 9 | 67 | 0 | https://www2.yonsei.ac.kr/entrance/plan/2028_plan.pdf |

## 수시 보완 파일(`*_fill.json`)
| 파일 | 칸 보완(fills) | 빠진 학과 추가 | 일정 교체 |
|---|---|---|---|
| `hanyang_2027_susi_fill.json` | 9 | 0 | 22 |
| `inha_2027_susi_fill.json` | 12 | 0 | 0 |
| `skku_2027_susi_fill.json` | 4 | 0 | 0 |
| `snu_2027_susi_fill.json` | 4 | 15 | 0 |
| `yonsei_2028_plan_fill.json` | 2 | 0 | 0 |

주요 정정:
- 서울대 수시: 기존 파싱이 요강 11쪽(생활과학대학~치의학과 15개 학과)을 빠뜨려 지역균형 414→**523**, 일반 1,169→**1,458**(실기위주 71 제외), 기회균형 140→**181**로 정정. 11쪽 합계행 523/1,529/181로 검증.
- 한양대 수시: 일정 15건이 원문과 달라(원서접수 9.8~9.11, 논술 11.28~29, 발표 12.18) 원문 22건으로 교체. 기존 행은 `archive_schedules`로 운영 DB에서 보관 처리.
- 한양대 수시 9개 전형 4칸(인원·자격·방법·최저), 성균관대 4개 전형 자격·인원, 인하대 9개 전형 자격과 방법·최저 6건, 연세대 2028 신설 2개 전형 인원·자격.

## 시드 반영(`scripts/build_univ_sample_seed.py`)
- `*_jeongsi*.json` → 정시 전형(round_type=JEONGSI, 이름 "정시 …(군)"), 일정, 학과 인원(기존 학과 행의 counts_by_type에 정시 열 병합, 기존 "합계"는 "수시 합계"로).
- 같은 이름 학과(서울대 "광역" 2개)는 원문 순서대로 짝지음.
- `*_fill.json` → fills(값 있으면 덮어씀), departments_add, schedules_replace(+archive_schedules).
- 결과: {"universities": 7, "documents": 19, "departments": 592, "admission_types": 136, "schedules": 315, "archive_schedules": 15, "prior_results": 0, "approved": 0, "verification_status_all": "NORMALIZED"}

## 운영 반영
feel2real-buildit PR #962(적재기 갱신·보관 지원) 병합·배포 후 관리자: load/seed → activate-all(2027, 2028) → knowledge/build → knowledge/reindex `ALL`.

## 남은 일
- 수시 이월 반영 최종 정시 인원(대학별 12월 말~1월 초 공고) 갱신.
- 탐구 변환표준점수표(수능 성적 발표 후 공지).
- 전년도 입시결과(경쟁률·충원) 미수집.

## 전국 확대 1차(경기·인천 8곳, 2026-11-02)
- 등록부: adiga.kr 서울 외 4년제 일반대학 166개(캠퍼스별) 확인, 그중 161개는 수시·정시 요강이 모두 올라와 있음. 경기·인천 대학부터 묶음별로 진행.
- 신규 6곳: 아주대(`ajou`), 가천대(`gachon`), 인천대(`inu`), 한양대학교(ERICA)(`hyerica`), 단국대(`dankook`, 죽전·천안 통합 요강 — 두 캠퍼스 파일 sha256 동일), 한국항공대(`kau`).
- 대학 전체로 다시 정리 2곳: 경기대(`kyonggi`, 수원+서울캠퍼스), 가톨릭대(`catholic`, 성심+성의+성신교정). 대학 이름이 `경기대학교(서울캠퍼스)`→`경기대학교`, `가톨릭대학교(서울)`→`가톨릭대학교`로 바뀌며, 적재 시 예전 서울 전용 항목은 authoritative 정리로 보관된다.
- 캠퍼스 규칙: 통합 요강 대학은 대학 전체 한 항목(학과의 단과대 앞에 캠퍼스 표기), 별도 요강 분교(ERICA 등)는 캠퍼스 표기 이름으로 따로 둔다.
- 빌더 보완:
  - 자료 제목에 대학 이름이 없으면 앞에 붙인다(예: `성균관대학교 2027학년도 수시모집 모집요강`). 대학끼리 같은 제목이 남으면 빌드를 멈춘다. 흔한 제목이 겹쳐 예전 적재기가 다른 대학 자료에 행을 연결하던 문제 대응(feel2real-buildit 적재기도 대학+제목으로 구분하도록 수정).
  - 일정 제목(`item (type_name)`)이 200자(DB 열 길이)를 넘으면 빌드를 멈춘다. 가천대 면접 일정 2건은 대상 모집단위 목록을 일자 칸으로 옮김.
- 검증: 모든 대학 학과별 인원 합 = 원문 합계·소계(불일치 0). 운영 재현 평가(예전 수집본 → 7개 → 43개 → 이번 시드, 또는 예전 수집본 → 7개 → 이번 시드) 213/213, 승인 행의 출처 자료 대학 불일치 0건.
- 결과: {"universities": 49, "documents": 102, "departments": 2245, "admission_types": 1000, "schedules": 2213, "archive_schedules": 15, "authoritative_universities": 49}

## 유튜브 전문가 해석 시드 반영(2026-11-02)
- `data/youtube/analyses.json`(영상 78개 분석 127건)을 시드 최상위 `youtube_knowledge`로 넣는다(빌더). feel2real-buildit 적재기가 지식 항목(sourceClass=YOUTUBE)으로 넣고, 상담 답변에서는 공식 정보와 분리된 "참고 — 유튜브 전문가 해석(공식 자료 아님)"으로만 쓴다.
- analyses.json usage_rules에 따라 OUTDATED 3건과 confidence=LOW(개인 배치에 쓰지 않음)는 제외 → 109건(2028 대상 101, 2027 6, 2026 2 — 2026은 적재기가 넣지 않음).
- 본문에 분류(전문가 해석·전략·전망·의견 갈림·공식 발표 해설), 대상 학년도, 주장·근거·상담 활용·주의, 공식 자료 대조, 출처 영상(채널·제목·게시일), 확인 수준(설명란·챕터 기반 복원, 발언 미확인, 신뢰도)을 적는다. 링크는 해당 구간 시작 시각(`&t=`)을 붙인다.

## 전국 확대 2차(경기 8곳, 2026-11-02)
- 신규: 중앙대학교(다빈치캠퍼스)(`caudavinci`, 서울 요강과 같은 통합 파일에서 다빈치 행만), 명지대학교(자연캠퍼스)(`mjunat`, 인문캠퍼스와 같은 통합 파일에서 자연 행만), 수원대(`suwon`, adiga 파일명은 "1p"지만 수시 88쪽·정시 64쪽 전체 요강), 한국공학대(`tukorea`), 용인대(`yongin`), 강남대(`kangnam`, 정시 파일명 "(안)"이나 본문에 시안 표기 없음 — notes), 한신대(`hanshin`, 수시 PDF가 글꼴 아웃라인이라 텍스트 추출 불가 → 쪽 이미지로 읽고 총괄표·전형별 표·요약표 3중 대조), 성결대(`sungkyul`).
- 빌더 보완(학과 병합):
  - 수시·정시 같은 이름 학과가 하나뿐이면 단과대 표기가 달라도 합친다(서울기독대 8개 학과가 정시 행으로 따로 들어가던 문제).
  - 한 대학·학년도에 같은 학과명이 남으면 단과대를 이름에 붙인다(서울대 `광역` → `광역(학부대학)`·`광역(공과대학)`; 적재기가 이름으로 한 행에 합쳐 한쪽 인원이 사라지던 문제). 그래도 겹치면 빌드 중단.
- 검증: 모든 대학 학과별 인원 합 = 원문 합계·소계(불일치 0). 운영 재현 평가(예전 수집본 → 7개 → 49개+유튜브 → 이번 시드) 245/245, 출처 자료 대학 불일치 0건.
- 결과: {"universities": 57, "documents": 118, "departments": 2483, "youtube_knowledge": 109, "admission_types": 1166, "schedules": 2527}
- 남은 일: `mju_2027_jeongsi.json` 일부 근거 쪽(수능 반영방법·학교폭력 감점표·전형료)이 인쇄 쪽 번호로 적혀 있어 PDF 쪽(+2)으로 고칠 것.
