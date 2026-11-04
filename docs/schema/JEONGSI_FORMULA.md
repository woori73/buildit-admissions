# 정시 수능 환산 계산식 형식 (jeongsi_formula/v1)

대학 모집요강의 **수능 반영 방법**(반영비율, 활용지표, 영어·한국사 등급 점수, 가산점)을 계산할 수 있는 형태로 적는다.
계산·검증은 `scripts/jeongsi_formula.py`가 한다. 기준 예시: `data/parsed/jeongsi_formula/uos_2027_jeongsi_formula.json`.

## 원칙
- 근거는 그 대학이 공개한 2027학년도 정시 모집요강 원문뿐이다. 원문 숫자를 그대로 옮기고, 원문에 없는 값은 만들지 않는다.
- 원문을 해석해야 계산식이 되는 부분(예: "1개 과목 반영점수"가 숫자로 없음)은 계산식에 넣되 `uncertain`에 한 줄로 적는다.
- 수식 언어로 정확히 옮길 수 없는 전형은 비슷하게 만들지 않고 `not_covered`에 사유를 적는다.
- 수능 점수만 계산한다. 학생부·실기·면접·학교폭력 감점은 넣지 않고, 필요하면 `not_in_csat_score_text`에 원문을 적는다.

## 파일
`data/parsed/jeongsi_formula/{university_key}_2027_jeongsi_formula.json` (university_key는 `data/parsed/univ_sample/{key}_2027_jeongsi.json`과 같다)

| 칸 | 내용 |
|---|---|
| schema | `jeongsi_formula/v1` |
| university_key, university_name, academic_year | 2027 |
| documents[] | document_key, document_name, institution_name, source_page_url(게시 페이지), file_url(파일), file_sha256, page_count |
| formulas[] | 아래 |
| not_covered | {전형명: 사유} — 계산식이 없는 2027 정시 전형 |
| gaps[] | 원문을 받지 못한 경우 {item, reason, url} (이때 formulas는 비워도 된다) |
| notes[] | 그 밖의 메모 |

### formulas[] 한 항목
| 칸 | 내용 |
|---|---|
| formula_id | `{key}_{짧은이름}` |
| label | 원문 계열·유형 이름(예: "인문계열Ⅰ", "A형/B형 중 높은 점수") |
| document_key | documents의 키 |
| applies_to.type_names | 2027 정시 자료의 **전형명 그대로**(검증기가 대조) |
| applies_to.department_names | 2027 정시 자료의 **모집단위명 그대로**. 전형 전체에 같으면 생략 가능 |
| applies_to.unit_scope_text | 원문의 해당 모집단위 문구 |
| csat_points | 원문 수능 만점(가산점 제외). 원문에 없으면 null |
| perfect_score_expected | 만점 입력(아래)에서 나와야 할 값. 원문 수치로 정해질 때만 적는다. 표준점수를 그대로 곱하는 식처럼 만점이 고정되지 않으면 null. 만점 입력은 등급을 1로 넣으므로, 한국사처럼 등급표로 더하는 가산점은 1등급 값이 포함된다(예: 수능 1,000 + 한국사 1등급 가산 5 = 1,005). 선택과목·탐구 과목에 따른 가산은 포함하지 않는다 |
| tables | 등급표 {"ENG": {"1": 100, …, "9": 0}, "HIST": {...}}. 영어·한국사·제2외국어 표는 1~9등급을 모두 적는다. 감점은 음수로 |
| expression | 계산식(아래 수식 언어) |
| rounding_text | 원문의 소수점 처리 문구(없으면 null). 계산식에 round()/trunc()로 반영 |
| eligibility_text | 응시 영역·지정 과목 원문 |
| not_in_csat_score_text | 수능 외 요소 원문(없으면 null) |
| evidence_pages | 근거 쪽(PDF 쪽, 1부터) |
| raw_text | 근거 원문 발췌(숫자는 원문 그대로) |
| examples[] | 원문에 계산 예시가 있으면 {inputs, expected, page, tolerance} — 검증기가 계산해서 맞춰 본다 |
| uncertain[] | 해석이 들어간 부분 |

## 수식 언어
숫자, 변수, `+ - * /`, 괄호, 비교(`== != < <= > >=`), `and or not`, 그리고 함수:
`max(...)`, `min(...)`, `sum(...)`, `top_sum(k, a, b, …)`(큰 값 k개 합), `cond(조건, 참, 거짓)`, `table('표이름', 값)`,
`round(x, 자릿수)`(반올림), `trunc(x, 자릿수)`(버림). 비교·논리식은 참 1, 거짓 0.

### 변수
| 변수 | 뜻 |
|---|---|
| KOR_STD, KOR_PCT, KOR_GRD, KOR_STD_MAX | 국어 표준점수·백분위·등급·전국 최고 표준점수 |
| MATH_STD, MATH_PCT, MATH_GRD, MATH_STD_MAX | 수학 같은 항목 |
| KOR_SEL_HW, KOR_SEL_EM | 국어 선택 화법과 작문 / 언어와 매체면 1 |
| MATH_SEL_PROB, MATH_SEL_CALC, MATH_SEL_GEOM | 수학 선택 확률과 통계 / 미적분 / 기하면 1 |
| ENG_GRD, HIST_GRD | 영어·한국사 등급 |
| FL_GRD, FL_TAKEN | 제2외국어/한문 등급, 응시하면 1 |
| INQ1_STD, INQ1_PCT, INQ1_GRD, INQ1_STD_MAX | 탐구1 표준점수·백분위·등급·전국 최고 표준점수 |
| INQ1_CONV, INQ1_CONV_MAX | 탐구1 대학 변환표준점수와 그 최고점(대학 발표 표) |
| INQ1_SOC, INQ1_SCI, INQ1_VOC, INQ1_SCI2 | 탐구1이 사회 / 과학 / 직업 / 과학Ⅱ면 1 |
| INQ2_… | 탐구2 같은 항목 |

`*_STD_MAX`와 `*_CONV*`는 수능 성적 발표(평가원 채점결과) 또는 대학 변환표준점수 발표 뒤에 정해진다. 검증기는 이 값을 `pending_inputs`로 따로 표시한다.
"상위 1과목"처럼 고르는 규칙은 `max(INQ1_CONV, INQ2_CONV)`처럼 적는다.

## 만점 입력
표준점수 = 전국 최고점, 백분위 100, 등급 1, 변환표준점수 = 최고점, 선택 과목 표시는 모두 0(가산점 없음).
`perfect_score_expected`가 있으면 이 입력의 결과가 그 값과 같아야 한다.

## 검증
```
python3 scripts/jeongsi_formula.py data/parsed/jeongsi_formula/{key}_2027_jeongsi_formula.json
python3 scripts/jeongsi_formula.py --all
```
오류: 문법, 모르는 변수, 표 누락·등급 누락, 2027 자료에 없는 전형명·모집단위명, 만점 불일치, 원문 예시 불일치.
경고: 계산식이 없는 정시 전형(not_covered에 사유가 없을 때), 쓰지 않는 표.
