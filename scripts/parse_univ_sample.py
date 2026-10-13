#!/usr/bin/env python3
"""샘플 대학(서울대·연세대·성균관대) 2027/2028 자료 구조화 파이프라인.

- PDF 전문(data/raw/pdfs, gitignore) → 텍스트(data/raw/text) → 검증된 구조화 행(data/parsed/univ_sample).
- 모든 레코드에 출처 URL·문서명·적용학년도·검증상태를 기록한다.
- 검증(행 합 = 표기 합, 컬럼 합 = 전형별 총괄)에 실패하면 해당 필드는 unresolved로 남긴다.
"""
import io, re, json, os, sys, hashlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw', 'text')
OUTD = os.path.join(ROOT, 'data', 'parsed', 'univ_sample')
os.makedirs(OUTD, exist_ok=True)
NOW = datetime.datetime.now().astimezone().isoformat(timespec='seconds')

PROV = {
    'snu': dict(
        institution_name='서울대학교 입학본부',
        document_name='2027학년도 대학 신입학생 수시모집 안내(모집요강)',
        source_url='https://admission.snu.ac.kr/materials/guides/guides?md=v&bbsidx=170741',
        file_url='https://admission.snu.ac.kr/webdata/admission/files/2027susi.pdf',
        applicable_academic_year=2027, published_at='2026-05-29'),
    'yon': dict(
        institution_name='연세대학교 입학처',
        document_name='2027학년도 수시모집 모집요강',
        source_url='https://admission.yonsei.ac.kr/seoul/admission/html/rolling/guide.asp',
        file_url='https://admission.yonsei.ac.kr/seoul/upload/guide/20260529204109T8NZNJ.PDF',
        applicable_academic_year=2027, published_at='2026-05-29'),
    'yon_plan27': dict(
        institution_name='연세대학교',
        document_name='2027학년도 연세대학교 서울캠퍼스 입학전형 시행계획',
        source_url='https://www2.yonsei.ac.kr/entrance/plan/2027_plan.pdf',
        file_url='https://www2.yonsei.ac.kr/entrance/plan/2027_plan.pdf',
        applicable_academic_year=2027, published_at='2026-04'),
    'yon_plan28': dict(
        institution_name='연세대학교',
        document_name='2028학년도 연세대학교 서울캠퍼스 입학전형 시행계획',
        source_url='https://www2.yonsei.ac.kr/entrance/plan/2028_plan.pdf',
        file_url='https://www2.yonsei.ac.kr/entrance/plan/2028_plan.pdf',
        applicable_academic_year=2028, published_at='2026-04'),
    'skku': dict(
        institution_name='성균관대학교 입학처',
        document_name='2027학년도 수시모집 모집요강',
        source_url='https://admission.skku.edu/admission/html/rolling/guide.html',
        file_url='https://admission.skku.edu/upload/guide/20260813104526BBPE44.pdf',
        applicable_academic_year=2027, published_at='2026-08-13'),
}

def text(name):
    return io.open(os.path.join(RAW, name + '.txt'), encoding='utf-8').read()

def lines(name):
    return [l.strip() for l in text(name).splitlines()]

# ---------- SNU 모집단위×전형 테이블 ----------
def parse_snu_rows():
    ls = lines('snu_2027_susi')
    s = ls.index('모집단위와 모집인원')
    e = next(i for i, l in enumerate(ls) if l.startswith('※ 학사조직'))
    toks = [l for l in ls[s:e] if l]
    def clean(t):
        if t == '·':
            return 0
        m = re.match(r'^(\d[\d,]*)', t)
        return int(m.group(1).replace(',', '')) if m else None
    skip = re.compile(r'^(<<<PAGE.*|- \d+ -|모집단위와 모집인원|모집단위|정원 내 전형|지역균형전형|일반전형|기회균형특별전형|\(사회통합\))$')
    i = toks.index('합계') + 1
    order, pending = [], []
    while i < len(toks):
        t = toks[i]
        if skip.match(t):
            i += 1; continue
        if clean(t) is None:
            pending.append(t); i += 1; continue
        if pending and i + 4 <= len(toks) and all(clean(x) is not None for x in toks[i:i+4]):
            order.append((pending.pop(), [clean(x) for x in toks[i:i+4]]))
            pending = []; i += 4; continue
        i += 1
    rows, grp, markfail, rowfail = [], [], 0, 0
    for name, vv in order:
        if name in ('소계', '합계'):
            matched = next((k for k in range(1, len(grp)+1)
                            if [sum(g[1][j] for g in grp[-k:]) for j in range(4)] == vv), None)
            if matched is None:
                markfail += 1
            else:
                grp = grp[:-matched]
        else:
            if vv[0] + vv[1] + vv[2] != vv[3]:
                rowfail += 1
            rows.append({'department': name, '지역균형전형': vv[0], '일반전형': vv[1],
                         '기회균형특별전형': vv[2], 'total': vv[3]})
            grp.append((name, vv))
    checks = {'rows': len(rows), 'row_sum_failures': rowfail, 'subtotal_marker_failures': markfail}
    return rows, checks

# ---------- 연세대 2027 시행계획 모집단위 테이블 ----------
YON_COLS = ['추천형', '활동우수형', '국제형_국내고', '국제형_해외고', '국제인재', '기회균형', '논술', '특기자_체육']

def parse_yon_plan_rows():
    ls = lines('yonsei_2027_plan')
    mi = [i for i, l in enumerate(ls) if l == '모집단위별 모집인원']
    s = mi[0]
    e = next(i for i, l in enumerate(ls[s+1:], s+1) if l.startswith('2. 정시모집'))
    toks = [l for l in ls[s:e] if l]
    hdr = set(['문과대학','상경대학','경영대학','신과대학','사회과학대학','생활과학대학','의과대학','치과대학','약학대학','간호대학','이과대학','공과대학','생명시스템대학','인공지능융합대학','글로벌인재대학','언더우드국제대학'])
    noise = set(['대학','모집단위','계열','모집','인원','정원','내','외','III','1.','수시모집','모집단위별','모집단위별모집인원',
                 '추천형','활동','우수형','국제형','국제','인재','기회','균형','논술','특기자','전형','특수교육','대상자','국내고','해외고',
                 '실기/실적학생부종합','교과','종합','실기/실적','학생부','학생부교과','학생부종합'])
    def isnum(x): return bool(re.match(r'^\d[\d,]*$', x))
    def ismark(x): return x in ('-', '○')
    rows, probs, cur, i = [], [], None, 0
    while i < len(toks):
        x = toks[i]
        if x in hdr:
            cur = x; i += 1; continue
        if (x in noise or x.startswith('<<<PAGE') or re.match(r'^- \d+ -$', x) or x == '모집인원'
                or '정원' in x or x.startswith('학생부')):
            i += 1; continue
        if isnum(x) or ismark(x):
            i += 1; continue
        j = i + 1; track = None
        if j < len(toks) and toks[j] in ('인문', '자연', '통합', '예능', '체능', '인문·사회', '자연·공학', '의·치·약'):
            track = toks[j]; j += 1
        seq = []
        while j < len(toks) and (isnum(toks[j]) or ismark(toks[j])) and len(seq) < 12:
            seq.append(toks[j]); j += 1
        if len(seq) in (9, 10) and isnum(seq[0]):
            v = [int(t.replace(',', '')) if isnum(t) else 0 for t in seq]
            rec = {'college': cur, 'department': x, 'track': track, 'total': v[0]}
            rec.update({c: v[1+k] for k, c in enumerate(YON_COLS)})
            if v[0] == sum(v[1:9]):
                rows.append(rec)
            else:
                probs.append((x, seq))
            i = j; continue
        i = j if seq else i + 1
    agg = {c: sum(r[c] for r in rows) for c in YON_COLS + ['total']}
    checks = {'rows': len(rows), 'row_sum_failures': len(probs),
              'column_totals': agg,
              'vs_type_summary': {'추천형487': agg['추천형'] == 487, '활동우수형714': agg['활동우수형'] == 714,
                                  '기회균형190': agg['기회균형'] == 190, '논술272': agg['논술'] == 272,
                                  '특기자38': agg['특기자_체육'] == 38}}
    return rows, checks

# ---------- 문서별 산출물 ----------
def write(name, obj):
    p = os.path.join(OUTD, name)
    json.dump(obj, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', name)

def meta(key, extra=None):
    m = dict(PROV[key])
    m.update({'collected_at': NOW, 'extraction': 'pymupdf text layer',
              'verification_status': 'NORMALIZED', 'approved': False,
              'exposure': 'HIDDEN (APPROVED-only search gate)'})
    if extra:
        m.update(extra)
    return m

snu_rows, snu_checks = parse_snu_rows()
snutot = {c: sum(r[c] for r in snu_rows) for c in ['지역균형전형', '일반전형', '기회균형특별전형', 'total']}
write('snu_2027_susi.json', {
    'document': meta('snu', {'verification': snu_checks, 'column_totals': snutot}),
    'admission_types': [
        {'name': '학생부종합전형(지역균형전형)', 'applicant_total': snutot['지역균형전형'],
         'method': '1단계 서류100%(2배수) → 2단계 서류평가+면접(의·치학계열 제외 전 모집단위)',
         'csat_minimum': '4개 영역(국어,수학,영어,탐구) 중 3개 영역 등급 합 7 이내(탐구 2과목 평균)',
         'eligibility': '학교장추천(고교별 2명), 동일 고교 졸업자 기준 등 요강 14쪽 지원자격',
         'evidence_pages': [1, 15]},
        {'name': '학생부종합전형(일반전형)', 'applicant_total': snutot['일반전형'],
         'method': '서류평가(1단계) + 면접·구술·실기(2단계, 모집단위별 상이)',
         'csat_minimum': '전 모집단위 미적용(미술대학 디자인과만 수능 응시영역기준·최저 적용)',
         'eligibility': '고등학교 졸업(예정)자 또는 동등 학력(요강 19~28쪽)',
         'evidence_pages': [3, 22]},
        {'name': '학생부종합전형(기회균형특별전형(사회통합))', 'applicant_total': snutot['기회균형특별전형'],
         'method': '서류평가 + 면접(사범대는 교직적성·인성면접 포함)',
         'csat_minimum': '미적용', 'eligibility': '기초생활수급·차상위·농어촌·북한이탈 등(요강 36~44쪽)',
         'evidence_pages': [5, 40]},
        {'name': '실기위주전형(일반전형-음악대학 피아노·관현악)', 'applicant_total': None,
         'method': '실기 위주(요강 29~36쪽)', 'csat_minimum': '미적용',
         'eligibility': '음악대학 지원자(요강)', 'evidence_pages': [29]},
    ],
    'schedules_sample': {'type': '지역균형전형', 'items': [
        {'item': '지원서 접수(인터넷)', 'date': '2026.9.7.(월) 10:00 ~ 9.9.(수) 18:00'},
        {'item': '서류제출(온라인 업로드)', 'date': '2026.9.7.(월) 10:00 ~ 9.10.(목) 18:00'},
        {'item': '1단계 합격자 발표', 'date': '2026.11.27.(금) 18:00 이후'},
        {'item': '면접(전 모집단위, 의·치대 제외)', 'date': '2026.12.4.(금)'},
        {'item': '면접(수의·의과대학)', 'date': '2026.12.5.(토)'},
        {'item': '합격자 발표', 'date': '2026.12.18.(금) 18:00 이후'},
        {'item': '합격자 등록(온라인 문서등록)', 'date': '2026.12.21.(월) 09:00 ~ 12.23.(수) 16:00'}]},
    'departments': snu_rows})

yon_rows, yon_checks = parse_yon_plan_rows()
write('yonsei_2027_susi.json', {
    'document': meta('yon', {'verification': {
        'type_totals_from_yoyang_summary': {'추천형': '487명(25명)', '활동우수형': '714명(52명)', '국제형': '254명',
                                             '국제인재': '120명', '기회균형': '190명(5명)', '논술전형': '272명(16명)',
                                             '특기자_체육인재': '38명', '특수교육대상자': '13명'},
        'cross_check_vs_plan': 'see yonsei_2027_plan.json columns'}}),
    'admission_types': [
        {'name': '학생부교과전형[추천형]', 'applicant_total': 487, 'outside_quota_contract': 25,
         'method': '단계별(1단계 학생부교과100 500% → 2단계 학생부교과80+서류평가20)+수능최저',
         'csat_minimum': '적용(전 모집단위, 인문 또는 자연(일반) 기준 중 하나 만족)',
         'eligibility': '학교장 추천자(요강 22쪽~)', 'evidence_pages': [1, 22]},
        {'name': '학생부종합전형[활동우수형]', 'applicant_total': 714, 'outside_quota_contract': 52,
         'method': '1단계 서류100(4배수) → 2단계 서류60+면접40+수능최저',
         'csat_minimum': '적용', 'eligibility': '고졸(예정)·검정고시 등(요강)', 'evidence_pages': [1]},
        {'name': '학생부종합전형[국제형(국내고/해외고·검정고시)]', 'applicant_total': 254,
         'method': '단계별 서류+면접(국내고 5배수→ 서류60+면접40+수능최저; 해외고/검정고시 3배수→서류60+면접40)',
         'csat_minimum': '국내고만 적용, 해외고/검정고시 미적용',
         'eligibility': '외국 소재 고교 등(요강 국제형)', 'evidence_pages': [2]},
        {'name': '학생부종합전형[국제인재]', 'applicant_total': 120,
         'method': '1단계 서류(3배수)→2단계 서류60+면접40', 'csat_minimum': '미적용',
         'eligibility': '요강 국제인재', 'evidence_pages': [2]},
        {'name': '학생부종합전형[기회균형]', 'applicant_total': 190, 'outside_quota_contract': 5,
         'method': '1단계 서류(3배수)→2단계 서류60+면접40', 'csat_minimum': '미적용',
         'eligibility': '기초생활수급·농어촌 등(요강)', 'evidence_pages': [2]},
        {'name': '논술전형', 'applicant_total': 272, 'outside_quota_contract': 16,
         'method': '논술100+수능최저', 'csat_minimum': '적용(전 모집단위)',
         'eligibility': '고졸(예정) 등(요강)', 'evidence_pages': [1]},
        {'name': '특기자전형[체육인재]', 'applicant_total': 38,
         'method': '1단계 서류→2단계 실기/면접(요강 67쪽~)', 'csat_minimum': '미적용',
         'eligibility': '경기실적(2024.1.1. 이후 등 요강)', 'evidence_pages': [3]},
        {'name': '특수교육대상자전형', 'applicant_total': 13,
         'method': '서류+면접/실기(요강 71쪽~)', 'csat_minimum': '미적용',
         'eligibility': '특수교육대상자', 'evidence_pages': [3]},
    ],
    'schedules_sample': {'type': '전 전형 공통 원서접수', 'items': [
        {'item': '인터넷 원서접수', 'date': '2026.9.7.(월) 10:00 ~ 9.9.(수) 17:00'},
        {'item': '서류제출 마감', 'date': '2026.9.10.(목) 17:00'},
        {'item': '논술시험', 'date': '2026.10.10.(토)'},
        {'item': '활동우수형 1단계 발표', 'date': '2026.11.16.(월)'},
        {'item': '활동우수형 면접(인문·통합/자연)', 'date': '2026.11.21.(토)/11.22.(일)'},
        {'item': '최종합격자 발표', 'date': '2026.12.18.(금)'}]},
    'unresolved': ['모집요강 Ⅱ부 전형별 모집단위 테이블(수시+정시 통합 레이아웃) 컬럼 정렬 자동 파싱 실패 → 시행계획 테이블로 대체 확보(전공별 수시 인원만)']})

write('yonsei_2027_plan.json', {
    'document': meta('yon_plan27', {'verification': yon_checks}),
    'departments': yon_rows})

write('yonsei_2028_plan.json', {
    'document': meta('yon_plan28', {'verification': {
        'underwood_table_rowsum_check': '144=114+30, 15=10+5, 143=120+23, 70=50+20, 합계 392=314+78 (일치)',
        'underwood_2027_check': '364=175+69+120 (일치)'}}),
    'summary_2028': {
        'changes': [
            '학생부교과전형[추천형]: 일괄합산(교과100) → 단계별 전형(1단계 500%, 2단계 교과80+서류20)',
            '학생부종합전형 세부전형 개편: 활동우수형+국제인재 통합→ 종합인재형(서류70+면접30+수능최저*), 일반/국제→ 탐구인재형(서류60+면접40)',
            '논술전형 전 모집단위 수능최저 적용',
            '언더우드국제대학 선발 전형 변경(2028: 종합인재형 314 + 탐구인재형(국제) 78)'],
        'admission_type_totals': {'종합인재형_underwood': 314, '탐구인재형국제_underwood': 78},
        'csat_minimum_notes': '종합인재형 일부 모집단위(언더우드학부 인문·사회, 생명과학공학) 미적용'}})

write('skku_2027_susi.json', {
    'document': meta('skku', {'verification': {
        'type_total_sum_check': '1487+419+376+96=2378 (일치)',
        'ratio_check': '35.8+10.1+9.0+2.3=57.2%',
        'subtype_columns': 'UNRESOLVED — 요약표 세부전형 값(329/589/196/3/155/28)이 소계 1,487과 재현 불일치, PDF 육안 재확인 필요'}}),
    'admission_types': [
        {'name': '학생부종합(서류형: 융합인재·탐구인재·기회균형·특성화고졸재직자)', 'applicant_total': None,
         'method': '서류100(기회균형·지역인재는 지원자격 심사 포함)',
         'csat_minimum': '융합인재 적용(3개 영역 등급합 6), 탐구인재·기회균형 미적용',
         'evidence_pages': [7]},
        {'name': '학생부종합(면접형: 성균인재·성균인재-지역인재·과학인재)', 'applicant_total': None,
         'method': '1단계 서류100(배수별) → 2단계 서류70+면접30',
         'csat_minimum': '미적용(성균인재 계열별 상이, 요강 확인)', 'evidence_pages': [7]},
        {'name': '학생부교과(추천인재)', 'applicant_total': 419,
         'method': '학생부100+수능최저',
         'csat_minimum': '인문·사회계열 합7 / 자유전공·글로벌·전자의류 등 합6(3개 영역)',
         'eligibility': '학교장 추천', 'evidence_pages': [7, 11]},
        {'name': '논술위주(언어형·수리형)', 'applicant_total': 376,
         'method': '논술100+수능최저',
         'csat_minimum': '대부분 모집단위 3개 영역 등급합 6, 첨단학과·의예과 등 합5',
         'evidence_pages': [7, 11]},
        {'name': '실기/실적(예체능특기자·실기우수자)', 'applicant_total': 96,
         'method': '실기·서류(요강 60쪽~)', 'csat_minimum': '미적용', 'evidence_pages': [8]}],
    'totals_by_category': {'학생부종합': 1487, '학생부교과': 419, '논술위주': 376, '실기/실적': 96, 'sum': 2378},
    'schedules': {'items': [
        {'item': '원서접수', 'date': '2026.9.8.(화) 10:00 ~ 9.11.(금) 18:00'},
        {'item': '온라인 입력/서류제출', 'date': '2026.9.8.(화) 10:00 ~ 9.12.(토) 14:00'},
        {'item': '추천대상자 입력(학생부교과)', 'date': '2026.9.14.(월) ~ 9.18.(금)'},
        {'item': '논술시험(언어형/수리형)', 'date': '2026.11.21.(토) ~ 11.22.(일)'},
        {'item': '최초합격자 발표', 'date': '2026.12.18.(금) 이전'},
        {'item': '최초합격자 등록(온라인 문서등록)', 'date': '2026.12.21.(월) 10:00 ~ 12.23.(수) 16:00'}]},
    'unresolved': ['모집인원 총괄표의 전공×전형 컬럼 매핑(공백 생략 레이아웃) 자동 파싱 불가 → 육안 검토 대상']})

print('SNU checks:', json.dumps(snu_checks, ensure_ascii=False))
print('YON plan checks:', json.dumps(yon_checks['column_totals'], ensure_ascii=False),
      yon_checks['vs_type_summary'])
