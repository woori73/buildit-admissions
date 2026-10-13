# 연세대 2027 수시모집요강 Ⅱ부(전형별 모집단위·모집인원) 재파싱 — find_tables 기반
# 기존 실패 원인: 모집인원* 컬럼은 수시+정시 합산 → 행합 불일치. 수시 8개 전형 컬럼만 사용.
import pymupdf, json, os

PDF = 'data/raw/pdfs/yonsei_2027_susi.pdf'
OUT = 'data/parsed/univ_sample/yonsei_2027_susi_part2.json'
COLS = ['추천형', '활동우수형', '국제형_국내고', '국제형_해외고', '국제인재', '기회균형', '논술', '특기자_체육']

def num(s):
    s = (s or '').replace(',', '').replace('†', '').strip()
    return int(s) if s.isdigit() else None

doc = pymupdf.open(PDF)
rows = []
for pno in (10, 11):
    for t in doc[pno].find_tables().tables:
        if t.col_count == 13:
            rows.extend([[ (c or '').replace('\n', '').strip() for c in r ] for r in t.extract()])

depts, total_row, i = [], None, 4
while i < len(rows):
    r = rows[i]
    if r[0] == '대학' and r[1] == '모집단위':
        i += 4
        continue
    if r[0] == '합계':
        total_row = r
        break
    vals = [num(r[4 + k]) or 0 for k in range(8)]
    depts.append({
        'college': r[0] or depts[-1]['college'] if (r[0] or depts) else None,
        'department': r[1] or r[0], 'track': r[2],
        'plan_total_susi_plus_regular_star': num(r[3]),
        'susi_by_type': dict(zip(COLS, vals)), 'susi_sum': sum(vals),
        'out_of_quota_special_ed': r[12] == '○',
    })
    i += 1

agg = {c: sum(d['susi_by_type'][c] for d in depts) for c in COLS}
tot = {c: num(total_row[4 + k]) for k, c in enumerate(COLS)}
assert agg == tot, f'컬럼 합계 불일치: {agg} vs {tot}'

result = {
    'document': {
        'institution_name': '연세대학교 입학처',
        'document_name': '2027학년도 수시모집 모집요강 Ⅱ부(전형별 모집단위·모집인원)',
        'source_url': 'https://admission.yonsei.ac.kr/seoul/admission/html/rolling/guide.asp',
        'file_url': 'https://admission.yonsei.ac.kr/seoul/upload/guide/20260529204109T8NZNJ.PDF',
        'applicable_academic_year': 2027, 'published_at': '2026-05-29',
        'extraction': 'pymupdf find_tables (PDF 표 격자 기준), 11~12쪽',
        'verification_status': 'NORMALIZED', 'approved': False,
        'exposure': 'HIDDEN (APPROVED-only search gate)',
        'verification': {
            'column_sum_vs_total_row': '8개 전형 컬럼 전부 일치 (assert 통과)',
            'cross_check_vs_part1_summary': '추천 512-25계약=487, 활동 766-52=714, 기회균형 195-5=190, 논술 288-16=272, 국제형 175+79=254, 국제인재 120, 체육 38, 특수교육 13 — Ⅰ부 요약·시행계획과 일치',
            'note': '모집인원*는 수시+정시 합산(각주) → 수시 인원은 susi_sum 사용. 정시 세부는 2026.9.1. 발표 정시모집요강 확인 필요',
        },
    },
    'departments': depts,
    'column_totals': agg,
    'international_decomposition': {
        '국제형_국내고_175': {'아시아학전공': 20, '융합인문사회과학부(HASS)': 110, '융합과학공학부(ISE)': 45},
        '국제형_해외고_79': {'언더우드학부(인문·사회)': 29, '언더우드학부(생명과학공학)': 5,
                            '융합인문사회과학부(HASS)': 20, '융합과학공학부(ISE)': 15, '글로벌인재학부': 10},
        '국제인재_120': {'언더우드학부(인문·사회)': 110, '언더우드학부(생명과학공학)': 10},
    },
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('rows', len(depts), 'totals', json.dumps(agg, ensure_ascii=False))
