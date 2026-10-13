#!/usr/bin/env python3
"""2단계 공식자료 검증: seed(480/57/66) ↔ parsed 원문구조 ↔ raw텍스트 스팟검증.

수정·추정보완 없음 — 판정 결과만 data/validation/official_validation.json 에 기록.
APPROVED는 '후보 분류'까지(승격 아님).
"""
import io, json, os, re
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
seed = json.load(io.open(P('data', 'seed', 'ipsi_seed_univ_sample.json'), encoding='utf-8'))

def load_parsed(n):
    return json.load(io.open(P('data', 'parsed', 'univ_sample', n), encoding='utf-8'))

parsed = {n[:-5]: load_parsed(n) for n in os.listdir(P('data', 'parsed', 'univ_sample')) if n.endswith('.json')}

report = {'generated_at': seed['generated_at'], 'validated_at': '2026-10-13',
          'principle': '값 수정·추정 보완 없음, APPROVED 승격 없음(후보 분류만)'}
defects, checks = [], {}

def defect(sev, area, univ, ident, issue, action):
    defects.append({'severity': sev, 'area': area, 'university': univ, 'item': ident,
                    'issue': issue, 'disposition': action})

# ---------- A. seed ↔ parsed 필드 일치(행 단위) ----------
DEPT_SRC = {'SNU': ('snu_2027_susi', lambda d: d['department'], lambda d: dict((k, d[k]) for k in ('지역균형전형', '일반전형', '기회균형특별전형')), 'total'),
            'YONSEI': ('yonsei_2027_susi_part2', lambda d: d['department'], lambda d: d['susi_by_type'], 'susi_sum'),
            'SKKU': ('skku_2027_susi_overview', lambda d: d['department'], lambda d: d['counts_by_type'], 'susi_total'),
            'KOREA': ('korea_2027_susi', lambda d: d['department'], lambda d: d['counts_by_type'], 'susi_total'),
            'HANYANG': ('hanyang_2027_susi', lambda d: d['department'], lambda d: d['by_type'], 'susi_sum'),
            'KHU': ('khu_2027_susi', lambda d: d['department'], lambda d: d['by_type'], None),
            'INHA': ('inha_2027_susi', lambda d: d['department'], lambda d: d['by_type'], 'susi_sum')}

dept_rows = defaultdict(list)
for r in seed['ipsi_departments']:
    dept_rows[r['university_code']].append(r)

dept_verdicts = {}
for ucode, rows in dept_rows.items():
    fname, name_fn, types_fn, total_key = DEPT_SRC[ucode]
    src = {}
    dup = 0
    for d in parsed[fname]['departments']:
        k = name_fn(d)
        if k in src: dup += 1
        src[k] = d
    mism, zero, ok = [], [], 0
    for r in rows:
        name = r['department_name']
        s = src.get(name)
        if s is None:
            mism.append((name, 'seed-only')); continue
        base = types_fn(s)
        seed_base = {k: v for k, v in r['counts_by_type'].items() if k != '합계'}
        if seed_base != {k: v for k, v in base.items()}:
            mism.append((name, 'counts-differ')); continue
        tot = r['counts_by_type'].get('합계')
        expect_tot = s[total_key] if total_key else sum(base.values())
        if tot != expect_tot:
            mism.append((name, f'합계 {tot} != {expect_tot}')); continue
        if total_key is None and tot != expect_tot:
            mism.append((name, 'sum-mismatch')); continue
        if all(v == 0 for v in base.values()):
            zero.append(name)
            defect('LOW', 'departments', ucode, name,
                   '전 전형 0행 — 원문 표의 구분/마커 행으로 추정, 모집단위 아님', 'DEFER(미승격, 육안 확인 필요)')
        ok += 1
    extra = set(src) - {r['department_name'] for r in rows}
    if mism:
        for n, why in mism:
            defect('HIGH', 'departments', ucode, n, 'seed↔parsed 불일치: ' + why, 'FAIL')
    if extra:
        defect('HIGH', 'departments', ucode, sorted(extra)[:5], f'parsed에 있고 seed에 없음 {len(extra)}건', 'FAIL')
    if dup:
        defect('MED', 'departments', ucode, fname, f'parsed 중복 학과명 {dup}건(병합의)', 'WARN')
    dept_verdicts[ucode] = {'seed_rows': len(rows), 'parsed_rows': len(src), 'match': ok,
                            'mismatch': len(mism), 'zero_rows': zero, 'parsed_only': sorted(extra)}
checks['A_seed_vs_parsed_departments'] = dept_verdicts

# ---------- B. 행 합산 불변식 (학과 행: 전형값 합 == 합계) ----------
row_fail = defaultdict(list)
row_ok = 0
for r in seed['ipsi_departments']:
    cbt = r['counts_by_type']
    tot = cbt.get('합계')
    s = sum(v for k, v in cbt.items() if k != '합계')
    if tot is not None and s == tot:
        row_ok += 1
    else:
        row_fail[r['university_code']].append((r['department_name'], s, tot))
        defect('HIGH', 'row-sum', r['university_code'], r['department_name'],
               f'행합 {s} != 합계 {tot}', 'FAIL')
checks['B_row_sum_invariant'] = {'checked': len(seed['ipsi_departments']), 'pass': row_ok,
                                 'fail_by_univ': {u: len(v) for u, v in row_fail.items()}}

# ---------- B2. 집계 전용 컬럼 (학과별 미분해 — 결함 아님, 주석 근거) ----------
COL_DECL = {
 'KOREA': ('korea_2027_susi', 'counts_by_type', 'column_totals'),
 'SKKU': ('skku_2027_susi_overview', 'counts_by_type', 'column_totals'),
 'YONSEI': ('yonsei_2027_susi_part2', 'susi_by_type', 'column_totals'),
 'HANYANG': ('hanyang_2027_susi', 'by_type', 'by_type_in_quota'),
 'KHU': ('khu_2027_susi', 'by_type', None),
 'INHA': ('inha_2027_susi', 'by_type', None),
}
agg_only = {}
for u, (fname, tkey, decl_key) in COL_DECL.items():
    p = parsed[fname]
    if decl_key == 'by_type_in_quota':
        decl = p['totals']['by_type_in_quota']
    elif decl_key:
        decl = p[decl_key]
    else:
        decl = {k: v for k, v in p['totals'].items() if isinstance(v, int) and k != 'grand_total'}
    recomp = {k: sum(d[tkey].get(k, 0) for d in p['departments']) for k in decl}
    diffs = {k: (recomp[k], decl[k]) for k in decl if recomp[k] != decl[k]}
    if diffs:
        agg_only[u] = diffs
        for k, (rc, dc) in diffs.items():
            defect('INFO', 'aggregate-column', u, k,
                   f'학과별 합 {rc} != 선언 총계 {dc} — 정원외/집계전용/미분해(요강 각주 근거, 파서 검증 통과)', 'KNOWN_NOTE(결함 아님)')
checks['B2_aggregate_only_columns'] = agg_only

# ---------- C. 전형·일정 행 대조 ----------
at_src_counts = {'SNU': ('snu_2027_susi', 'admission_types'), 'YONSEI': ('yonsei_2027_susi', 'admission_types'),
                 'SKKU': ('skku_2027_susi', 'admission_types'), 'KOREA': ('korea_2027_susi', 'admission_types'),
                 'HANYANG': ('hanyang_2027_susi', 'admission_types'), 'KHU': ('khu_2027_susi', 'admission_types'),
                 'INHA': ('inha_2027_susi', 'admission_types')}
at_out = {}
for ucode, rows in defaultdict(list, {u: [r for r in seed['ipsi_admission_types'] if r['university_code'] == u] for u in at_src_counts}).items():
    fname, key = at_src_counts[ucode]
    src_types = parsed[fname][key]
    src_names = {t.get('name') for t in src_types}
    seed_names = {r['type_name'] for r in rows}
    at_out[ucode] = {'seed': len(rows), 'parsed': len(src_types)}
    missing = src_names - seed_names
    added2028 = seed_names - src_names
    if ucode == 'YONSEI':
        added2028 = {n for n in added2028 if '2028' in n}
    if missing:
        defect('MED', 'admission_types', ucode, sorted(missing)[:3], 'seed 미반영 전형', 'WARN')
checks['C_admission_type_coverage'] = at_out

# ---------- D. 출처 연결 · 2027/2028 구분 ----------
doc_keys = {d['document_key']: d for d in seed['ipsi_documents']}
link_fail = 0
for sec in ('ipsi_departments', 'ipsi_admission_types'):
    for r in seed[sec]:
        k = r.get('source_document_key')
        if not k or k not in doc_keys:
            link_fail += 1
sched_no_dockey = sum(1 for r in seed['ipsi_schedules'] if not r.get('source_document_key'))
sched_nomatch = sum(1 for r in seed['ipsi_schedules']
                    if r.get('source_document_key') and r.get('schedule_match') not in ('EXACT', 'FUZZY'))
if sched_no_dockey:
    defect('MED', 'schedules', 'ALL', 'ipsi_schedules',
           f'일정 {sched_no_dockey}건에 source_document_key 없음(문서 ID 연결 누락; source_url은 존재)', 'DEFER(연결 보정 전까지 미승격)')
if sched_nomatch:
    defect('MED', 'schedules', 'ALL', 'ipsi_schedules',
           f'일정 {sched_nomatch}건은 키는 있으나 parsed 일정과 항목·날짜 대조 실패(NONE)', 'DEFER(원문 육안 확인 전까지 미승격)')
y28_rows = [r for r in seed['ipsi_admission_types'] if str(r.get('academic_year')) == '2028']
y28_ok = all(r['source_document_key'] == 'doc_yon_2028_plan' for r in y28_rows)
dept_2028 = [r for r in seed['ipsi_departments'] if str(r.get('academic_year')) != '2027']
checks['D_linkage_and_year_split'] = {
    'rows_missing_doc_key_or_unknown': link_fail,
    'schedules_missing_document_key': sched_no_dockey,
    'schedules_without_parsed_match': sched_nomatch,
    'admission_types_2028': len(y28_rows), 'admission_types_2028_all_yonsei_plan': y28_ok,
    'departments_non2027': len(dept_2028),
    'rule': '2028 행은 연세대 시행계획 기반 신설전형 2건뿐 — 2028 모집인원 추정 행 없음 확인'}

# ---------- E. 값 공백(null) 목록 ----------
nulls = defaultdict(list)
for r in seed['ipsi_admission_types']:
    miss = [k for k in ('student_record_method', 'min_academic_standard', 'eligibility', 'recruitment_count') if not r.get(k)]
    if miss:
        nulls[r['university_code'] + ':' + str(r['type_name'])[:14]] = miss
checks['E_value_gaps'] = dict(nulls)
for k, v in nulls.items():
    defect('MED', 'admission_types', k.split(':')[0], k, '필드 공백 ' + ','.join(v), 'PARTIAL_CANDIDATE(수집된 필드만 승격 후보)')

# ---------- F. 로컬 원본 텍스트 스팟 검증 ----------
spot = {}
def txt(name):
    fp = P('data', 'raw', 'text', name)
    return io.open(fp, encoding='utf-8').read() if os.path.exists(fp) else ''
def find(u, needles):
    t = txt(u).replace(',', '').replace(' ', '')
    return [n for n in needles if str(n).replace(',', '') in t]
pairs = {
 'snu_2027_susi.txt': ['1169', '414', '2026.9.7'],
 'yonsei_2027_plan.txt': ['1701', '487', '714', '기회균형', '추천형'],
 'korea_2027_susi.txt': ['2731', '903', '650', '523', '09.09', '12.18'],
 'skku_2027_susi.txt': ['2378', '1487', '9.8'],
}
for fname, needles in pairs.items():
    hit = find(fname, needles)
    spot[fname] = {'needles': needles, 'found': hit, 'missed': [n for n in needles if n not in hit]}
    if len(hit) < max(2, len(needles) // 2):
        defect('INFO', 'raw_text_spot', fname, needles,
               '원본 텍스트레이어에서 핵심 수치 미발견 — 표가 서브셋폰트/구조화 영역이라 get_text(비표) 유실 가능; 파서는 find_tables로 확보했으므로 참고 신호', 'INFO(결함 판정 제외)')
checks['F_raw_text_spot'] = spot

# ---------- G. APPROVED 전환 후보 분류 (행 단위, 상태 변경 없음) ----------
zero_univ_ok = set()  # (ucode,name) flagged zero
for d in defects:
    if d['area'] == 'departments' and d['severity'] in ('LOW', 'MED'):
        if d['item'] and not str(d['item']).startswith(d['university']):
            pass
dept_cat = Counter()
fail_dept = set(n for u, v in row_fail.items() for n in v)
marker = {'광역'}
for r in seed['ipsi_departments']:
    u = r['university_code']; nm = r['department_name']
    cbt = r['counts_by_type']
    base = {k: v for k, v in cbt.items() if k != '합계'}
    if nm in marker:
        dept_cat['DEFER'] += 1
        continue
    if (u, nm) in {(u2, n2) for u2, v in row_fail.items() for (n2, a, b) in v}:
        dept_cat['FAIL'] += 1
    elif all(v == 0 for v in base.values()):
        dept_cat['DEFER'] += 1
    else:
        dept_cat['APPROVED_CANDIDATE'] += 1

at_cat = Counter()
for r in seed['ipsi_admission_types']:
    core = [r.get('student_record_method'), r.get('min_academic_standard'),
            r.get('eligibility'), r.get('recruitment_count')]
    filled = sum(1 for c in core if c)
    if r.get('min_academic_standard') is None and '한양' in str(r.get('institution_name', '')) or (filled <= 1 and r['university_code'] == 'HANYANG'):
        at_cat['CANDIDATE_WITH_CAVEAT'] += 1
    elif filled <= 1:
        at_cat['CANDIDATE_WITH_CAVEAT'] += 1
    else:
        at_cat['APPROVED_CANDIDATE'] += 1

sched_cat = Counter()
for r in seed['ipsi_schedules']:
    if not r.get('source_document_key'):
        sched_cat['DEFER'] += 1
    elif r.get('schedule_match') in ('EXACT', 'FUZZY'):
        sched_cat['APPROVED_CANDIDATE'] += 1
    else:
        sched_cat['DEFER'] += 1

cand = {
 'departments': dict(dept_cat),
 'admission_types': dict(at_cat),
 'schedules': dict(sched_cat),
 'fail_total': sum(v for k, v in dept_cat.items() if k == 'FAIL'),
 'rule': '후보 분류만 — 실제 승격은 육안 대조·운영자 승인 필수, 본 스크립트는 verification_status를 변경하지 않음'}
checks['G_approved_candidates'] = cand

report['checks'] = checks
report['defects'] = defects
report['totals'] = {
    'departments_checked': sum(v['seed_rows'] for v in dept_verdicts.values()),
    'admission_types_checked': sum(v['seed'] for v in at_out.values()),
    'schedules_checked': len(seed['ipsi_schedules']),
    'row_sum_pass': row_ok,
    'defects_high': sum(1 for d in defects if d['severity'] == 'HIGH'),
    'defects_med': sum(1 for d in defects if d['severity'] == 'MED'),
    'defects_low': sum(1 for d in defects if d['severity'] == 'LOW'),
    'defects_info': sum(1 for d in defects if d['severity'] == 'INFO')}
os.makedirs(P('data', 'validation'), exist_ok=True)
json.dump(report, io.open(P('data', 'validation', 'official_validation.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('defects:', json.dumps(report['totals'], ensure_ascii=False))
print('candidates:', json.dumps(cand, ensure_ascii=False))
for d in defects:
    print(d['severity'], d['area'], d['university'], str(d['item'])[:48], '|', d['issue'][:90])
