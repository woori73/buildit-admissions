# -*- coding: utf-8 -*-
"""경희대 2027 수시 전형별 모집인원 표(PDF p20-21) -> JSON, 총계행 검증"""
import json, re, io
import pymupdf

PDF = "data/raw/pdfs/khu_2027_susi.pdf"
OUT = "data/parsed/univ_sample/khu_2027_susi.json"

# col -> (key, in/out quota)
TYPE_COLS = [
    (2, "학생부교과_지역균형", "in"),
    (3, "학생부교과_기회균형I_재직자", "out"),
    (4, "학생부종합_네오르네상스", "in"),
    (5, "학생부종합_기회균형I", "in"),
    (6, "학생부종합_기회균형I_장애인등", "out"),
    (7, "학생부종합_기회균형II", "in"),
    (8, "논술우수자", "in"),
    (9, "실기우수자", "in"),
]
COL_TRACK = 10


def num(cell):
    s = (cell or "").strip().replace(",", "")
    if not s:
        return 0, None
    if s.startswith("통합선발"):
        return 0, s
    m = re.fullmatch(r"(\d+)", s)
    assert m, f"bad cell {cell!r}"
    return int(m.group(1)), None


def main():
    log = io.StringIO()
    doc = pymupdf.open(PDF)
    rows = []
    grand = None
    for pno in (19, 20):
        tb = [t for t in doc[pno].find_tables().tables if t.col_count == 11][0]
        for r in tb.extract()[4:]:  # 4행 헤더
            if (r[0] or "").strip() == "총계":
                grand = r
                continue
            rows.append(r)
        print(f"p{pno+1} rows ok", file=log)

    depts = []
    for r in rows:
        name = re.sub(r"\s*\n\s*", "", (r[0] or "").strip())
        vals = {}
        notes = []
        for idx, key, _q in TYPE_COLS:
            v, tag = num(r[idx])
            vals[key] = v
            if tag:
                notes.append(tag)
        track = re.sub(r"\s+", "", (r[COL_TRACK] or "").strip())
        if not name:
            prev = depts[-1]
            for k, v in vals.items():
                prev["by_type"][k] += v
            prev["sub_major_rows"].append({
                "sub": re.sub(r"\s*\n\s*", "", (r[1] or "").strip()),
                "by_type": vals, "note": notes,
            })
            continue
        depts.append({
            "department": name,
            "sub_or_major": re.sub(r"\s*\n\s*", "", (r[1] or "").strip()),
            "track": track,
            "by_type": vals,
            "notes": notes,
            "sub_major_rows": [],
        })
    # 통합선발 태그는 행 이동 시 소실되지 않게 병합
    # 검증: 열합 == 총계행
    exp = {
        "학생부교과_지역균형": 604, "학생부교과_기회균형I_재직자": 263,
        "학생부종합_네오르네상스": 1076, "학생부종합_기회균형I": 150,
        "학생부종합_기회균형I_장애인등": 15, "학생부종합_기회균형II": 90,
        "논술우수자": 471, "실기우수자": 337,
    }
    # 장애인등(정원외) 열은 학과별 분해 없이 총계 15만 표기(본문은 통합선발 태그)
    NO_DECOMP = {"학생부종합_기회균형I_장애인등"}
    for idx, key, _q in TYPE_COLS:
        g, _ = num(grand[idx])
        assert g == exp[key], f"총계행 자체 불일치 {key}: {g}!={exp[key]}"
        s = sum(d["by_type"][key] for d in depts)
        if key in NO_DECOMP:
            assert s == 0, f"{key}: 학과별 값 없음 전제 무너짐, 합 {s}"
        else:
            assert s == exp[key], f"{key}: 열합 {s} != 총계 {exp[key]}"
        print(f"{key}: {s}", file=log)
    total = sum(exp.values())
    print(f"총 모집인원(정원내+재직자/장애인 정원외 포함)={total}", file=log)

    result = {
        "university": "경희대학교(서울)",
        "academic_year": 2027,
        "cycle": "수시",
        "doc_type": "2027학년도 경희대학교 수시모집 요강 - 전형별 모집인원",
        "source_url": "https://iphak.khu.ac.kr (khuiphakstorage 공식 PDF, 2026.5.13 게시 최종본)",
        "verification_status": "NORMALIZED",
        "exposure": "HIDDEN",
        "n_departments": len(depts),
        "totals": {**exp, "grand_total": total,
                   "check": "8개 열합 = 총계행(604/263/1,076/150/15/90/471/337) 일치"},
        "departments": depts,
        "notes": [
            "기회균형I_재직자(263)·장애인등(15)은 정원외",
            "'통합선발(서울C)/(국제C)' 표기 모집단위는 통합선발 후 배정(원문 태그 보존)",
            "세부전공 병합행은 상위 모집단위 by_type에 가산하고 sub_major_rows에 원값 보존",
            "실기우수자 표의 학부(미술20·무용47·PostModern음악36·스포츠지도96 등) 포함",
        ],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    open("tmp_khu_log.txt", "w", encoding="utf-8").write(log.getvalue())
    print("OK", OUT)


if __name__ == "__main__":
    main()
