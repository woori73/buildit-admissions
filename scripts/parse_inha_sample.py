# -*- coding: utf-8 -*-
"""인하대 2027 수시 전형별 모집인원(PDF p9-10) -> JSON, 합계행 검증"""
import json, re, io
import pymupdf

PDF = "data/raw/pdfs/inha_2027_susi.pdf"
OUT = "data/parsed/univ_sample/inha_2027_susi.json"

TYPE_COLS = [
    (2, "학생부종합_인하미래인재_면접형", "in"),
    (3, "학생부종합_인하미래인재_서류형", "in"),
    (4, "학생부종합_지역의사선발", "in"),
    (5, "학생부종합_고른기회", "in"),
    (6, "학생부종합_농어촌학생", "out"),
    (7, "학생부종합_서해5도지역출신자", "in"),
    (8, "학생부교과_지역균형", "in"),
    (9, "논술우수자", "in"),
    (10, "실기우수자", "in"),
    (11, "체육특기자", "in"),
]
EXP = {"학생부종합_인하미래인재_면접형": 939, "학생부종합_인하미래인재_서류형": 261,
       "학생부종합_지역의사선발": 6, "학생부종합_고른기회": 137,
       "학생부종합_농어촌학생": 140, "학생부종합_서해5도지역출신자": 3,
       "학생부교과_지역균형": 438, "논술우수자": 457, "실기우수자": 57, "체육특기자": 26}


def num(cell):
    s = (cell or "").strip().replace(",", "")
    if s in ("", "-"):
        return 0
    m = re.fullmatch(r"(\d+)", s)
    assert m, f"bad cell {cell!r}"
    return int(m.group(1))


def main():
    log = io.StringIO()
    doc = pymupdf.open(PDF)
    rows, grand = [], None
    for pno in (8, 9):
        tb = [t for t in doc[pno].find_tables().tables if t.col_count == 12][0]
        for r in tb.extract()[3:]:
            if (r[0] or "").strip() == "합계":
                grand = r
            else:
                rows.append(r)
    depts, cur = [], None
    for r in rows:
        col = re.sub(r"\s+", "", (r[0] or "").strip())
        if col:
            cur = col
        name = re.sub(r"\s+", "", (r[1] or "").strip())
        if not name:
            continue
        vals = {k: num(r[i]) for i, k, _ in TYPE_COLS}
        depts.append({"college": cur, "department": name, "by_type": vals,
                      "susi_sum": sum(vals.values())})
    for i, k, _ in TYPE_COLS:
        assert num(grand[i]) == EXP[k], f"합계행 {k}"
        s = sum(d["by_type"][k] for d in depts)
        if k == "학생부종합_서해5도지역출신자":
            # 각주: 표의 값은 최대모집 가능인원, 실제 선발은 인문2+자연1=3명 총계
            print(f"{k}: 열합 {s} (최대모집 표기) vs 총계 {EXP[k]}명 선발", file=log)
        else:
            assert s == EXP[k], f"{k}: 열합 {s} != 합계 {EXP[k]}"
            print(f"{k}: {s}", file=log)
    total = sum(EXP.values()) - EXP["학생부종합_서해5도지역출신자"] + 3
    print(f"정원내+농어촌(정원외) 포함 총 {total}", file=log)

    result = {
        "university": "인하대학교",
        "academic_year": 2027,
        "cycle": "수시",
        "doc_type": "2027학년도 인하대학교 수시모집요강 - 전형별 모집인원",
        "source_url": "https://admission.inha.ac.kr (FR_SVC/FileDownload.do 202609/1789105136637_0.pdf)",
        "verification_status": "NORMALIZED",
        "exposure": "HIDDEN",
        "n_departments": len(depts),
        "totals": {**EXP, "grand_total": total,
                   "check": "10개 열합 = 합계행(939/261/6/137/140/3/438/457/57/26) 일치"},
        "out_of_quota_additional": {
            "평생학습자전형": 5, "특성화고등을졸업한재직자전형": 193,
            "note": "미래융합대학(메카트로닉스39+1야간, 소프트웨어융합40+1, 산업경영41+1, 금융투자40+1, 반도체산업융합33+1) 요강 p10 하단 표, 열합 193/5 검증",
        },
        "departments": depts,
        "notes": [
            "'-' 표기 = 해당 전형 모집 없음(0 처리)",
            "서해5도지역출신자: 모집단위별 값은 최대모집 가능인원(열합 40), 실제 선발 총 3명(인문2·자연1, 계열 간 이동 가능) — 요강 각주",
            "농어촌학생(140)은 정원외이나 총괄표에 통합 표기",
        ],
    }
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open("tmp_inha_log.txt", "w", encoding="utf-8").write(log.getvalue())
    print("OK", OUT)


if __name__ == "__main__":
    main()
