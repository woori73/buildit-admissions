#!/usr/bin/env python3
"""저장된 파싱 산출물의 필드만 읽어 분석용 디제스트를 만든다(재파싱 없음)."""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'data', 'parsed', 'univ_sample')
out = io.open(os.path.join(ROOT, 'tmp_digest.txt'), 'w', encoding='utf-8')

def w(*a):
    print(*a, file=out)

def load(n):
    if not n.endswith('.json'):
        n += '.json'
    return json.load(io.open(os.path.join(S, n), encoding='utf-8'))

def fmt(v, maxlen=160):
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    if s and len(s) > maxlen:
        s = s[:maxlen] + '…'
    return s

for fn in sorted(os.listdir(S)):
    if not fn.endswith('.json'):
        continue
    p = load(fn[:-5])
    w('=' * 90)
    w('FILE', fn)
    doc = p.get('document', {})
    w('  academic_year:', doc.get('applicable_academic_year', p.get('academic_year')))
    w('  institution:', doc.get('institution_name', p.get('university')))
    w('  doc_name:', fmt(doc.get('document_name', p.get('doc_type')), 80))
    w('  source_url:', fmt(doc.get('source_url', p.get('source_url')), 100))
    w('  published:', doc.get('published_at'))
    w('  top keys:', list(p.keys()))
    if 'n_departments' in p:
        w('  n_departments:', p['n_departments'])
    if 'totals' in p:
        w('  totals:', fmt(p['totals'], 400))
    depts = p.get('departments', [])
    if depts:
        w('  departments:', len(depts))
        d0 = depts[0]
        w('   dept keys:', list(d0.keys()))
        for d in depts[:3]:
            w('   ex:', fmt({k: v for k, v in d.items()}, 220))
    at = p.get('admission_types', [])
    if at:
        w('  admission_types:', len(at))
        for t in at:
            w('   -', fmt(t, 500))
    sc = p.get('schedules', p.get('schedules_sample', {}))
    if sc:
        items = sc.get('items', []) if isinstance(sc, dict) else sc
        w('  schedules:', len(items))
        for it in items:
            w('   -', fmt(it, 200))
    for k in ('notes', 'type_notes', 'column_totals', 'summary_2028',
              'out_of_quota_additional', 'susi_by_type_notes', 'gaps'):
        if k in p:
            w(' ', k + ':', fmt(p[k], 900))
    if 'schedules_sample' in p and isinstance(p['schedules_sample'], dict):
        w('  schedules_sample.type:', p['schedules_sample'].get('type'))

# 수집 분류·시드
for extra in ['../collection_classification.json', '../../seed/ipsi_seed_univ_sample.json']:
    fp = os.path.normpath(os.path.join(S, extra))
    if os.path.exists(fp):
        j = json.load(io.open(fp, encoding='utf-8'))
        w('=' * 90)
        w('FILE', os.path.basename(fp))
        if 'counts' in j:
            w('  counts:', fmt(j['counts'], 300))
        if 'gate' in j:
            w('  gate:', j['gate'])
        if 'items' in j:
            from collections import Counter
            c = Counter(i.get('category') for i in j['items'])
            w('  classification:', fmt(dict(c), 400))
        if 'gaps' in j:
            w('  gaps:', fmt(j['gaps'], 1500))
out.close()
print('ok')
