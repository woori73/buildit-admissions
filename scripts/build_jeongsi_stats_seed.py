"""수능 표준점수 최고점(csat_std_max/v1)·대학 변환표준점수표(conversion_score/v1) → feel2real 적재 시드.

파일을 모두 검증(오류가 하나라도 있으면 중단)한 뒤, 값이 모두 발표된 최고점 문서와 표가 있는 변환표준점수 문서만 시드로 만든다.
대학은 기존 2027 시드(data/seed/ipsi_seed_univ_sample.json)의 코드·이름을 그대로 쓴다.

사용: python3 scripts/build_jeongsi_stats_seed.py [--out 경로]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jeongsi_stats as js  # noqa: E402

ROOT = js.ROOT
BASE_SEED = os.path.join(ROOT, "data", "seed", "ipsi_seed_univ_sample.json")
OUT_PATH = os.path.join(ROOT, "data", "seed", "jeongsi_stats_2027", "ipsi_seed_jeongsi_stats_2027.json")


class BuildError(RuntimeError):
    pass


def _base(name: str) -> str:
    return re.sub(r"\(.*?\)", "", name or "").strip()


def _document(key: str, doc: dict, institution_default: str) -> dict:
    src = doc["source"]
    return {"document_key": key, "document_name": src["document_name"],
            "institution_name": src.get("institution_name") or institution_default,
            "source_url": src.get("file_url") or src.get("source_page_url"),
            "applicable_academic_year": doc["academic_year"], "published_at": src.get("published_at")}


def build(paths: list[str] | None = None, base_seed: dict | None = None) -> dict:
    paths = paths or sorted(glob.glob(os.path.join(js.STATS_DIR, "*.json")))
    if base_seed is None:
        with open(BASE_SEED, encoding="utf-8") as f:
            base_seed = json.load(f)
    by_code = {u["university_code"]: u for u in base_seed["ipsi_universities"]}
    universities, documents, std_rows, conv_rows = [], [], [], []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        is_std = doc.get("schema") == js.STD_MAX_SCHEMA
        report = js.validate_std_max(doc) if is_std else js.validate_conversion(doc)
        if report["errors"]:
            raise BuildError(f"{os.path.basename(p)}: 검증 오류 {report['errors'][:3]}")
        year = doc["academic_year"]
        if is_std:
            if not report["published"]:
                continue
            key = f"doc_kice_{year}_csat_scores"
            documents.append(_document(key, doc, "한국교육과정평가원"))
            pages = doc.get("evidence_pages") or []
            for area in ("KOR", "MATH"):
                std_rows.append({"academic_year": year, "subject_key": area, "area": area, "subject_name": None, "track": None,
                                 "std_max": doc["areas"][area], "evidence_pages": pages,
                                 "source_document_key": key, "source_url": documents[-1]["source_url"]})
            for s in doc.get("inquiry") or []:
                std_rows.append({"academic_year": year, "subject_key": f"INQ:{s['subject']}", "area": "INQ",
                                 "subject_name": s["subject"], "track": s["track"], "std_max": s["std_max"],
                                 "evidence_pages": pages, "source_document_key": key, "source_url": documents[-1]["source_url"]})
            continue
        if not doc.get("tables"):
            continue
        code = doc["university_key"].upper()
        univ = by_code.get(code)
        if univ is None or _base(univ["name"]) != _base(doc["university_name"]):
            raise BuildError(f"{doc['university_key']}: 기존 2027 시드에서 대학을 찾지 못함(코드 {code}, 이름 {doc['university_name']})")
        key = f"doc_{code.lower()}_{year}_jeongsi_conversion"
        universities.append({k: univ.get(k) for k in ("university_code", "name", "region", "establishment_type", "admission_office_url")})
        documents.append(_document(key, doc, f"{doc['university_name']} 입학처"))
        for t in doc["tables"]:
            conv_rows.append({"university_code": code, "academic_year": year, "track": t["track"],
                              "label": t.get("label") or t["track"], "scores": {p: t["scores"][p] for p in js.PERCENTILES},
                              "evidence_pages": t.get("evidence_pages") or [], "note": t.get("note"),
                              "source_document_key": key, "source_url": documents[-1]["source_url"]})
    return {"schema": "ipsi_seed/jeongsi_stats", "academic_year": 2027,
            "ipsi_universities": universities, "ipsi_documents": documents,
            "csat_std_max": std_rows, "conversion_scores": conv_rows,
            "counts": {"std_max": len(std_rows), "conversion_universities": len(universities), "conversion_tables": len(conv_rows)}}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT_PATH)
    args = ap.parse_args(argv)
    seed = build()
    c = seed["counts"]
    if not seed["csat_std_max"] and not seed["conversion_scores"]:
        print("적재할 값이 없습니다(최고점·변환표준점수 모두 발표 전).")
        return 0
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=1)
    print(f"시드: {args.out} — 최고점 {c['std_max']} · 변환표준점수 대학 {c['conversion_universities']} · 표 {c['conversion_tables']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
