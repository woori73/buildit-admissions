#!/usr/bin/env python3
"""data/parsed/univ_sample/*.json → DB 시드 형태(data/seed/ipsi_seed_univ_sample.json).

스키마(docs/schema V1064~V1067) 컬럼명을 따른다. 검증状态는 전부 NORMALIZED —
REVIEW/APPROVED 승격은 육안 대조·승인 절차通过后에야 가능(상담 검색 게이트 유지).
"""
import io, json, os, datetime

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

UNIV = {
    'snu': dict(university_code='SNU', name='서울대학교', establishment_type='국립',
                region='서울', admission_office_url='https://admission.snu.ac.kr/'),
    'yon': dict(university_code='YONSEI', name='연세대학교', establishment_type='사립',
                region='서울', admission_office_url='https://admission.yonsei.ac.kr/'),
    'skku': dict(university_code='SKKU', name='성균관대학교', establishment_type='사립',
                 region='서울', admission_office_url='https://admission.skku.edu/'),
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
         ('doc_skku_2027_susi', skku), ('doc_skku_2027_overview', skku_ov)]]

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
            'published_at': u['document']['published_at'], 'collected_at': u['document']['collected_at'],
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
    '전년도(2026) 입시결과(경쟁률·충원·권장과의목) 3개교 미추출 — 서울대 전형결과 페이지 등 후속',
    '고려대·한양대·경희대·인하대 확대 — 확대 작업에서 처리 예정',
    '적용학년도 2028 모집요강(수시)은 각 대학 2027년 5월 발표 → 2028 시행계획만 확보 완료(추정 보충 금지)']

counts = {
    'universities': len(seed['ipsi_universities']),
    'documents': len(seed['ipsi_documents']),
    'departments': len(seed['ipsi_departments']),
    'admission_types': len(seed['ipsi_admission_types']),
    'schedules': len(seed['ipsi_schedules']),
    'prior_results': 0,
    'approved': 0,
    'verification_status_all': 'NORMALIZED'}
seed['counts'] = counts
out = os.path.join(ROOT, 'data', 'seed', 'ipsi_seed_univ_sample.json')
json.dump(seed, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('seed ->', out)
print(json.dumps(counts, ensure_ascii=False))
