#!/usr/bin/env python3
"""수집 후보 36건 분류 + 적용학년도 누락 근거 조사 결과물 생성.

출력: data/parsed/collection_classification.json
- category: OFFICIAL_RULE_NATIONAL(국가 기본사항) / OFFICIAL_CONTEXT(기관 공식문서지만 대입규정 아님) /
            NON_OFFICIAL_RULE(EBS 해설·강좌·이벤트) / NOT_ADMISSIONS(대입 무관) / NON_DOCUMENT(목록·네비 페이지)
- year_evidence: TITLE_YEAR(제목 연도) / ATTACHMENT_NAME(첨부파일명) / PRESS_CONTEXT(보도 날짜) / NOT_APPLICABLE / NONE
- disposition: KEEP_* / EXCLUDE_* ; 상담 검색 노출은 APPROVED 전용 게이트 유지(여기서 승격 없음).
"""
import io, re, json, os, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = datetime.datetime.now().astimezone().isoformat(timespec='seconds')

docs = []
for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'parsed', 'discovery_*.json'))):
    if 'state' in f:
        continue
    d = json.load(io.open(f, encoding='utf-8'))
    if isinstance(d, list):
        docs += d

art = {}
for f in glob.glob(os.path.join(ROOT, 'data', 'parsed', 'articles', '*.json')):
    a = json.load(io.open(f, encoding='utf-8'))
    art[a.get('url_hash', '')[:24]] = a

YE = re.compile(r'(20(?:2[4-9]|3[01]))학년도')
Y2 = re.compile(r'20(?:2[4-9]|3[01])')

def classify(d):
    t = d.get('title', '') or ''
    src = d.get('source_key')
    h = d.get('url_hash', '')
    item = {
        'url': d.get('url'), 'title': t, 'source_key': src, 'url_hash': h,
        'board_name': d.get('board_name'),
    }
    a = art.get(h[:24])
    if a:
        item['extracted'] = True
        item['attachments'] = [x['name'] for x in a.get('attachments', [])][:4]
        if a.get('academic_year'):
            item['applicable_academic_year'] = a['academic_year']
            item['year_evidence'] = 'TITLE_YEAR+ATTACHMENT_NAME'
            item['verification_status_now'] = a.get('verification_status')
    # 규칙 판정
    if src == 'kcue':
        if YE.search(t) and ('입학전형기본사항' in t or '수시모집' in t):
            item['category'] = 'OFFICIAL_RULE_NATIONAL'
            item.setdefault('applicable_academic_year', int(YE.search(t).group(1)))
            item.setdefault('year_evidence', 'TITLE_YEAR')
            item['disposition'] = 'KEEP_AS_NATIONAL_POLICY'
        elif t == '대학입학':
            item['category'] = 'NON_DOCUMENT'
            item['year_evidence'] = 'NOT_APPLICABLE'
            item['disposition'] = 'EXCLUDE_NON_DOCUMENT'
        elif '박람회' in t:
            item['category'] = 'NOT_ADMISSIONS'
            item['year_evidence'] = 'PRESS_CONTEXT'
            item['note'] = '행사 보도자료(온라인 2026-08-13), 대입 적용학년도 없음'
            item['disposition'] = 'EXCLUDE_NOT_ADMISSIONS'
        else:
            item['category'] = 'NOT_ADMISSIONS'
            item['year_evidence'] = 'NOT_APPLICABLE'
            item['note'] = '대교협 일반 공지(행사·융자·설문·타기관 안내) — 대입자료 아님'
            item['disposition'] = 'EXCLUDE_NOT_ADMISSIONS'
    elif src == 'moe':
        item['category'] = 'OFFICIAL_CONTEXT'
        item['year_evidence'] = 'NOT_APPLICABLE'
        item['note'] = '부처 업무계획 — 대학별 전형자료 아님'
        item['disposition'] = 'EXCLUDE_OFFICIAL_CONTEXT'
    elif src == 'ebsi':
        y = YE.search(t) or Y2.search(t)
        item['category'] = 'NON_OFFICIAL_RULE'
        exam_ctx = any(k in t for k in ['수능', '모평', '정시', '수시', '연계교재', '파이널', '봉투모의고사', '표지', '체크포인트', '입결', '학모평'])
        if y and exam_ctx and int(y.group(0)[:4]) in (2027, 2028):
            item['applicable_academic_year'] = int(y.group(0)[:4])
            item['year_evidence'] = 'TITLE_YEAR'
            item['disposition'] = 'KEEP_AS_NONOFFICIAL_CONTEXT'
        else:
            item['year_evidence'] = 'NOT_APPLICABLE'
            item['note'] = '강좌·이벤트·설문 등 — 대입 적용학년도 아님, 상담 검색 제외'
            item['disposition'] = 'EXCLUDE_NONOFFICIAL_EVENT'
    return item

items = [classify(d) for d in docs]
missing_before = 34
resolved = {}
unresolved = []
for it in items:
    if 'applicable_academic_year' in it:
        resolved.setdefault(it['applicable_academic_year'], 0)
        resolved[it['applicable_academic_year']] += 1
    elif it['year_evidence'] in ('NOT_APPLICABLE',):
        resolved.setdefault('_not_applicable', 0)
        resolved['_not_applicable'] += 1
    elif it['year_evidence'] == 'PRESS_CONTEXT':
        resolved.setdefault('_press_context_only', 0)
        resolved['_press_context_only'] += 1
    else:
        unresolved.append(it['title'][:40])

summary = {
    'total': len(items),
    'by_category': {},
    'by_disposition': {},
    'year_resolution': {
        'missing_before': missing_before,
        'resolved_year': {k: v for k, v in resolved.items() if isinstance(k, int)},
        'no_year_applicable(비 대입 문서)': resolved.get('_not_applicable', 0),
        'press_context_only(행사 보도)': resolved.get('_press_context_only', 0),
        'still_unresolved(연도 근거 없음)': len(unresolved),
    },
    'unresolved_titles': unresolved,
    'policy': '적용학년도 미확정·미검증 자료는 APPROVED 금지, 상담 검색 미노출(게이트 유지)',
    'generated_at': NOW,
    'items': items,
}
for it in items:
    summary['by_category'][it['category']] = summary['by_category'].get(it['category'], 0) + 1
    summary['by_disposition'][it['disposition']] = summary['by_disposition'].get(it['disposition'], 0) + 1

out = os.path.join(ROOT, 'data', 'parsed', 'collection_classification.json')
json.dump(summary, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('classification ->', out)
