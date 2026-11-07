#!/usr/bin/env python3
"""2026학년도(지난해) 입시결과 수집본 → 상담 적재용 시드.

입력: data/parsed/prior_results/{key}_2026_prior.json (대학 입학처 공식 입시결과에서 뽑은 행, 수집 지시서 형식)
      data/seed/ipsi_seed_univ_sample.json (대학 코드·2027 전형/모집단위 이름 대조용)
출력: data/seed/ipsi_seed_prior_2026.json  — 관리자 화면 load/seed로 올리는 별도 시드
      data/seed/build_report.json          — prior_results 항목(건수·gaps·검증) 추가

규칙(지시서 §3·§4):
- 원문 이름·지표명 그대로. 2027 이름과 정확히 같을 때만 linked_2027_* 를 채운다.
- 원문에 없는 값은 null. 지표를 합치거나 환산하지 않는다.
- extra_admitted_count는 충원 '인원'일 때만. 원문이 마지막 예비번호만 주는 대학은 그 값을 원문 이름의 지표 행(OTHER)으로 옮긴다.
- 범위: GRADE 1~9, PERCENTILE 0~100, 경쟁률 ≥0, 인원은 0 이상 정수. 벗어나면 행을 빼고 실패로 보고한다.
- 모든 행은 source_url과 문서 키가 있어야 한다.
- authoritative_universities를 넣지 않는다 — 이 시드를 올려도 기존 2027 모집요강 자료는 보관되지 않는다.
- 값이 null인 칸은 시드에서 뺀다(적재기는 없는 칸을 null로 읽는다). 파일은 data/seed/prior_2026/ 아래 여러 개로 나눈다
  (한 파일 약 4.5M자 이하). 순서대로 하나씩 load/seed 한다 — 행 단위 자연키라 순서·재적재와 무관하게 중복되지 않는다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIOR_DIR = os.path.join(ROOT, "data", "parsed", "prior_results")
MAIN_SEED = os.path.join(ROOT, "data", "seed", "ipsi_seed_univ_sample.json")
OUT_DIR = os.path.join(ROOT, "data", "seed", "prior_2026")
# 관리자 화면 적재는 시드 전체를 JSON 문자열 하나로 보낸다. 요청·파서 한도에 여유를 두려고 파일당 글자 수를 제한한다.
MAX_CHARS_PER_FILE = 4_500_000
MAX_ROWS_PER_PART = 6000
REPORT = os.path.join(ROOT, "data", "seed", "build_report.json")

RESULT_YEAR = 2026
COUNSEL_YEAR = 2027  # 승격·검색 단위가 되는 상담 학년도
# OTHER: 원문에 수시·정시 구분이 없는 학교(예: 한국예술종합학교 — 대교협 수시·정시 체계 밖 자체 입시)
ROUND_LABEL = {"SUSI": "수시", "JEONGSI": "정시", "OTHER": "수시·정시 구분 없음(학교 자체 입시)"}

# 원문 열이 '충원 인원'이 아니라 '마지막 예비번호'인 대학: extra_admitted_count → 이 이름의 지표 행으로 옮긴다.
EXTRA_IS_RESERVE_RANK = {
    "u14": "최종 추합 번호",        # 부산대: 원문 '최종 추합 번호'(최종 추가합격 예비번호)
    "khu": "충원합격 예비번호",     # 경희대: 원문 '충원합격 > 예비번호'
}

MAX_LEN = {"type_name": 200, "department_name": 200, "metric_label": 200, "raw_value_text": 200}


def natural_key(r: dict) -> str:
    raw = "|".join([str(r["result_year"]), r["round_type"], r.get("group") or "", r["type_name"], r["department_name"],
                    r.get("metric_label") or ""])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def range_problem(r: dict) -> str | None:
    for f in ("recruit_count", "applicant_count", "extra_admitted_count"):
        v = r.get(f)
        if v is not None and not is_int(v):
            return f"{f}={v!r} (0 이상 정수 아님)"
    c = r.get("competition_rate")
    if c is not None and (not isinstance(c, (int, float)) or c < 0):
        return f"competition_rate={c!r} (0 미만)"
    v, unit = r.get("metric_value"), r.get("metric_unit")
    if v is not None:
        if not isinstance(v, (int, float)):
            return f"metric_value={v!r} (숫자 아님)"
        if unit == "GRADE" and not (1 <= v <= 9):
            return f"GRADE {v} (1~9 밖)"
        if unit == "PERCENTILE" and not (0 <= v <= 100):
            return f"PERCENTILE {v} (0~100 밖)"
    return None


def load_main_seed():
    with open(MAIN_SEED, encoding="utf-8") as f:
        seed = json.load(f)
    by_key = {u["code"]: u for u in seed["ipsi_universities"]}
    types, depts = {}, {}
    for t in seed.get("ipsi_admission_types", []):
        if str(t.get("academic_year")) == str(COUNSEL_YEAR):
            types.setdefault(t["university_code"], set()).add(t["type_name"])
    for d in seed.get("ipsi_departments", []):
        if str(d.get("academic_year")) == str(COUNSEL_YEAR):
            depts.setdefault(d["university_code"], set()).add(d["department_name"])
    return by_key, types, depts


def build(keys: list[str] | None):
    by_key, types2027, depts2027 = load_main_seed()
    files = sorted(glob.glob(os.path.join(PRIOR_DIR, f"*_{RESULT_YEAR}_prior.json")))
    universities, documents, rows, gaps, per_univ = [], [], [], [], []
    for path in files:
        with open(path, encoding="utf-8") as f:
            src = json.load(f)
        key = src["university_key"]
        if keys and key not in keys:
            continue
        univ = by_key.get(key)
        if univ is None:
            raise SystemExit(f"{path}: 시드에 없는 대학 키 {key}")
        code = univ["university_code"]
        name = univ["name"]
        used_docs = {r["source_document_key"] for r in src["rows"]}
        doc_map = {}
        for d in src["documents"]:
            if d["document_key"] not in used_docs:
                continue  # 행이 없는 검증용 문서(예: xlsx와 같은 내용의 PDF)는 자료로 등록하지 않는다
            new_key = "doc_" + d["document_key"]
            label = ROUND_LABEL[d["round_type"]]
            doc_name = f"{name} {RESULT_YEAR}학년도 {label} 입시결과: {d['document_name']}"[:300]
            doc_map[d["document_key"]] = (new_key, d)
            documents.append({
                "document_key": new_key,
                "document_name": doc_name,
                "applicable_academic_year": COUNSEL_YEAR,
                "result_year": RESULT_YEAR,
                "round_type": d["round_type"],
                "document_type": "입시결과",
                "institution_name": d.get("institution_name") or f"{name} 입학처",
                "source_url": d.get("source_url") or d.get("source_page_url"),
                "source_page_url": d.get("source_page_url"),
                "file_name": d.get("file_name"),
                "file_sha256": d.get("file_sha256"),
                "published_at": d.get("published_at"),
                "verification_status": "NORMALIZED",
            })
        for g in src.get("gaps", []):
            gaps.append({"university_code": code, "university_name": name, **g})

        out_rows, failures, warnings, moved, linked_t, linked_d, seen = [], [], [], 0, 0, 0, {}
        rank_label = EXTRA_IS_RESERVE_RANK.get(key)
        for i, r in enumerate(src["rows"]):
            doc = doc_map.get(r["source_document_key"])
            if doc is None:
                failures.append({"row_index": i, "reason": "문서 키 없음"})
                continue
            new_key, d = doc
            base = {
                "university_code": code, "academic_year": COUNSEL_YEAR, "result_year": RESULT_YEAR,
                "round_type": r["round_type"], "group": r.get("group"),
                "type_name": (r.get("type_name") or "").strip(),
                # 원문에 모집단위 열이 없는 표(전형 단위 결과)는 "전형 전체"로 둔다(빈 이름은 적재기가 건너뛰므로).
                "department_name": (r.get("department_name") or "").strip() or "전형 전체",
                "source_document_key": new_key,
                "source_url": d.get("source_url") or d.get("source_page_url"),
                "institution_name": d.get("institution_name") or f"{name} 입학처",
                "published_at": d.get("published_at"),
                "evidence_pages": r.get("evidence_pages") or [],
            }
            if r.get("round_type") not in ROUND_LABEL or not base["type_name"]:
                failures.append({"row_index": i, "reason": f"round_type/type_name 이상: {r.get('round_type')!r}/{r.get('type_name')!r}"})
                continue
            if not base["source_url"]:
                failures.append({"row_index": i, "reason": "source_url 없음"})
                continue
            t_ok = base["type_name"] in types2027.get(code, ())
            d_ok = base["department_name"] in depts2027.get(code, ())
            base["linked_2027_type_name"] = base["type_name"] if t_ok else None
            base["linked_2027_department_name"] = base["department_name"] if d_ok else None
            row = {**base,
                   "metric_label": r.get("metric_label"), "metric_unit": r.get("metric_unit"),
                   "metric_value": r.get("metric_value"), "raw_value_text": r.get("raw_value_text"),
                   "recruit_count": r.get("recruit_count"), "applicant_count": r.get("applicant_count"),
                   "competition_rate": r.get("competition_rate"), "extra_admitted_count": r.get("extra_admitted_count")}
            emit = [row]
            if rank_label and row["metric_label"] is None and row["extra_admitted_count"] is not None:
                rank = row["extra_admitted_count"]
                row["extra_admitted_count"] = None
                emit.append({**base, "metric_label": rank_label, "metric_unit": "OTHER", "metric_value": rank,
                             "raw_value_text": str(rank), "recruit_count": None, "applicant_count": None,
                             "competition_rate": None, "extra_admitted_count": None})
                moved += 1
            for e in emit:
                prob = range_problem(e)
                if prob:
                    failures.append({"row_index": i, "reason": prob})
                    continue
                long = [f for f, n in MAX_LEN.items() if e.get(f) and len(str(e[f])) > n]
                if long:
                    failures.append({"row_index": i, "reason": f"길이 초과 {long}"})
                    continue
                nk = natural_key(e)
                if nk in seen:
                    prev = seen[nk]
                    value_keys = ("metric_value", "raw_value_text", "recruit_count", "applicant_count",
                                  "competition_rate", "extra_admitted_count")
                    conflict = [k for k in value_keys if prev.get(k) is not None and e.get(k) is not None and prev[k] != e[k]]
                    if prev.get("source_document_key") == e.get("source_document_key"):
                        # 같은 문서 안의 같은 단위: 빈 칸만 채운다(출처가 같으므로 한 행으로 합쳐도 된다).
                        for k in value_keys:
                            if prev.get(k) is None and e.get(k) is not None:
                                prev[k] = e[k]
                    else:
                        # 다른 문서의 같은 단위: 한 행에는 출처가 하나뿐이라 두 문서 값을 섞지 않는다.
                        # 값이 더 많은 쪽 행을 그 출처째로 남기고, 다른 문서의 값은 넣지 않는다(경고로 남김).
                        filled = lambda r: sum(r.get(k) is not None for k in value_keys)
                        dropped = [k for k in value_keys if e.get(k) is not None]
                        if filled(e) > filled(prev):
                            dropped = [k for k in value_keys if prev.get(k) is not None]
                            out_rows[out_rows.index(prev)] = e
                            seen[nk] = e
                        diff = f", 서로 다른 값 {conflict}" if conflict else ""
                        warnings.append({"row_index": i, "reason": f"같은 단위가 두 문서에 나옴 — 값이 더 많은 문서 행만 남기고 다른 문서 값 {dropped} 제외{diff}"})
                        continue
                    if conflict:
                        warnings.append({"row_index": i, "reason": f"같은 단위가 한 문서에 다른 값 {conflict} — 앞 행 값 유지"})
                    continue
                seen[nk] = e
                out_rows.append(e)
                linked_t += 1 if (e is row and t_ok) else 0
                linked_d += 1 if (e is row and d_ok) else 0
        rows.extend(out_rows)
        if out_rows:
            universities.append({k: univ[k] for k in ("code", "university_code", "name", "establishment_type", "region")
                                 if k in univ})

        ver = src.get("verification", {})
        base_rows = [r for r in out_rows if r["metric_label"] is None]
        per_univ.append({
            "university_key": key, "university_code": code, "university_name": name,
            "documents": {"SUSI": sum(1 for d in doc_map.values() if d[1]["round_type"] == "SUSI"),
                          "JEONGSI": sum(1 for d in doc_map.values() if d[1]["round_type"] == "JEONGSI"),
                          "OTHER": sum(1 for d in doc_map.values() if d[1]["round_type"] == "OTHER")},
            "rows": len(out_rows), "base_rows": len(base_rows), "metric_rows": len(out_rows) - len(base_rows),
            "metric_labels": len({r["metric_label"] for r in out_rows if r["metric_label"]}),
            "reserve_rank_moved_to_metric": moved,
            "linked_2027_type_rows": linked_t, "linked_2027_department_rows": linked_d,
            "recruit_total_checks": ver.get("recruit_total_checks", []),
            "spot_checks": len(ver.get("spot_checks", [])),
            "spot_checks_all_match": all(c.get("match") for c in ver.get("spot_checks", [])) if ver.get("spot_checks") else None,
            "range_failures_source": ver.get("range_failures", 0),
            "build_failures": failures,
            "build_warnings": warnings,
            "gaps": len(src.get("gaps", [])),
        })

    seed = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "gate": "verification_status=NORMALIZED — 관리자 activate-all(2027) 승격 전까지 상담 검색 미노출. "
                "지난해(2026학년도) 공식 입시결과 전용 시드 — authoritative_universities 없음(기존 모집요강 자료를 보관하지 않음)",
        "ipsi_universities": universities,
        "ipsi_documents": documents,
        "prior_results": rows,
        "gaps": gaps,
        "counts": {"universities": len(universities), "documents": len(documents), "prior_results": len(rows),
                   "gaps": len(gaps)},
    }
    return seed, per_univ


def slim(row: dict) -> dict:
    return {k: v for k, v in row.items() if v is not None and v != []}


def split_seed(seed: dict) -> list[dict]:
    """대학·문서별로 행을 나누고(조각당 MAX_ROWS_PER_PART행) 글자 수 한도 안에서 앞에서부터 묶는다."""
    univ_by_code = {u["university_code"]: u for u in seed["ipsi_universities"]}
    doc_by_key = {d["document_key"]: d for d in seed["ipsi_documents"]}
    groups: dict[str, list] = {}
    for r in seed["prior_results"]:
        groups.setdefault(r["source_document_key"], []).append(slim(r))
    parts = []
    for key, rows in groups.items():
        for i in range(0, len(rows), MAX_ROWS_PER_PART):
            chunk = rows[i:i + MAX_ROWS_PER_PART]
            parts.append((doc_by_key[key], chunk, len(json.dumps(chunk, ensure_ascii=False, separators=(",", ":")))))
    files, cur, size = [], [], 0
    for part in parts:
        if cur and size + part[2] > MAX_CHARS_PER_FILE:
            files.append(cur)
            cur, size = [], 0
        cur.append(part)
        size += part[2]
    if cur:
        files.append(cur)
    out = []
    for n, file_parts in enumerate(files, 1):
        docs = {p[0]["document_key"]: p[0] for p in file_parts}
        rows = [r for p in file_parts for r in p[1]]
        codes = sorted({r["university_code"] for r in rows})
        out.append({
            "generated_at": seed["generated_at"], "gate": seed["gate"],
            "part": f"{n}/{len(files)}",
            "ipsi_universities": [univ_by_code[c] for c in codes],
            "ipsi_documents": list(docs.values()),
            "prior_results": rows,
            "counts": {"universities": len(codes), "documents": len(docs), "prior_results": len(rows)},
        })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--keys", nargs="*", help="이 대학 키만 (기본: 전체)")
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--report-key", default="prior_results",
                    help="build_report.json 안의 항목 이름(추가 묶음은 prior_results_batch3처럼 따로 둬 기존 기록을 덮지 않음)")
    args = ap.parse_args()
    seed, per_univ = build(args.keys)
    os.makedirs(args.out_dir, exist_ok=True)
    for old in glob.glob(os.path.join(args.out_dir, "ipsi_seed_prior_2026_*.json")):
        os.remove(old)
    files = []
    for part in split_seed(seed):
        n = part["part"].split("/")[0].zfill(2)
        codes = "_".join(u["university_code"].lower() for u in part["ipsi_universities"])
        path = os.path.join(args.out_dir, f"ipsi_seed_prior_2026_{n}_{codes}.json")
        text = json.dumps(part, ensure_ascii=False, separators=(",", ":"))
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        files.append({"file": os.path.relpath(path, ROOT), "prior_results": part["counts"]["prior_results"],
                      "documents": part["counts"]["documents"], "chars": len(text)})
    with open(os.path.join(args.out_dir, "gaps.json"), "w", encoding="utf-8") as f:
        json.dump(seed["gaps"], f, ensure_ascii=False, indent=2)
    report = {}
    if os.path.exists(REPORT):
        with open(REPORT, encoding="utf-8") as f:
            report = json.load(f)
    report[args.report_key] = {
        "seed_files": files,
        "result_year": RESULT_YEAR, "academic_year": COUNSEL_YEAR,
        "count": len(seed["prior_results"]), "documents": len(seed["ipsi_documents"]),
        "universities_with_rows": len(seed["ipsi_universities"]),
        "gaps": seed["gaps"],
        "per_university": per_univ,
    }
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    fails = sum(len(u["build_failures"]) for u in per_univ)
    print(json.dumps(seed["counts"], ensure_ascii=False), "build_failures", fails)
    for f in files:
        print("  file", f["file"], f["prior_results"], "rows", f["chars"], "chars")
    for u in per_univ:
        print(f"  {u['university_key']:8} {u['university_name']:16} docs {u['documents']} rows {u['rows']} "
              f"(기본 {u['base_rows']}/지표 {u['metric_rows']}) 예비번호→지표 {u['reserve_rank_moved_to_metric']} "
              f"2027연결 전형 {u['linked_2027_type_rows']} 학과 {u['linked_2027_department_rows']} "
              f"대조 {u['spot_checks']} gaps {u['gaps']} 실패 {len(u['build_failures'])}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
