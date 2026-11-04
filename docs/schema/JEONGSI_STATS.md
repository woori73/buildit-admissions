# 정시 환산용 발표 값 — csat_std_max/v1 · conversion_score/v1

정시 계산식(JEONGSI_FORMULA.md)에서 수능 성적 발표 뒤에야 정해지는 값을 원문 그대로 적는다.

| 계산식 변수 | 값 | 원문 | 발표 시기 |
|---|---|---|---|
| `KOR_STD_MAX`, `MATH_STD_MAX` | 영역 표준점수 최고점 | 한국교육과정평가원 수능 채점 결과 | 성적 통지 전날 보도자료(2027 수능: 2026-12-10 전후) |
| `INQ1_STD_MAX`, `INQ2_STD_MAX` | 학생이 응시한 탐구 과목의 표준점수 최고점 | 같은 자료의 과목별 값 | 같음 |
| `INQ1_CONV`, `INQ2_CONV` | 학생 탐구 백분위에 해당하는 대학 변환표준점수 | 대학 입학처 공지(변환표준점수표) | 대학별, 정시 원서 접수 전 |
| `INQ1_CONV_MAX`, `INQ2_CONV_MAX` | 같은 표의 백분위 100 점수 | 같음 | 같음 |

원칙
- 원문에 적힌 숫자만 적는다. 발표 전이면 `null`로 두고, 일부만 확인되면 적재하지 않는다.
- 과목명은 원문 표기 그대로 적는다(예: `물리학Ⅰ`). 학생 입력의 과목명과 글자 그대로 맞춰 찾는다.
- 대학 표가 계열(사회/과학/직업탐구)보다 더 잘게 나뉘면(모집단위·전형별 다른 표 등) 표를 만들지 말고 `gaps`에 적는다.

## csat_std_max/v1
파일: `data/parsed/jeongsi_stats/csat_std_max_{학년도}.json`
```json
{
  "schema": "csat_std_max/v1",
  "academic_year": 2027,
  "source": {"institution_name": "한국교육과정평가원", "document_name": "…채점 결과…", "file_url": "https://…", "published_at": "2026-12-10"},
  "evidence_pages": [3, 4],
  "areas": {"KOR": null, "MATH": null},
  "inquiry": [{"subject": "생활과 윤리", "track": "SOC", "std_max": null}]
}
```
- `track`: `SOC`(사회탐구) · `SCI`(과학탐구) · `VOC`(직업탐구). 계산식의 `INQ*_SOC/SCI/VOC` 표시와 같은 구분
- 검증: KOR·MATH 항목 필수, 값 0 초과 200 이하, 과목 중복 금지. 모든 값이 있어야 `published`

## conversion_score/v1
파일: `data/parsed/jeongsi_stats/{university_key}_{학년도}_conversion.json` (`university_key`는 계산식 파일과 같음)
```json
{
  "schema": "conversion_score/v1",
  "university_key": "yonsei",
  "university_name": "연세대학교",
  "academic_year": 2027,
  "source": {"institution_name": "연세대학교 입학처", "document_name": "…", "source_page_url": "https://…"},
  "tables": [{"track": "SOC", "label": "사회탐구", "scores": {"100": 0, "99": 0, "…": 0, "0": 0}, "evidence_pages": [1], "note": null}],
  "gaps": []
}
```
- `scores`: 백분위 0~100 101칸 모두. 백분위가 낮을수록 점수가 같거나 낮아야 한다(검증)
- 같은 계열 표는 하나만
- 경고: 그 대학 계산식이 `INQ*_CONV`를 쓰지 않으면 알림

## 시드
`python3 scripts/build_jeongsi_stats_seed.py` → `data/seed/jeongsi_stats_2027/ipsi_seed_jeongsi_stats_2027.json`
- `csat_std_max`: 행 하나가 과목 하나(`subject_key` = `KOR` · `MATH` · `INQ:{과목명}`)
- `conversion_scores`: 행 하나가 대학·계열 표 하나(`scores` 101칸)
- 근거 자료 키: 평가원 `doc_kice_{학년도}_csat_scores`, 대학 `doc_{코드}_{학년도}_jeongsi_conversion`
