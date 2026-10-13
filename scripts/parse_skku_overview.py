# 성균관대 2027 수시모집요강 02. 모집인원 총괄표(9쪽, 전공×전형) 재파싱 — find_tables 기반
# 기존 실패 원인: 공백 생략 레이아웃의 텍스트 레이어 파싱. 표 격자 기준으로 해결.
import pymupdf, json, os

PDF = 'data/raw/pdfs/skku_2027_susi.pdf'
OUT = 'data/parsed/univ_sample/skku_2027_susi_overview.json'
TYPE_COLS = ['융합인재', '탐구인재', '기회균형', '성균인재', '성균인재-지역인재', '과학인재',
             '추천인재', '언어형', '수리형', '예체능특기자', '예체능실기우수자']

def num(s):
    s = (s or '').replace(',', '').replace('☆', '').strip()
    return int(s) if s.isdigit() else 0

doc = pymupdf.open(PDF)
raw = [[(c or '').replace('\n', '').strip() for c in r] for r in doc[8].find_tables().tables[0].extract()]

groups, depts, total_row = [], [], None
group = None
for r in raw[4:]:
    if r[0] == '합계':
        total_row = r
        break
    label = r[0] or r[1]
    if not label:
        continue
    if r[0] in ('사범대학', '전공예약') and r[1]:
        group = r[0]
        name, college = r[1], r[0]
    else:
        if r[0] in ('영상학과', '의상학과') and group:
            college = group
        else:
            college = None if r[0] in ('',) else (r[0] if r[1] else None)
            group = college or group
        name = r[1] if r[1] else r[0]
    vals = {t: num(r[2 + k]) for k, t in enumerate(TYPE_COLS)}
    vals['특성화고졸재직자(정원외)'] = num(r[14])
    row_sum = num(r[13])
    calc = sum(vals.values())
    if row_sum == 0 and vals['특성화고졸재직자(정원외)'] > 0:
        calc = vals['특성화고졸재직자(정원외)']  # 정원외 전용 행: 소계 열은 비어 있음
    assert calc == row_sum or (row_sum == 0 and calc == vals['특성화고졸재직자(정원외)']), \
        f'{name}: 행합 {calc} != 소계 {row_sum}'
    depts.append({'department': name.replace('†', ''), 'college_group': college,
                  'counts_by_type': vals, 'susi_total': row_sum})

tot = {t: num(total_row[2 + k]) for k, t in enumerate(TYPE_COLS)}
tot['특성화고졸재직자(정원외)'] = num(total_row[14])
agg = {t: sum(d['counts_by_type'][t] for d in depts) for t in tot}
assert agg == tot, f'열 합계 불일치: {agg} vs {tot}'
assert num(total_row[13]) == sum(tot[t] for t in TYPE_COLS) == 2191
assert tot['특성화고졸재직자(정원외)'] == 187

result = {
    'document': {
        'institution_name': '성균관대학교 입학처',
        'document_name': '2027학년도 수시모집 모집요강 02.모집인원 총괄표',
        'source_url': 'https://admission.skku.edu/admission/html/rolling/guide.html',
        'file_url': 'https://admission.skku.edu/upload/guide/20260813104526BBPE44.pdf',
        'applicable_academic_year': 2027, 'published_at': '2026-08-13',
        'extraction': 'pymupdf find_tables (PDF 표 격자 기준), 9쪽',
        'verification_status': 'NORMALIZED', 'approved': False,
        'exposure': 'HIDDEN (APPROVED-only search gate)',
        'verification': {
            'row_sum': f'{len(depts)}행 전부 행합=소계 열 일치(assert 통과)',
            'column_sum_vs_total': '12개 전형 컬럼 전부 합계행과 일치; 소계 2,191 + 정원외(특성화고졸재직자) 187 = 2,378 — 전형유형별 요약표와 재현',
            'subtype_reconciliation': '학생부종합 정원내 소계 = 329+589+28+196+3+155 = 1,300; 요약표의 1,487은 정원외 특성화고졸재직자 187 포함(1,300+187)',
            'note': '응용AI융합학부(AI융합운영 94/산업인공지능 93)는 전원이 정원외 특성화고졸재직자',
        },
    },
    'departments': depts,
    'column_totals': tot,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('rows', len(depts), 'grand', 2191 + 187)
