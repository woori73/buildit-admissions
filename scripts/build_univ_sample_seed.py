#!/usr/bin/env python3
"""data/parsed/univ_sample/*.json → DB 시드 형태(data/seed/ipsi_seed_univ_sample.json).

스키마(docs/schema V1064~V1067) 컬럼명을 따른다. 검증状态는 전부 NORMALIZED —
REVIEW/APPROVED 승격은 육안 대조·승인 절차通过后에야 가능(상담 검색 게이트 유지).
"""
import io, json, os, datetime, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
S = os.path.join(ROOT, 'data', 'parsed', 'univ_sample')

def load(n):
    return json.load(io.open(os.path.join(S, n), encoding='utf-8'))

snu = load('snu_2027_susi.json')
yon = load('yonsei_2027_susi.json')
yplan = load('yonsei_2027_plan.json')
yp2 = load('yonsei_2027_susi_part2.json')
y28 = load('yonsei_2028_plan.json')
skku = load('skku_2027_susi.json')
skku_ov = load('skku_2027_susi_overview.json')
korea = load('korea_2027_susi.json')
hanyang = load('hanyang_2027_susi.json')
khu = load('khu_2027_susi.json')
inha = load('inha_2027_susi.json')

UNIV = {
    'snu': dict(university_code='SNU', name='서울대학교', establishment_type='국립',
                region='서울', admission_office_url='https://admission.snu.ac.kr/'),
    'yon': dict(university_code='YONSEI', name='연세대학교', establishment_type='사립',
                region='서울', admission_office_url='https://admission.yonsei.ac.kr/'),
    'skku': dict(university_code='SKKU', name='성균관대학교', establishment_type='사립',
                 region='서울', admission_office_url='https://admission.skku.edu/'),
    'korea': dict(university_code='KOREA', name='고려대학교(서울)', establishment_type='사립',
                  region='서울', admission_office_url='https://oku.korea.ac.kr/'),
    'hanyang': dict(university_code='HANYANG', name='한양대학교(서울)', establishment_type='사립',
                    region='서울', admission_office_url='https://go.hanyang.ac.kr/'),
    'khu': dict(university_code='KHU', name='경희대학교(서울)', establishment_type='사립',
                region='서울', admission_office_url='https://iphak.khu.ac.kr/'),
    'inha': dict(university_code='INHA', name='인하대학교', establishment_type='사립',
                 region='인천', admission_office_url='https://admission.inha.ac.kr/'),
}

def docrow(key, p):
    return {
        'document_key': key,
        'institution_name': p['institution_name'], 'document_name': p['document_name'],
        'source_url': p['source_url'], 'file_url': p['file_url'],
        'applicable_academic_year': p['applicable_academic_year'],
        'published_at': p['published_at'], 'collected_at': p.get('collected_at', NOW),
        'verification_status': p['verification_status'],
        'redistribution': 'METADATA_PRIORITY', 'store_fulltext': False,
        'note': '원문 전문은 git 미저장(data/raw). 구조화 행만 저장.'}

docs = [docrow(k, v['document']) for k, v in
        [('doc_snu_2027_susi', snu), ('doc_yon_2027_susi', yon), ('doc_yon_2027_plan', yplan),
         ('doc_yon_2027_susi_part2', yp2), ('doc_yon_2028_plan', y28),
         ('doc_skku_2027_susi', skku), ('doc_skku_2027_overview', skku_ov),
         ('doc_korea_2027_susi', korea)]]

def docrow_new(key, p):
    return {
        'document_key': key,
        'institution_name': p['university'], 'document_name': p['doc_type'],
        'source_url': p['source_url'], 'file_url': p['source_url'],
        'applicable_academic_year': p['academic_year'],
        'published_at': '2026-05~09(요강별 상이)', 'collected_at': NOW,
        'verification_status': p['verification_status'],
        'redistribution': 'METADATA_PRIORITY', 'store_fulltext': False,
        'note': '원문 전문은 git 미저장(data/raw). 구조화 행만 저장.'}

for key, p in [('doc_hanyang_2027_susi', hanyang), ('doc_khu_2027_susi', khu), ('doc_inha_2027_susi', inha)]:
    docs.append(docrow_new(key, p))

seed = {
    'generated_at': NOW,
    'gate': 'verification_status=NORMALIZED — APPROVED전까지 상담 검색 미노출',
    'ipsi_universities': [dict(code=k, verification_status='NORMALIZED', **v) for k, v in UNIV.items()],
    'ipsi_documents': docs,
    'ipsi_departments': [],
    'ipsi_admission_types': [],
    'ipsi_schedules': [],
    'prior_results': [],
    'gaps': [],
}

for dept in snu['departments']:
    seed['ipsi_departments'].append({
        'university_code': 'SNU', 'academic_year': '2027', 'department_name': dept['department'],
        'counts_by_type': {'지역균형전형': dept['지역균형전형'], '일반전형': dept['일반전형'],
                           '기회균형특별전형': dept['기회균형특별전형'], '합계': dept['total']},
        'source_document_key': 'doc_snu_2027_susi', 'verification_status': 'NORMALIZED'})
for dept in yp2['departments']:  # Ⅱ부 모집요강(권위 소스) — 시행계획 행은 파싱 산출물 파일로 보존
    seed['ipsi_departments'].append({
        'university_code': 'YONSEI', 'academic_year': '2027', 'department_name': dept['department'],
        'college_name': dept['college'], 'track': dept['track'],
        'counts_by_type': dict(dept['susi_by_type'], 합계=dept['susi_sum']),
        'plan_total_susi_plus_regular': dept['plan_total_susi_plus_regular_star'],
        'source_document_key': 'doc_yon_2027_susi_part2', 'verification_status': 'NORMALIZED'})
for dept in skku_ov['departments']:
    seed['ipsi_departments'].append({
        'university_code': 'SKKU', 'academic_year': '2027', 'department_name': dept['department'],
        'college_name': dept['college_group'],
        'counts_by_type': dict(dept['counts_by_type'], 합계=dept['susi_total']),
        'source_document_key': 'doc_skku_2027_overview', 'verification_status': 'NORMALIZED'})

def types_from(u, code, dok):
    for t in u['admission_types']:
        seed['ipsi_admission_types'].append({
            'university_code': code, 'academic_year': u['document']['applicable_academic_year'],
            'round_type': 'SUSI', 'type_name': t['name'],
            'type_category': (t['name'].split('(')[0].split('[')[0]).strip(),
            'recruitment_count': t.get('applicant_total'),
            'eligibility': t.get('eligibility'), 'student_record_method': t.get('method'),
            'min_academic_standard': t.get('csat_minimum'),
            'source_document_key': dok, 'source_url': u['document']['source_url'],
            'institution_name': u['document']['institution_name'],
            'published_at': u['document']['published_at'], 'collected_at': u['document'].get('collected_at', NOW),
            'verification_status': 'NORMALIZED'})

types_from(snu, 'SNU', 'doc_snu_2027_susi')
types_from(yon, 'YONSEI', 'doc_yon_2027_susi')
types_from(skku, 'SKKU', 'doc_skku_2027_susi')

for u, code in [(snu, 'SNU'), (yon, 'YONSEI')]:
    if 'schedules_sample' in u:
        for it in u['schedules_sample']['items']:
            seed['ipsi_schedules'].append({
                'university_code': code, 'academic_year': u['document']['applicable_academic_year'],
                'round_type': 'SUSI', 'type_name': u['schedules_sample']['type'],
                'item': it['item'], 'date': it['date'],
                'source_url': u['document']['source_url'], 'verification_status': 'NORMALIZED'})
for it in skku['schedules']['items']:
    seed['ipsi_schedules'].append({
        'university_code': 'SKKU', 'academic_year': 2027, 'round_type': 'SUSI', 'type_name': '전 전형',
        'item': it['item'], 'date': it['date'],
        'source_url': skku['document']['source_url'], 'verification_status': 'NORMALIZED'})

# ---- 2026-10-13 오후 확대: 고려·한양·경희·인하 ----
for dept in korea['departments']:
    seed['ipsi_departments'].append({
        'university_code': 'KOREA', 'academic_year': '2027', 'department_name': dept['department'],
        'college_name': dept.get('college'), 'track': dept.get('track'),
        'counts_by_type': dict(dept['counts_by_type'], 합계=dept['susi_total']),
        'source_document_key': 'doc_korea_2027_susi', 'verification_status': 'NORMALIZED'})
types_from(korea, 'KOREA', 'doc_korea_2027_susi')
for it in korea['schedules']['items']:
    seed['ipsi_schedules'].append({
        'university_code': 'KOREA', 'academic_year': 2027, 'round_type': 'SUSI', 'type_name': '전 전형',
        'item': it['item'], 'date': it['date'],
        'source_url': korea['document']['source_url'], 'verification_status': 'NORMALIZED'})

for u, code, dok in [(hanyang, 'HANYANG', 'doc_hanyang_2027_susi'),
                     (khu, 'KHU', 'doc_khu_2027_susi'),
                     (inha, 'INHA', 'doc_inha_2027_susi')]:
    for dept in u['departments']:
        seed['ipsi_departments'].append({
            'university_code': code, 'academic_year': '2027', 'department_name': dept['department'],
            'college_name': dept.get('college'), 'track': dept.get('track'),
            'counts_by_type': dict(dept['by_type'], 합계=dept.get('susi_sum', sum(dept['by_type'].values()))),
            'plan_total': dept.get('plan_total'),
            'source_document_key': dok, 'verification_status': 'NORMALIZED'})
    for t in u.get('admission_types', []):
        seed['ipsi_admission_types'].append({
            'university_code': code, 'academic_year': 2027, 'round_type': 'SUSI',
            'type_name': t['name'], 'type_category': (t['name'].split('(')[0].split('[')[0]).strip(),
            'recruitment_count': t.get('total'),
            'eligibility': t.get('eligibility'), 'student_record_method': t.get('method'),
            'min_academic_standard': t.get('csat_min'),
            'source_document_key': dok, 'source_url': u['source_url'],
            'institution_name': u['university'], 'published_at': '2026(요강별 상이)', 'collected_at': NOW,
            'verification_status': 'NORMALIZED'})
    for it in u.get('schedules', []):
        seed['ipsi_schedules'].append({
            'university_code': code, 'academic_year': 2027, 'round_type': 'SUSI', 'type_name': '전 전형',
            'item': it.get('stage'), 'date': it.get('period'),
            'source_url': u['source_url'], 'verification_status': 'NORMALIZED'})

seed['ipsi_admission_types'].append({
    'university_code': 'YONSEI', 'academic_year': 2028, 'round_type': 'SUSI',
    'type_name': '학생부종합전형[종합인재형](2028 신설)', 'type_category': '학생부종합',
    'student_record_method': '서류70+면접30(4배수)', 'min_academic_standard': '일부 모집단위 적용(언더우드 인문·사회/생명과학공학 미적용)',
    'source_document_key': 'doc_yon_2028_plan', 'source_url': y28['document']['source_url'],
    'institution_name': y28['document']['institution_name'], 'published_at': y28['document']['published_at'],
    'collected_at': NOW, 'verification_status': 'NORMALIZED'})
seed['ipsi_admission_types'].append({
    'university_code': 'YONSEI', 'academic_year': 2028, 'round_type': 'SUSI',
    'type_name': '학생부종합전형[탐구인재형](2028 신설)', 'type_category': '학생부종합',
    'student_record_method': '서류60+면접40(일반 4배수·국제 3배수)', 'min_academic_standard': '미적용',
    'source_document_key': 'doc_yon_2028_plan', 'source_url': y28['document']['source_url'],
    'institution_name': y28['document']['institution_name'], 'published_at': y28['document']['published_at'],
    'collected_at': NOW, 'verification_status': 'NORMALIZED'})

seed['gaps'] = [
    '[2026-10-13 오후 해소] 연세대 요강 Ⅱ부 → yonsei_2027_susi_part2.json(67행, 검증 통과). 잔여: 정시 세부 인원(2026.9.1. 정시요강 확인)',
    '[해소] 연세대 국제형 254/국제인재 120 전공별 분해 → part2 international_decomposition',
    '[해소] 성균관대 세부전형 소계 불일치 → 특별전형(정원외)187 포함 1,487 재현(PDF 7쪽 시각검증) + 총괄표 skku_2027_susi_overview.json(56행 검증 통과)',
    '전년도(2026) 입시결과(경쟁률·충원·권장과의목) 7개교 미추출 — 대학별 발표 페이지 후속',
    '[해소 2026-10-13 오후] 고려대(66행·2,731 검증)·한양대(65행·1,731+190 검증)·경희대(88행·3,006 검증)·인하대(63행·2,464 검증) — 총괄표 열합/합계행 교차 검증, 전형방법·수능최저는 경희·인하·고려 확보, 한양 method/csat 미추출(null 보존, 추정 금지)',
    '적용학년도 2028 모집요강(수시)은 각 대학 2027년 5월 발표 → 2028 시행계획만 확보 완료(추정 보충 금지)']

# ---- 2026-11-02 확대: 2027 정시 모집요강 + 수시 빈칸 보완(파일이 있는 대학만) ----
import glob

CODE_BY_KEY = {'snu': 'SNU', 'yonsei': 'YONSEI', 'skku': 'SKKU', 'korea': 'KOREA',
               'hanyang': 'HANYANG', 'khu': 'KHU', 'inha': 'INHA'}

import glob

# 확대 대학 등록부: data/meta/univ_registry.json {"universities":[{"key","name","establishment_type","region","admission_office_url","adiga_unvCd"}]}
# 대학 코드는 key 대문자(적재기가 자료 키 doc_<key>_... 에서 대학을 찾는 규칙과 같다).
REG_PATH = os.path.join(ROOT, 'data', 'meta', 'univ_registry.json')
if os.path.exists(REG_PATH):
    for u in json.load(io.open(REG_PATH, encoding='utf-8'))['universities']:
        if u['key'] in CODE_BY_KEY:
            continue
        if not glob.glob(os.path.join(S, u['key'] + '_*.json')):
            continue  # 자료가 아직 없는 대학은 등록하지 않는다(빈 대학이 '등록된 대학'으로 보이지 않게)
        code = u['key'].upper()
        CODE_BY_KEY[u['key']] = code
        seed['ipsi_universities'].append(dict(
            code=u['key'], university_code=code, name=u['name'], establishment_type=u.get('establishment_type'),
            region=u.get('region', '서울'), admission_office_url=u.get('admission_office_url'),
            adiga_unvCd=u.get('adiga_unvCd'), verification_status='NORMALIZED'))


def jeongsi_files():
    # 신규 대학 수시 전체(*_susi_full.json)를 먼저 넣어야 정시 학과 인원이 같은 학과 행에 합쳐진다.
    paths = sorted(glob.glob(os.path.join(S, '*_susi_full.json'))) + sorted(glob.glob(os.path.join(S, '*_jeongsi*.json')))
    for path in paths:
        name = os.path.basename(path)
        key = name.split('_')[0]
        if key not in CODE_BY_KEY:
            raise SystemExit('등록부에 없는 대학 파일: %s (data/meta/univ_registry.json에 추가 필요)' % name)
        yield key, name, json.load(io.open(path, encoding='utf-8'))


def method_text(t):
    parts = [t.get('method'), ('수능 반영: ' + t['csat_reflection']) if t.get('csat_reflection') else None]
    joined = ' / '.join(p for p in parts if p)
    return joined or None


MERGED = set()  # 같은 이름의 학과(예: 서울대 '광역' 2개)는 원문 순서대로 하나씩 짝짓는다.


def merge_department(code, year, dept, dok, label='정시'):
    counts = {k: v for k, v in dept['counts_by_type'].items()}
    counts[label + ' 합계'] = dept.get('total', sum(v for v in counts.values() if isinstance(v, int)))
    for idx, row in enumerate(seed['ipsi_departments']):
        if idx in MERGED:
            continue
        if row.get('college_name') and dept.get('college') and row['college_name'] != dept['college']:
            continue
        if row['university_code'] == code and str(row['academic_year']) == str(year) \
                and row['department_name'] == dept['department']:
            MERGED.add(idx)
            old = row['counts_by_type']
            if '합계' in old:
                old['수시 합계'] = old.pop('합계')
            old.update(counts)
            if label == '정시':
                row.setdefault('jeongsi_source_document_key', dok)
                if dept.get('group') and not row.get('jeongsi_group'):
                    row['jeongsi_group'] = dept['group']
            return
    seed['ipsi_departments'].append({
        'university_code': code, 'academic_year': str(year), 'department_name': dept['department'],
        'college_name': dept.get('college'), 'jeongsi_group': dept.get('group'),
        'counts_by_type': counts, 'source_document_key': dok, 'verification_status': 'NORMALIZED'})


FILL_FIELDS = ('recruitment_count', 'eligibility', 'student_record_method', 'min_academic_standard')
for path in sorted(glob.glob(os.path.join(S, '*_fill.json'))):
    f = json.load(io.open(path, encoding='utf-8'))
    key = os.path.basename(path).split('_')[0]
    code = CODE_BY_KEY.get(key)
    for fill in f.get('fills', []):
        rows = [r for r in seed['ipsi_admission_types']
                if r['university_code'] == code and r['type_name'] == fill['type_name']]
        if len(rows) != 1:
            raise SystemExit('fill 대상 전형을 찾지 못함(또는 중복): %s %s' % (code, fill['type_name']))
        for k in FILL_FIELDS:
            if fill.get(k) not in (None, ''):
                rows[0][k] = fill[k]
    if f.get('schedules_replace'):  # 원문과 다른 기존 수시 일정을 통째로 교체하고, 빠지는 행은 운영 DB에서 보관 처리
        keep, removed = [], []
        for r in seed['ipsi_schedules']:
            (removed if r['university_code'] == code and r.get('round_type') == 'SUSI' else keep).append(r)
        new_rows = [{'university_code': code, 'academic_year': 2027, 'round_type': 'SUSI',
                     'type_name': it.get('type_name') or '전 전형', 'item': it['item'], 'date': it['date'],
                     'source_document_key': f['document_key'], 'source_url': f.get('file_url'),
                     'verification_status': 'NORMALIZED'} for it in f['schedules_replace']]
        new_keys = {(n['item'] + ' (' + n['type_name'] + ')', n['date']) for n in new_rows}
        seed['ipsi_schedules'] = keep + new_rows
        seed.setdefault('archive_schedules', []).extend(
            {'university_code': code, 'academic_year': r['academic_year'],
             'title': r['item'] + ' (' + r['type_name'] + ')', 'note': r['date'],
             'reason': '원문 대조 결과 불일치로 교체(%s)' % os.path.basename(path)}
            for r in removed if (r['item'] + ' (' + r['type_name'] + ')', r['date']) not in new_keys)
    for dept in f.get('departments_add', []):  # 기존 수시 파싱에서 빠진 학과 행(원문 쪽수 근거)
        seed['ipsi_departments'].append({
            'university_code': code, 'academic_year': '2027', 'department_name': dept['department'],
            'college_name': dept.get('college'), 'counts_by_type': dept['counts_by_type'],
            'source_document_key': f['document_key'], 'verification_status': 'NORMALIZED'})
    for g in f.get('gaps', []):
        seed['gaps'].append('[%s 수시 보완] %s' % (code, g))

for key, name, j in jeongsi_files():
    code = CODE_BY_KEY[key]
    d = j['document']
    year = d['applicable_academic_year']
    dok = 'doc_' + name[:-5]
    susi = name.endswith('_susi_full.json')
    round_type = 'SUSI' if susi else 'JEONGSI'
    docs.append({
        'document_key': dok, 'institution_name': d['institution_name'], 'document_name': d['document_name'],
        'source_url': d.get('source_url'), 'file_url': d.get('file_url'), 'applicable_academic_year': year,
        'published_at': d.get('published_at'), 'collected_at': d.get('collected_at', NOW),
        'verification_status': d.get('verification_status', 'NORMALIZED'),
        'redistribution': 'METADATA_PRIORITY', 'store_fulltext': False,
        'note': '원문 전문은 git 미저장(data/raw). 구조화 행만 저장.'})
    for t in j.get('admission_types', []):
        seed['ipsi_admission_types'].append({
            'university_code': code, 'academic_year': year, 'round_type': round_type,
            'type_name': t['name'],
            'type_category': (t.get('category') or t['name'].split('(')[0].strip()) if susi
            else '정시' + ('(' + t['group'] + '군)' if t.get('group') else ''),
            'recruitment_count': t.get('recruitment_count'), 'eligibility': t.get('eligibility'),
            'student_record_method': method_text(t), 'min_academic_standard': t.get('csat_minimum'),
            'submission_documents': t.get('submission_documents') or None,
            'source_document_key': dok, 'source_url': d.get('source_url'),
            'institution_name': d['institution_name'], 'published_at': d.get('published_at'),
            'collected_at': d.get('collected_at', NOW), 'verification_status': 'NORMALIZED'})
    for dept in j.get('departments', []):
        merge_department(code, year, dept, dok, '수시' if susi else '정시')
    for it in j.get('schedules', []):
        seed['ipsi_schedules'].append({
            'university_code': code, 'academic_year': year, 'round_type': round_type,
            'type_name': it.get('type_name') or ('전 전형' if susi else '정시 전 전형'), 'item': it['item'], 'date': it['date'],
            'source_document_key': dok, 'source_url': d.get('source_url'), 'verification_status': 'NORMALIZED'})
    for g in j.get('gaps', []):
        seed['gaps'].append('[%s %s] %s' % (code, '수시' if susi else '정시', g))

# 처음 7개 대학의 원래 수시 일정 행에는 출처 자료 키가 없었다(검색은 승인된 출처가 있는 행만 쓴다). 그 대학 수시 요강을 출처로 단다.
SUSI_DOC = {'SNU': 'doc_snu_2027_susi', 'YONSEI': 'doc_yon_2027_susi', 'SKKU': 'doc_skku_2027_susi', 'KOREA': 'doc_korea_2027_susi',
            'HANYANG': 'doc_hanyang_2027_susi', 'KHU': 'doc_khu_2027_susi', 'INHA': 'doc_inha_2027_susi'}
doc_keys = {d['document_key'] for d in docs}
for r in seed['ipsi_schedules']:
    if not r.get('source_document_key') and r.get('round_type') == 'SUSI' and SUSI_DOC.get(r['university_code']) in doc_keys:
        r['source_document_key'] = SUSI_DOC[r['university_code']]
missing = [r for r in seed['ipsi_schedules'] if not r.get('source_document_key')]
if missing:
    raise SystemExit('출처 자료 키가 없는 일정 %d건: %s' % (len(missing), missing[0]))
# 자료 제목에 대학 이름을 넣는다. "2027학년도 수시모집 모집요강"처럼 흔한 제목은 대학끼리 겹쳐 출처가 헷갈리고,
# 예전 적재기는 제목만으로 같은 자료를 찾아 다른 대학 자료에 연결했다.
_univ_name = {u['university_code']: u['name'] for u in seed['ipsi_universities']}
for d in seed['ipsi_documents']:
    code = d['document_key'].split('_')[1].upper()
    name = _univ_name.get(code) or _univ_name.get({'YON': 'YONSEI'}.get(code, code))
    if not name:
        raise SystemExit('자료 키의 대학 코드를 찾지 못함: %s' % d['document_key'])
    base = re.sub(r'\(.*?\)', '', name).strip()
    if base not in d['document_name'] and base.replace('학교', '') not in d['document_name']:
        d['document_name'] = base + ' ' + d['document_name']
_titles = [(d['document_key'].split('_')[1].upper(), d['document_name']) for d in seed['ipsi_documents']]
_dup_titles = sorted({t for c, t in _titles if sum(1 for c2, t2 in _titles if t2 == t and c2 != c)})
if _dup_titles:
    raise SystemExit('여러 대학이 같은 자료 제목을 씀: %s' % _dup_titles[0])

# 적재기는 일정 제목을 "item (type_name)"으로 만들고 DB 열은 200자다. 넘으면 적재 전체가 실패하므로 여기서 막는다.
too_long = [r for r in seed['ipsi_schedules'] if len('%s (%s)' % (r.get('item') or '', r.get('type_name') or '')) > 200]
if too_long:
    raise SystemExit('일정 제목(item + type_name)이 200자를 넘는 행 %d건: %s %s' % (len(too_long), too_long[0]['university_code'], too_long[0]['item'][:60]))

# 이 시드가 다루는 대학은 시드가 최신본이다(적재기가 같은 대학의 예전 행을 보관 처리). 수시·정시 원문을 모두 정리한 대학만.
seed['authoritative_universities'] = sorted({u['university_code'] for u in seed['ipsi_universities']})

counts = {
    'universities': len(seed['ipsi_universities']),
    'documents': len(docs),
    'departments': len(seed['ipsi_departments']),
    'admission_types': len(seed['ipsi_admission_types']),
    'schedules': len(seed['ipsi_schedules']),
    'archive_schedules': len(seed.get('archive_schedules', [])),
    'authoritative_universities': len(seed['authoritative_universities']),
    'prior_results': 0,
    'approved': 0,
    'verification_status_all': 'NORMALIZED'}
seed['counts'] = counts
out = os.path.join(ROOT, 'data', 'seed', 'ipsi_seed_univ_sample.json')
json.dump(seed, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('seed ->', out)
print(json.dumps(counts, ensure_ascii=False))
