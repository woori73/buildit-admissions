# -*- coding: utf-8 -*-
"""2단계보완: seed ipsi_schedules 66행에 source_document_key 백필 + parsed schedules 대조.
연결 규칙(추정 없음): 대학+적용학년도 → 해당 2027 수시 요강 문서 키는 유일하다(ipsi_documents).
판정: normalized(item/date) 완전일치 EXACT, 부분포함 FUZZY, 없음 NONE, parsed schedule 부재 NOSC.
seed 행에는 키·대조결과·매칭 인덱스만 추가하며 item/date 원문은 변경하지 않는다."""
import json, io, re, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def L(p):
    return json.load(io.open(os.path.join(BASE, p), encoding='utf-8'))

UNIV_DOC = {
    'SNU': ('doc_snu_2027_susi', 'snu_2027_susi.json', 'schedules_sample'),
    'YONSEI': ('doc_yon_2027_susi', 'yonsei_2027_susi.json', 'schedules_sample'),
    'SKKU': ('doc_skku_2027_susi', 'skku_2027_susi.json', 'schedules'),
    'KOREA': ('doc_korea_2027_susi', 'korea_2027_susi.json', 'schedules'),
    'HANYANG': ('doc_hanyang_2027_susi', 'hanyang_2027_susi.json', 'schedules'),
    'KHU': ('doc_khu_2027_susi', 'khu_2027_susi.json', 'schedules'),
    'INHA': ('doc_inha_2027_susi', 'inha_2027_susi.json', 'schedules'),
}

def norm(s):
    s = str(s or '')
    s = re.sub(r'[.\s()（）:：~〜ᄀ-힣a-zA-Z]0', '', s)  # no-op guard
    s = re.sub(r'[^0-9]', '', s.split('~')[0]) if False else s
    return s

def key_pair(item, date):
    """compare on digit signature + item text normalized"""
    digits = re.sub(r'[^0-9]', '', str(date))
    it = re.sub(r'\s+', '', str(item))
    return digits, it

def get_entries(d, attr):
    s = d.get(attr)
    if isinstance(s, dict):
        items = s.get('items')
        return items if isinstance(items, list) else []
    if isinstance(s, list):
        return s
    return []

def main():
    seedp = os.path.join(BASE, 'data', 'seed', 'ipsi_seed_univ_sample.json')
    sd = json.load(io.open(seedp, encoding='utf-8'))
    parsed = {u: [key_pair(e.get('item') or e.get('stage'), e.get('date') or e.get('period'))
                  for e in get_entries(L('data/parsed/univ_sample/' + fn), attr)]
              for u, (dk, fn, attr) in UNIV_DOC.items()}
    stats = {'EXACT': 0, 'FUZZY': 0, 'NONE': 0}
    for r in sd['ipsi_schedules']:
        u = r['university_code']
        dk, fn, attr = UNIV_DOC[u]
        kp = key_pair(r.get('item'), r.get('date'))
        match = None
        for i, (dg, it) in enumerate(parsed[u]):
            if kp[0] == dg and kp[1] == it:
                match = ('EXACT', i); break
        if match is None:
            for i, (dg, it) in enumerate(parsed[u]):
                if kp[0] and kp[0] == dg:
                    match = ('FUZZY', i); break
        if match is None:
            for i, (dg, it) in enumerate(parsed[u]):
                if kp[1] and (kp[1] in it or it in kp[1]):
                    match = ('FUZZY', i); break
        r['source_document_key'] = dk
        r['schedule_backfill'] = '2026-10-13 대학+학년도 유일 문서 매핑(ipsi_documents), item/date 원문 무변경'
        if match:
            r['schedule_match'] = match[0]
            r['schedule_match_index'] = match[1]
            stats[match[0]] += 1
        else:
            r['schedule_match'] = 'NONE'
            stats['NONE'] += 1
    json.dump(sd, io.open(seedp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    out = {'backfilled': len(sd['ipsi_schedules']), 'match_stats': stats,
           'rule': 'EXACT=항목·날짜 완전일치 FUZZY=날짜 또는 항목 부분일치 NONE=parsed에 대응 없음(문서 키는 부여, 승격 후보 제외)'}
    print(out)

if __name__ == '__main__':
    main()
