# -*- coding: utf-8 -*-
"""한양대 2027 수시 모집인원 총괄표(parsed via find_tables, pages 10-11) -> JSON"""
import json, re, io, sys

import pymupdf

PDF = "data/raw/pdfs/hanyang_2027_susi.pdf"
OUT = "data/parsed/univ_sample/hanyang_2027_susi.json"

TYPE_COLS = [
    ("학생부교과추천형", 4),
    ("학생부종합추천형", 5),
    ("학생부종합서류형", 6),
    ("학생부종합면접형", 7),
    ("학생부종합고른기회", 8),
    ("학생부종합사회통합", 9),
    ("특성화고졸재직자정원외", 10),
    ("논술우수자", 11),
    ("실기실적", 12),
]
COL_TOTAL = 13


def num(cell):
    s = (cell or "").strip().replace(",", "")
    if not s:
        return 0, False
    m = re.fullmatch(r"\((\d+)\)", s)
    if m:
        return int(m.group(1)), True
    m = re.fullmatch(r"(\d+)", s)
    if m:
        return int(m.group(1)), False
    return None, False


def main():
    log = io.StringIO()
    doc = pymupdf.open(PDF)
    rows_raw = []
    for pno in (9, 10):
        tables = doc[pno].find_tables()
        picked = [t for t in tables.tables if t.col_count == 14]
        assert len(picked) == 1, f"page {pno+1}: expected 1 table with 14 cols, got {len(picked)}"
        extracted = picked[0].extract()
        assert len(extracted) >= 4
        rows_raw.extend(extracted[3:])  # 3행 헤더(개행 포함) 건너뜀
        print(f"page {pno+1}: {len(extracted)} rows", file=log)

    colleges = []
    cur_college = None
    depts = []
    totals_row = None
    for r in rows_raw:
        c0 = (r[0] or "").strip()
        name = re.sub(r"\s+", "", (r[2] or ""))
        if name in ("합계", "계"):
            totals_row = r
            continue
        name = (r[2] or "").strip()
        if name == "모집단위(학과)":
            continue
        if not any((c or "").strip() for c in r):
            continue
        if depts and (not (r[3] or "").strip() or not (r[COL_TOTAL] or "").strip()):
            # 병합행 속행(한양인터칼리지학부 자연/인문): 직전 행에 가산
            prev = depts[-1]
            for tname, idx in TYPE_COLS:
                v, _oq = num(r[idx])
                assert v is not None, f"{prev['department']} 속행 col {idx}: {r[idx]!r}"
                prev["by_type"][tname] += v
            prev["merged_note"] = "한양인터칼리지학부(자연)+(인문) 병합행(모집인원 252·수시계 202 공통)"
            continue
        if c0:
            cur_college = c0
        n_plan, oq_plan = num(r[3])
        vals = {}
        for tname, idx in TYPE_COLS:
            v, _oq = num(r[idx])
            assert v is not None, f"{name!r} college={c0!r} r0={r[0]!r} r1={r[1]!r} col {idx}: {r[idx]!r}"
            vals[tname] = v
        su, _ = num(r[COL_TOTAL])
        assert su is not None, f"{name} 수시계: {r[COL_TOTAL]!r}"
        depts.append({
            "college": re.sub(r"\s+", "", cur_college or ""),
            "track": (r[1] or "").strip(),
            "department": re.sub(r"\s*\n\s*", "", name),
            "plan_total": n_plan if n_plan is not None else 0,
            "plan_out_of_quota_flag": oq_plan,
            "by_type": vals,
            "susi_sum": su,
        })
    # 병합행 재검증
    for d in depts:
        s = sum(d["by_type"].values())
        assert s == d["susi_sum"], f"{d['department']}: 행합 {s} != 수시계 {d['susi_sum']}"

    # 합계행 검증
    assert totals_row is not None, "합계 row not found"
    agg = {t: 0 for t, _ in TYPE_COLS}
    agg_sum = 0
    plan_in = plan_out = 0
    for d in depts:
        for t in agg:
            agg[t] += d["by_type"][t]
        agg_sum += d["susi_sum"]
        if d["plan_out_of_quota_flag"]:
            plan_out += d["plan_total"]
        else:
            plan_in += d["plan_total"]

    expected_in = {
        "학생부교과추천형": 340, "학생부종합추천형": 300, "학생부종합서류형": 496,
        "학생부종합면접형": 138, "학생부종합고른기회": 113, "학생부종합사회통합": 5,
        "특성화고졸재직자정원외": 0, "논술우수자": 229, "실기실적": 110,
    }
    # 정원외 행 분리 검증: 합계 198 / (6)(22)(158)(4) / 190
    out_rows = [d for d in depts if d["plan_out_of_quota_flag"]]
    in_rows = [d for d in depts if not d["plan_out_of_quota_flag"]]
    agg_in = {t: sum(d["by_type"][t] for d in in_rows) for t, _ in TYPE_COLS}
    agg_out = {t: sum(d["by_type"][t] for d in out_rows) for t, _ in TYPE_COLS}
    for t, exp in expected_in.items():
        assert agg_in[t] == exp, f"정원내 {t}: {agg_in[t]} != {exp}"
    assert sum(agg_in.values()) == 1731, sum(agg_in.values())
    exp_out = {"학생부교과추천형": 6, "학생부종합서류형": 22,
               "특성화고졸재직자정원외": 158, "논술우수자": 4}
    for t, exp in exp_out.items():
        assert agg_out[t] == exp, f"정원외 {t}: {agg_out[t]} != {exp}"
    assert sum(agg_out.values()) == 190, sum(agg_out.values())
    assert plan_out == 198, plan_out
    assert plan_in == 3020, plan_in

    print(f"rows={len(depts)} in={len(in_rows)} out={len(out_rows)}", file=log)
    print(f"수시계合计 in+out={sum(agg_in.values())+sum(agg_out.values())}", file=log)

    result = {
        "university": "한양대학교(서울)",
        "academic_year": 2027,
        "cycle": "수시",
        "doc_type": "2027학년도 수시모집 요강 - 수시 모집인원 총괄표",
        "source_url": "https://go.hanyang.ac.kr (pdfDown.do?menu=mojib&file_no=502&type=pdf)",
        "verification_status": "NORMALIZED",
        "exposure": "HIDDEN",
        "n_departments": len(depts),
        "totals": {
            "plan_in_quota": plan_in,
            "plan_out_of_quota": plan_out,
            "susi_in_quota": sum(agg_in.values()),
            "susi_out_of_quota": sum(agg_out.values()),
            "by_type_in_quota": agg_in,
            "by_type_out_of_quota": agg_out,
            "visual_check": "페이지 10-11 렌더링 이미지(hy_p10.png, hy_p11.png)로 합계행 대조 확인",
        },
        "departments": depts,
        "notes": [
            "요강 PDF 텍스트 레이어가 서브셋 폰트이나 find_tables 추출은 한글·숫자 모두 정상이었으며 렌더링 이미지로 시각 검증 병행",
            "모집인원 괄호 (n) = 정원외 트랙(반도체공학과 32, 기술혁신산업융합학부 158 등)",
            "정시 모집인원은 요강에 미포함(수시 총괄만)",
        ],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    with open("tmp_hy_parse_log.txt", "w", encoding="utf-8") as f:
        f.write(log.getvalue())
    print("OK", OUT)


if __name__ == "__main__":
    main()
