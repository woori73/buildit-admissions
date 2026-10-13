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
y28 = load('yonsei_2028_plan.json')
skku = load('skku_2027_susi.json')

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
        'published_at': p['published_at'], 'collected_at': p['collected_at'],
        'verification_status': p['verification_status'],
        'redistribution': 'METADATA_PRIORITY', 'store_fulltext': False,
        'note': '원문 전문은 git 미저장(data/raw). 구조화 행만 저장.'}

docs = [docrow(k, v['document']) for k, v in
        [('doc_snu_2027_susi', snu), ('doc_yon_2027_susi', yon), ('doc_yon_2027_plan', yplan),
         ('doc_yon_2028_plan', y28), ('doc_skku_2027_susi', skku)]]

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
for dept in yplan['departments']:
    seed['ipsi_departments'].append({
        'university_code': 'YONSEI', 'academic_year': '2027', 'department_name': dept['department'],
        'college_name': dept['college'], 'track': dept['track'],
        'counts_by_type': {'추천형': dept['추천형'], '활동우수형': dept['활동우수형'], '기회균형': dept['기회균형'],
                           '논술': dept['논술'], '특기자_체육': dept['특기자_체육'], '합계': dept['total']},
        'source_document_key': 'doc_yon_2027_plan', 'verification_status': 'NORMALIZED'})

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
    '연세대 모집요강 Ⅱ부(수시+정시 통합 전공 테이블) 컬럼 레이아웃 자동파싱 실패 → 2027 시행계획 테이블로 전공별 수시 인원 대체 확보(정시 인원 미확보)',
    '연세대 2027 정원외 국제형(254)/국제인재(120)의 전공별 분해 미확보(시행계획 파서 컬럼 매핑 외)',
    '성균관대 세부전형(융합329/탐구589/성균196/지역3/과학155/기회28) 값이 소계 1,487과 재현 불일치 → PDF 육안 검증 전까지 미채택',
    '성균관대 전공×전형 총괄표 매핑 미해결(공백 생략 레이아웃)',
    '전년도(2026) 입시결과(경쟁률·충원·권장과의목) 3개교 미추출 — 서울대 전형결과 페이지 등 후속',
    '인하대(admission.inha.ac.kr JS 셸)/고려대(네트워크 차단)/한양·경희(도미 넬 미확인) — 샘플 확장 시 처리',
    '적용학년도 2028 모집요강(수시)은 각 대학 2027년 5월 발표 → 2028 시행계획만 확보 완료']

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
