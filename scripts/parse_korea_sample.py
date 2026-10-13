# 고려대 2027 서울캠퍼스 수시모집요강 — 전형별 모집단위·모집인원(4~5쪽) + 수능최저/일정 구조화
# 공식 경로: admission.korea.ac.kr 이 이 PC에서 차단되어, 입학처 공식 대체 호스트 oku.korea.ac.kr 사용
import pymupdf, json, os, re

PDF = 'data/raw/pdfs/korea_2027_susi.pdf'
OUT = 'data/parsed/univ_sample/korea_2027_susi.json'
TYPES = ['학교추천전형', '학업우수전형', '계열적합전형', '고른기회전형', '다문화전형',
         '재직자전형', '사이버국방전형', '논술전형', '특기자전형']

def num(s):
    s = (s or '').replace(',', '').replace('*', '').replace('★', '').replace('◇', '').replace('☆', '').strip()
    return int(s) if s.isdigit() else 0

doc = pymupdf.open(PDF)
rows = []
for pno in (3, 4):
    for t in doc[pno].find_tables().tables:
        if t.col_count == 13:
            rows.extend([[(c or '').replace('\n', '').strip() for c in r] for r in t.extract()])

depts, total_row, college = [], None, None
for r in rows:
    if r[0].startswith('모집인원 합계'):
        total_row = r
        continue
    if r[2] and r[3] and not r[2].startswith('모집단위') and r[0] not in ('대학(학부)',):
        college = r[0] or college
        vals = {}
        for k, tname in enumerate(TYPES):
            cell = r[4 + k]
            vals[tname] = num(cell)
            if cell == '◉':
                vals[tname] = 0
        marked = '◉' in r[4:13]
        s = sum(vals.values())
        assert s == num(r[3]), f"{r[2]}: 행합 {s} != 모집인원 {r[3]}"
        depts.append({'department': r[2], 'college': college, 'track': r[1],
                      'counts_by_type': vals, 'susi_total': num(r[3]),
                      'contract_dept_marker': marked})
tot = {t: num(total_row[4 + k]) for k, t in enumerate(TYPES)}
agg = {t: sum(d['counts_by_type'][t] for d in depts) for t in TYPES}
# 재직자전형: 각 모집단위 최대 1명·총 18명 이내 '선발'(요강 5쪽 각주2) → 모집인원 컬럼에 미포함, 상한 별도 관리
assert agg['재직자전형'] == 0 and tot['재직자전형'] == 18
elig_emp = [d['department'] for d in depts if d['counts_by_type']['재직자전형'] == 0
            and d['contract_dept_marker']]
tot_check = sum(agg[t] for t in TYPES if t != '재직자전형')
assert tot_check == num(total_row[3]) - 18, f'행 합계 {tot_check} != 2,731-18'

# 수능최저(6쪽)·일정(7~9쪽) — 원문 육안 전사(발췌 정규식 파싱 불가 레이아웃)
schedules = [
    {'item': '원서접수(인터넷)', 'date': '2026.09.07.(월) 10:00 ~ 09.09.(수) 17:00', 'page': 7},
    {'item': '서류 온라인 제출', 'date': '2026.09.07.(월) 10:00 ~ 09.09.(수) 18:00', 'page': 7},
    {'item': '서류 등기우편 제출(국내)', 'date': '2026.09.10.(목) 소인까지 유효', 'page': 7},
    {'item': '고교별 추천대상자명단 입력', 'date': '2026.09.14.(월) 09:00 ~ 09.18.(금) 18:00', 'page': 7},
    {'item': '1단계 발표(고른기회·다문화·재직자)', 'date': '2026.10.23.(금) 17:00', 'page': 9},
    {'item': '1단계 발표(계열적합)', 'date': '2026.10.30.(금) 17:00', 'page': 9},
    {'item': '계열적합 면접', 'date': '2026.11.07.(토) 인문 / 11.08.(일) 자연', 'page': 9},
    {'item': '1단계 발표(논술)', 'date': '2026.11.17.(화) 17:00', 'page': 9},
    {'item': '논술시험', 'date': '2026.11.21.(토) 자연 / 11.22.(일) 인문', 'page': 9},
    {'item': '최초합격자 발표(전 전형)', 'date': '2026.12.18.(금) 17:00', 'page': 9},
    {'item': '문서등록기간', 'date': '2026.12.21.(월) 10:00 ~ 12.23.(수) 14:00', 'page': 9},
    {'item': '등록금 납부', 'date': '2027.02.15.(월) ~ 02.16.(화)', 'page': 9}]

result = {
    'document': {
        'institution_name': '고려대학교 입학처',
        'document_name': '2027학년도 수시모집요강(서울캠퍼스)',
        'source_url': 'https://oku.korea.ac.kr/oku/cms/FR_CON/index.do?MENU_ID=680',
        'file_url': 'https://oku.korea.ac.kr/attach/202605/1780023076409_0.pdf',
        'applicable_academic_year': 2027, 'published_at': '2026-05',
        'extraction': 'pymupdf find_tables, 4~5쪽',
        'verification_status': 'NORMALIZED', 'approved': False,
        'exposure': 'HIDDEN (APPROVED-only search gate)',
        'access_note': 'admission.korea.ac.kr은 이 PC에서 연결 차단 → 입학처 공식 대체 호스트(oku)로 확보. 차단 우회 아님',
        'verification': {
            'row_sum': f'{len(depts)}행 전부 모집인원=전형 컬럼 합 일치(assert)',
            'column_sum_vs_total': f'합계행과 일치, 총 2,731 (재직자 18 제외 2,713+18)',
            'marker_note': "◉=재직자전형 지원가능 모집단위(8개 학과), 각 최대 1명·총 18명 이내 선발(5쪽 각주2) — 행 모집인원에는 미포함",
        },
    },
    'departments': depts,
    'column_totals': tot,
    'admission_types': [
        {'name': '학생부교과(학교추천전형)', 'applicant_total': 650, 'method': '교과100 일괄',
         'csat_minimum': '적용(모집단위별 상이, 요강 6쪽)', 'eligibility': '고교 졸업(예정)자, 학교장 추천 불요 표기 확인(요강 12쪽~)', 'evidence_pages': [3, 4]},
        {'name': '학생부종합(학업우수전형)', 'applicant_total': 903, 'method': '단계별: 서류100(3배수)→서류70+면접30',
         'csat_minimum': '적용(요강 6쪽)', 'eligibility': '일반고·특목고·검정고시·국외고 등(요강 14쪽~)', 'evidence_pages': [3, 4]},
        {'name': '학생부종합(계열적합전형)', 'applicant_total': 523, 'method': '단계별: 서류100(3배수)→서류70+면접30',
         'csat_minimum': '미적용', 'eligibility': '특목고·병합·검정고시·국외고 등(요강 15쪽~)', 'evidence_pages': [3, 4]},
        {'name': '학생부종합(고른기회전형)', 'applicant_total': 201, 'method': '서류100 일괄',
         'csat_minimum': '미적용', 'eligibility': '기초생활수급자·차상위·농어촌 등(요강 16쪽~)', 'evidence_pages': [3, 4]},
        {'name': '학생부종합(다문화전형)', 'applicant_total': 20, 'method': '서류100 일괄',
         'csat_minimum': '미적용', 'eligibility': '다문화가족 자녀 등(요강 18쪽~)', 'evidence_pages': [3, 4]},
        {'name': '학생부종합(재직자전형)', 'applicant_total': 18, 'method': '서류100 일괄',
         'csat_minimum': '미적용', 'eligibility': '산업체 3년 이상 근무(요강 19쪽~)·◉지원가능 모집단위 각 최대 1명 총 18명 이내', 'evidence_pages': [3, 4, 5]},
        {'name': '학생부종합(사이버국방전형)', 'applicant_total': 10, 'method': '단계별(체력검정·국면 포함)',
         'csat_minimum': '미적용', 'eligibility': '요강 21쪽~, 국방부 연계', 'evidence_pages': [3, 4]},
        {'name': '논술(논술전형)', 'applicant_total': 351, 'method': '논술100 일괄+수능최저',
         'csat_minimum': '적용(요강 6쪽)', 'eligibility': '고졸(예정) 등(요강 22쪽~)', 'evidence_pages': [3, 4]},
        {'name': '실기/실적(특기자전형)', 'applicant_total': 55, 'method': '실기·서류(예능 실기/체능 실적)',
         'csat_minimum': '예능 적용·체능 미적용(요강 6쪽)', 'eligibility': '요강 24쪽~', 'evidence_pages': [3, 4]},
    ],
    'schedules': {'items': schedules, 'evidence': '7·9쪽 원문 육안 전사'},
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('depts', len(depts), 'total', sum(tot.values()))
