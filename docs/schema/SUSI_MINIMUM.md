# 수시 수능최저학력기준 형식 (susi_minimum/v1)

대학 수시 모집요강의 **수능최저학력기준**을 조건식으로 적는다. 학생 등급을 넣으면 충족·미충족을 판정한다.
조건식은 정시 계산식과 같은 수식 언어([JEONGSI_FORMULA.md](JEONGSI_FORMULA.md))이고, 참(1)이면 충족이다.
검증·판정: `scripts/susi_minimum.py`.

## 원칙
- 근거는 그 대학이 공개한 2027학년도 수시 모집요강 원문뿐이다. 우리 2027 자료의 요약 문장은 찾는 실마리로만 쓴다.
- 원문 숫자·영역·지정 과목을 그대로 옮긴다. 원문에 없는 규칙은 만들지 않는다.
- 해석이 들어간 부분은 `uncertain`에, 해석에 따라 판정이 달라질 수 있으면 `needs_review`에 적는다.
- 판정은 "등급 기준 충족 여부"까지다. 합격 여부·가능성은 말하지 않는다.

## 파일
`data/parsed/susi_minimum/{university_key}_2027_susi_minimum.json` (university_key = 2027 시드 대학 코드 소문자)

| 칸 | 내용 |
|---|---|
| schema | `susi_minimum/v1` |
| university_key, university_name, academic_year | 2027 |
| documents[] | document_key, document_name, institution_name, source_page_url, file_url, file_sha256, page_count |
| rules[] | 아래 |
| no_minimum | {전형명: 원문 근거 문구(쪽)} — 수능최저가 없는 전형 |
| not_covered | {전형명: 사유} — 정리하지 못한 전형(원문 미확보 등) |
| gaps[] | 원문을 받지 못한 경우 {item, reason, url} |
| notes[] | 그 밖의 메모 |

### rules[] 한 항목
| 칸 | 내용 |
|---|---|
| rule_id | `{key}_{짧은이름}` |
| label | 원문 표현(예: "인문·자연계열(의예과 제외)") |
| document_key | documents의 키 |
| applies_to.type_names | 2027 수시 전형명 그대로(검증기가 대조) |
| applies_to.department_names | 모집단위별로 다르면 모집단위명 그대로. 전형 전체면 생략 |
| applies_to.unit_scope_text | 원문의 해당 모집단위 문구 |
| condition | 조건식. 참이면 충족 |
| required_areas_text | 응시 필수 영역·지정 과목 원문 |
| raw_text | 근거 원문 발췌(숫자 그대로) |
| evidence_pages | 근거 쪽(PDF 쪽) |
| examples[] | 원문에 판정 예시가 있으면 {inputs, expected_met, page} |
| uncertain[], needs_review | 정시 계산식과 같은 뜻 |
| sanity_best / sanity_worst | 검증기 기본 입력(아래)이 이 규칙에 맞지 않을 때 덮어쓸 값 |

### 규칙 적용 순서
한 전형에 "전체(의예과 제외)" 규칙과 "의예과" 규칙이 함께 있으면: `department_names`가 있는 규칙이 그 모집단위에 우선한다.
판정할 때 모집단위가 어떤 규칙의 `department_names`에 들어 있으면 같은 전형의 전형 전체 규칙(`department_names` 없음)은 쓰지 않는다.
모집단위를 모르면 그 전형의 규칙을 모두 보여 준다.

## 조건식 쓰는 법
변수: `KOR_GRD, MATH_GRD, ENG_GRD, HIST_GRD, INQ1_GRD, INQ2_GRD, FL_GRD`, 선택 표시
`KOR_SEL_HW, KOR_SEL_EM, MATH_SEL_PROB, MATH_SEL_CALC, MATH_SEL_GEOM, INQ1_SOC, INQ1_SCI, INQ1_VOC, INQ1_SCI2, INQ2_…, FL_TAKEN`.

| 원문 | 조건식 |
|---|---|
| 국·수·영·탐(1과목) 중 3개 영역 합 6 이내 | `low_sum(3, KOR_GRD, MATH_GRD, ENG_GRD, min(INQ1_GRD, INQ2_GRD)) <= 6` |
| 탐구 2과목 평균(소수점 절사) | `trunc((INQ1_GRD + INQ2_GRD) / 2)` 를 탐구 등급으로 |
| 탐구 2과목 평균(소수점 그대로) | `(INQ1_GRD + INQ2_GRD) / 2` |
| 수학 포함 | `MATH_GRD + low_sum(2, KOR_GRD, ENG_GRD, 탐구) <= 6` |
| 2개 영역 각 2등급 이내 | `cond(KOR_GRD <= 2, 1, 0) + cond(MATH_GRD <= 2, 1, 0) + … >= 2` |
| 과학탐구 응시 필수 | `INQ1_SCI == 1 and INQ2_SCI == 1 and (…)` |
| 미적분·기하 응시 시에만 수학 인정 | 수학 자리에 `cond(MATH_SEL_CALC + MATH_SEL_GEOM >= 1, MATH_GRD, 9)` |
| 한국사 4등급 이내 추가 | `(…) and HIST_GRD <= 4` |
| 제2외국어/한문을 탐구 1과목으로 대체 가능 | 탐구 자리에 `min(INQ1_GRD, INQ2_GRD, cond(FL_TAKEN == 1, FL_GRD, 9))` |

## 검증
- 모든 등급 1·선택 표시 모두 1 → 충족이어야 하고, 모든 등급 9 → 미충족이어야 한다(규칙에 맞지 않으면 sanity_best/worst로 덮어쓴다).
- 전형명은 2027 시드(`data/seed/ipsi_seed_univ_sample.json`)의 그 대학 수시 전형명과 같아야 한다.
- 시드의 수시 전형마다 rules·no_minimum·not_covered 중 어디에도 없으면 경고.

```
python3 scripts/susi_minimum.py data/parsed/susi_minimum/{key}_2027_susi_minimum.json
python3 scripts/susi_minimum.py --all
```
