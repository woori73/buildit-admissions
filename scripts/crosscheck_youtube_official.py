# -*- coding: utf-8 -*-
"""2단계-2: 유튜브 분석자료(127) vs 공식자료(11문서) 대조.

네 가지로 구분 (우선순위 적용, 각 항목은 정확히 하나의 버킷):
  ② 공식자료와 충돌      : official_ref.status==CONFLICT 또는 classification==DISPUTED
  ① 공식자료와 일치      : status==OFFICIAL_CONFIRMED / CONSISTENT_WITH_OFFICIAL
  ④ 직접 발언 확인 필요  : OFFICIAL_FACT 주장이나 공식 대조 미완(status NEEDS_OFFICIAL_DOC/UNSUPPORTED)
  ③ 전문가 의견·해석     : 그 외(EXPERT_ANALYSIS/STRATEGY/PREDICTION/OUTDATED)
오버레이: 전 항목 speech_verified=false(본 네트워크 자막 미확보) — ①③에 들어가도
'발언 원문 미확인·설명란/챕터 라벨 기반 복원' 라벨을 유지한다.
원칙: 유튜브 내용이 공식자료를 덮어쓰지 않는다. 공식 원문 보유 여부는 본 저장소 기준으로 별도 표기.
읽기 전용 — data/youtube/* 및 data/parsed/* 를 변경하지 않는다."""
import json, io, re, os, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(p):
    return json.load(io.open(os.path.join(BASE, p), encoding='utf-8'))

analyses = load('data/youtube/analyses.json')
items = analyses.get('analyses') if isinstance(analyses, dict) else analyses
conflicts = load('data/youtube/conflicts.json')
conf_list = conflicts.get('conflicts') if isinstance(conflicts, dict) else conflicts
conf_by_id = {c['id']: c for c in conf_list}

UNIV_ALIASES = {
    'SNU': ['서울대'],
    'YONSEI': ['연세대', '연세'],
    'KOREA': ['고려대', '고려'],
    'SKKU': ['성균관대', '성균'],
    'HANYANG': ['한양대', '한양'],
    'KHU': ['경희대', '경희'],
    'INHA': ['인하대', '인하'],
}
# 본 저장소 공식 원문 보유 (대학: [(학년도, 문서)])
HELD = {
    'SNU': ['2027'], 'YONSEI': ['2027', '2028'], 'KOREA': ['2027'],
    'SKKU': ['2027'], 'HANYANG': ['2027'], 'KHU': ['2027'], 'INHA': ['2027'],
}

# 2027 보유 수치 앵커(판정용 — docs/ANALYSIS 및 validate_official_data.py 결과에서 확인된 값)
SNU_2027 = {'지역균형_1단계': '2배수', '지역균형_추천': '고교별 2명', '지역균형_최저': '3개 영역 등급합 7',
            '지역균형_모집': 414}

SPOTCHECKS = {
    'YT-A001': ('①', '대교협 2028 시행계획 수치(348,789/수시80.8%) — 교육부·교비트 보도로 채널이 외부 확인. 본 저장소에 대교협 1차 문서 미보유: 인용 시 공식 URL과 함께 "시행계획 단계, 최종 요강 전" 고지.'),
    'YT-A012': ('①-조건부', '2028 정시 학생부 반영 대학 목록. 본 저장소 2028 원문 보유 대학은 연세대(시행계획)뿐 — 서울·한양·고려·경희·성균 2028 시행계획 미대조. YT-C001(비율 수치 미확정) 병기.'),
    'YT-A016': ('판정불가', '한양 2028 교과 서류 40%: 한양 2028 시행계획 원문 미보유(2027 수시 요강만 보유). confidence=LOW → 개인 배치 사용 금지.'),
    'YT-A019': ('판정불가', '대학별 2028 전형 변경 열거(신설·폐지): 각 대학 2028 시행계획 원문 대조 필요(연세 외 미보유). 2026-05 시점 정보로 최종 요강 전.'),
    'YT-A020': ('②', 'YT-C005 연결. "분리 시도/재수 불리"는 확정 제도 사실이 아닌 진영 간 해석 차이 — 양측 근거 병행 안내, 단정 답변 금지.'),
    'YT-A056': ('충돌의혹', '정정문 전제 "지역균형 1단계는 원래 3배수" ↔ 본 저장소 서울대 2027 요강: 1단계 2배수·고교별 추천 2명(snu_2027_susi admission_types). 2028 "원래"를 2027 원문이 반박: 정정 내용도 서울대 2028 시행계획 원문 재확인 전까지 미검증. 추천 2→3명·728명 확대는 2028 사안으로 대조 불가(미보유).'),
    'YT-A071': ('부분대조', '성균관대 2027 "정시" 하이브리드 주장 — 본 저장소는 성균관대 2027 수시 요강만 보유(정시 요강 미보유). 수시 문서상 성균인재(사범대 포함) 면접형 수능최저 "미적용(계열별 상이)"과 직접 충돌하지 않으나, 2027 정시 원문 없이는 일치도 확인 불가.'),
    'YT-A072': ('부분대조', '연세대 2027 논술 재시험 여파 모집감소: 보유 문서(수시 요강 Ⅱ부)는 발표 시점 확정 인원이며 "재시험 여파 감소"의 전후 비교 대상 공지가 없음. 연세대 문서 notes에 재시험 관련기재 없음 → 확인 불가 항목으로 유지.'),
    'YT-A073': ('②-수치', 'YT-C010: "수시 80.3%" vs 대교협 공표 80.8%(YT-A001) — 같은 사안의 수치 불일치 기록. 원문(시행계획 공표) 미보유로 최종 판정 보류.'),
}

def text_of(a):
    parts = [a.get('claim') or '', a.get('evidence') or '']
    orf = a.get('official_ref') or {}
    parts += [orf.get('note') or '', orf.get('url') or '']
    ent = a.get('entities') or {}
    for v in ent.values():
        if isinstance(v, list):
            parts += [str(x) for x in v]
    return ' '.join(parts)

def univs_of(a):
    t = text_of(a)
    return [code for code, al in UNIV_ALIASES.items() if any(x in t for x in al)]

def bucket_of(a):
    st = (a.get('official_ref') or {}).get('status')
    cl = a.get('classification')
    if st == 'CONFLICT' or cl == 'DISPUTED':
        return '②_충돌'
    if st in ('OFFICIAL_CONFIRMED', 'CONSISTENT_WITH_OFFICIAL'):
        return '①_공식일치'
    if cl == 'OFFICIAL_FACT':
        return '④_발언·원문확인필요'
    return '③_전문가의견해석'

def official_held_status(a, univs):
    yr = str(a.get('academic_year') or '')
    if not univs:
        return None
    if yr in ('2027',):
        return ' 보유(2027 수시 7개교)' if all(yr in HELD[u] for u in univs) else ' 부분보유'
    if yr == '2028':
        held28 = [u for u in univs if '2028' in HELD[u]]
        if len(held28) == len(univs):
            return ' 보유(연세대 2028 시행계획)'
        return ' 미보유(2028 시행계획: 연세 외 각 대학 원문 필요)' if not held28 else ' 부분보유(연세만)'
    return ' 연도외'

def conflict_brief(a):
    out = []
    for cid in (a.get('conflict_ids') or []):
        cf = conf_by_id.get(cid)
        if not cf:
            continue
        out.append({
            'id': cid, 'type': cf.get('type'), 'resolution': cf.get('resolution'),
            'summary': (cf.get('summary') or '')[:150],
            'side_a': (cf.get('side_a') or {}).get('position', '')[:120],
            'side_b': (cf.get('side_b') or {}).get('position', '')[:120],
            'counseling_rule': cf.get('counseling_rule'),
        })
    return out

rows = []
tally = {}
for a in items:
    b = bucket_of(a)
    us = univs_of(a)
    orf = a.get('official_ref') or {}
    eb = a.get('evidence_basis') or ''
    inferred = eb.startswith('INFERRED_')
    row = {
        'id': a['id'], 'video_id': a.get('video_id'), 'bucket': b,
        'classification': a.get('classification'), 'academic_year': a.get('academic_year'),
        'official_ref_status': orf.get('status'), 'confidence': a.get('confidence'),
        'evidence_basis': eb, 'speech_verified': bool(a.get('speech_verified')),
        'univ_codes': us,
        'topics': a.get('topics') or [],
        'conflicts': conflict_brief(a),
        'claim': (a.get('claim') or ''),
        'conflict_ids': a.get('conflict_ids') or [],
        'label_overlays': [
            l for l in [
                '발언 원문 미확인(자막 미확보·설명란/챕터 라벨 기반 복원)' if inferred else
                '게시 텍스트(설명란 전문) 근거 — 영상 발언 자체는 미확인',
                'LOW신뢰도: 개인 합격·불합격 배치 사용 금지' if a.get('confidence') == 'LOW' else None,
                'confidence_capped(공식 1차 문장 아님)' if a.get('confidence_capped') else None,
            ] if l
        ],
    }
    oh = official_held_status(a, us)
    if oh:
        row['official_doc_ours'] = oh
    if a['id'] in SPOTCHECKS:
        row['spotcheck'] = {'verdict': SPOTCHECKS[a['id']][0], 'note': SPOTCHECKS[a['id']][1]}
    tally[b] = tally.get(b, 0) + 1
    rows.append(row)

by_bucket_univ = {}
for r in rows:
    if r['univ_codes']:
        by_bucket_univ.setdefault(r['bucket'], {'total': 0})
        by_bucket_univ[r['bucket']]['total'] += 1

evidence_overlay = {
    'speech_verified_true': sum(1 for r in rows if r['speech_verified']),
    'inferred_basis': sum(1 for r in rows if (r['evidence_basis'] or '').startswith('INFERRED_')),
    'as_published_text': sum(1 for r in rows if r['evidence_basis'] == 'AS_PUBLISHED_TEXT'),
}
conflict_usage = {cid: sorted({r['id'] for r in rows if cid in r['conflict_ids']}) for cid in conf_by_id}

b2 = [r for r in rows if r['bucket'] == '②_충돌']
b2_res = {}
for r in b2:
    key = ','.join(sorted({c['resolution'] for c in r['conflicts']})) or 'NO_CONFLICT_ID'
    b2_res[key] = b2_res.get(key, 0) + 1
b2_audit = {
    'count': len(b2),
    'with_conflict_link': sum(1 for r in b2 if r['conflicts']),
    'without_conflict_link': [r['id'] for r in b2 if not r['conflicts']],
    'with_counseling_rule': sum(1 for r in b2 if any(c.get('counseling_rule') for c in r['conflicts'])),
    'resolution_dist': b2_res,
    'level_note': '②항목 검증 수준 = (a)충돌대장 연결 여부 (b)resolution 상태 (c)counseling_rule 보유 (d)우리 공식 원문 보유 시 수치 대조(spot_check). RESOLVED_BY_CORRECTION(YT-C009)도 보유 2027 원문과 전제 상충 시 별도 충돌의혹 기록.',
}

out = {
    'meta': {
        'task': 'stage2-2 유튜브 분석자료 vs 공식자료 4분류 대조',
        'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
        'inputs_readonly': ['data/youtube/analyses.json', 'data/youtube/conflicts.json',
                              'data/parsed/univ_sample/*.json(보유·수치 앵커 참조)'],
        'bucket_rule': '우선순위: CONFLICT·DISPUTED→② / OFFICIAL_CONFIRMED·CONSISTENT_WITH_OFFICIAL→① / 미대조 OFFICIAL_FACT→④ / 그 외 전문가류→③. 전 항목 speech_verified=false 오버레이 유지.',
        'principle': '유튜브는 보조 설명일 뿐이며 공식자료를 덮어쓰지 않는다. 수치·전형 확정 인용은 항상 보유 공식 문서 우선.',
        'no_promotion': '본 대조는 분류 기록까지 — verification_status 변경 없음(APPROVED 승격 0).',
    },
    'counts': {
        'analyses_total': len(rows),
        'by_bucket': tally,
        'touching_our_7_univs': sum(1 for r in rows if r['univ_codes']),
        'with_conflict_id': sum(1 for r in rows if r['conflict_ids']),
    },
    'evidence_overlay': evidence_overlay,
    'spot_checks': [{'id': k, 'verdict': v[0], 'note': v[1]} for k, v in SPOTCHECKS.items()],
    'conflict_usage': conflict_usage,
    'bucket2_audit': b2_audit,
    'items': rows,
}
dst = os.path.join(BASE, 'data', 'validation', 'youtube_crosscheck.json')
json.dump(out, io.open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('OK', dst)
print('by_bucket', json.dumps(tally, ensure_ascii=False))
print('univ_touch', out['counts']['touching_our_7_univs'], 'conflict_id', out['counts']['with_conflict_id'])
