#!/usr/bin/env python3
"""저장된 departments 행에서 유사 학과 교차 비교 행을 추출한다(재파싱 없음)."""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'data', 'parsed', 'univ_sample')
out = io.open(os.path.join(ROOT, 'tmp_compare.txt'), 'w', encoding='utf-8')

def load(n):
    if not n.endswith('.json'):
        n += '.json'
    return json.load(io.open(os.path.join(S, n), encoding='utf-8'))

KEYS = ['컴퓨터', '경영', '경제', '의예', ' 간호', '수학교육', '전기', '반도체',
        '화학', '법학', '국어국문', '영문', '데이터', '신규', '자율전공', '자유전공', '의류']

def scan(label, depts, total_fn, types_fn):
    print('#### ' + label, file=out)
    for d in depts:
        name = d.get('department', '')
        if any(k.strip() in name for k in KEYS):
            print('  -', name, '| total=', total_fn(d), '|', json.dumps(types_fn(d), ensure_ascii=False), file=out)

snu = load('snu_2027_susi')
scan('SNU(서울대)', snu['departments'], lambda d: d['total'],
     lambda d: {k: v for k, v in d.items() if k not in ('department', 'total')})

yp = load('yonsei_2027_susi_part2')
scan('YONSEI(연세대, 요강 Ⅱ부)', yp['departments'], lambda d: d['susi_sum'],
     lambda d: dict(d['susi_by_type'], **{'수시합': d['susi_sum'], '계획총계*': d['plan_total_susi_plus_regular_star']}))

sk = load('skku_2027_susi_overview')
scan('SKKU(성균관대)', sk['departments'], lambda d: d['susi_total'], lambda d: d['counts_by_type'])

ku = load('korea_2027_susi')
scan('KOREA(고려대)', ku['departments'], lambda d: d['susi_total'], lambda d: d['counts_by_type'])

hy = load('hanyang_2027_susi')
scan('HANYANG(한양대)', hy['departments'], lambda d: d['susi_sum'], lambda d: d['by_type'])

kh = load('khu_2027_susi')
scan('KHU(경희대)', kh['departments'], lambda d: sum(d['by_type'].values()), lambda d: d['by_type'])

inh = load('inha_2027_susi')
scan('INHA(인하대)', inh['departments'], lambda d: d['susi_sum'], lambda d: d['by_type'])

# 대학별 수시 총계·전형 구성 비율(계산된 비교 T1)
print('\n####totals summary####', file=out)
rows = [
    ('SNU', 414 + 1169 + 140, {'지역균형': 414, '일반전형': 1169, '기회균형': 140}),
    ('YONSEI(요강Ⅱ부)', sum(yp['column_totals'].values()), yp['column_totals']),
    ('SKKU(총괄표)', sum(sk['column_totals'].values()), sk['column_totals']),
    ('KOREA', sum(ku['column_totals'].values()), ku['column_totals']),
    ('HANYANG(정원내)', hy['totals']['susi_in_quota'], hy['totals']['by_type_in_quota']),
    ('KHU', kh['totals']['grand_total'], kh['totals']),
    ('INHA', inh['totals']['grand_total'], inh['totals']),
]
for name, tot, by in rows:
    by = {k: v for k, v in by.items() if isinstance(v, int) and k not in ('grand_total', 'check')}
    print(f'{name}: 총 {tot:,}', file=out)
    for k, v in sorted(by.items(), key=lambda x: -x[1]):
        print(f'   {k}: {v:,} ({v/tot*100:.1f}%)', file=out)
out.close()
print('ok')
