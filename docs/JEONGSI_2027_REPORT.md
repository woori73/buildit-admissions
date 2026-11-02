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
