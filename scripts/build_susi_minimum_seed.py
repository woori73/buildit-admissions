"""수시 수능최저학력기준(susi_minimum/v1) → feel2real 적재 시드(susi_minimums).

규칙 파일을 모두 검증(오류가 하나라도 있으면 중단)한 뒤, 규칙이나 '최저 없음' 전형이 있는 대학만 시드로 만든다.
대학은 기존 2027 시드(data/seed/ipsi_seed_univ_sample.json)의 코드·이름을 그대로 쓰고, 근거 자료는 그 대학의
기존 2027 수시 모집요강 자료 제목으로 연결한다(적재기가 같은 제목 자료에 붙인다).

사용: python3 scripts/build_susi_minimum_seed.py [--out 경로]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import susi_minimum as sm  # noqa: E402

ROOT = sm.ROOT
BASE_SEED = os.path.join(ROOT, "data", "seed", "ipsi_seed_univ_sample.json")
OUT_PATH = os.path.join(ROOT, "data", "seed", "susi_minimum_2027", "ipsi_seed_susi_minimum_2027.json")
DOC_PREFIX_ALIAS = {"YONSEI": "yon"}  # 기존 시드 문서 키가 대학 코드와 다른 경우


class BuildError(RuntimeError):
    pass


def _base(name: str) -> str:
    return re.sub(r"\(.*?\)", "", name or "").strip()


def _susi_document(code: str, doc: dict, base_seed: dict) -> dict:
    prefix = f"doc_{DOC_PREFIX_ALIAS.get(code, code.lower())}_2027_susi"
    candidates = [d for d in base_seed["ipsi_documents"] if d["document_key"].startswith(prefix) and "part" not in d["document_key"]]
    fdoc = (doc.get("documents") or [{}])[0]
    if candidates:
        existing = candidates[0]
        return {"document_key": existing["document_key"], "document_name": existing["document_name"],
                "institution_name": fdoc.get("institution_name") or existing.get("institution_name"),
                "source_url": fdoc.get("file_url") or fdoc.get("source_page_url"),
                "applicable_academic_year": 2027, "published_at": None}
    return {"document_key": prefix, "document_name": f"{doc['university_name']} {fdoc.get('document_name') or '2027학년도 수시 모집요강'}",
            "institution_name": fdoc.get("institution_name") or f"{doc['university_name']} 입학처",
            "source_url": fdoc.get("file_url") or fdoc.get("source_page_url"), "applicable_academic_year": 2027, "published_at": None}


def build(paths: list[str] | None = None, base_seed: dict | None = None) -> dict:
    paths = paths or sorted(glob.glob(os.path.join(sm.MINIMUM_DIR, "*_2027_susi_minimum.json")))
    if base_seed is None:
        with open(BASE_SEED, encoding="utf-8") as f:
            base_seed = json.load(f)
    by_code = {u["university_code"]: u for u in base_seed["ipsi_universities"]}
    universities, documents, rows = [], [], []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        report = sm.validate_doc(doc)
        if report["errors"]:
            raise BuildError(f"{os.path.basename(p)}: 검증 오류 {report['errors'][:3]}")
        if not doc.get("rules") and not doc.get("no_minimum"):
            continue
        code = doc["university_key"].upper()
        univ = by_code.get(code)
        if univ is None or _base(univ["name"]) != _base(doc["university_name"]):
            raise BuildError(f"{doc['university_key']}: 기존 2027 시드에서 대학을 찾지 못함(코드 {code}, 이름 {doc['university_name']})")
        mdoc = _susi_document(code, doc, base_seed)
        universities.append({k: univ.get(k) for k in ("university_code", "name", "region", "establishment_type", "admission_office_url")})
        documents.append(mdoc)
        fdocs = {d["document_key"]: d for d in doc.get("documents") or []}
        for r in doc.get("rules") or []:
            src = fdocs.get(r["document_key"], {})
            rows.append({
                "university_code": code, "academic_year": 2027, "rule_key": r["rule_id"], "rule_kind": "RULE",
                "label": r["label"], "type_names": r["applies_to"]["type_names"],
                "department_names": r["applies_to"].get("department_names") or [],
                "unit_scope_text": r["applies_to"].get("unit_scope_text"), "condition": r["condition"],
                "required_areas_text": r.get("required_areas_text"), "evidence_pages": r.get("evidence_pages") or [],
                "raw_text": r.get("raw_text"), "uncertain": r.get("uncertain") or [],
                "needs_review_reason": (r.get("needs_review") or {}).get("reason") if isinstance(r.get("needs_review"), dict) else r.get("needs_review"),
                "source_document_key": mdoc["document_key"], "source_url": src.get("file_url") or src.get("source_page_url"),
            })
        fdoc = (doc.get("documents") or [{}])[0]
        for type_name, evidence in (doc.get("no_minimum") or {}).items():
            digest = hashlib.sha256(type_name.encode("utf-8")).hexdigest()[:10]
            rows.append({
                "university_code": code, "academic_year": 2027, "rule_key": f"{doc['university_key']}_nomin_{digest}",
                "rule_kind": "NO_MINIMUM", "label": type_name, "type_names": [type_name], "department_names": [],
                "raw_text": evidence, "evidence_pages": [int(x) for x in re.findall(r"(\d+)\s*쪽", evidence or "")][:5],
                "uncertain": [], "needs_review_reason": None,
                "source_document_key": mdoc["document_key"], "source_url": fdoc.get("file_url") or fdoc.get("source_page_url"),
            })
    return {"schema": "ipsi_seed/susi_minimum", "academic_year": 2027,
            "ipsi_universities": universities, "ipsi_documents": documents, "susi_minimums": rows,
            "counts": {"universities": len(universities), "rules": sum(1 for r in rows if r["rule_kind"] == "RULE"),
                       "no_minimum": sum(1 for r in rows if r["rule_kind"] == "NO_MINIMUM"),
                       "needs_review": sum(1 for r in rows if r.get("needs_review_reason"))}}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT_PATH)
    args = ap.parse_args(argv)
    seed = build()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=1)
    c = seed["counts"]
    print(f"시드: {args.out} — 대학 {c['universities']} · 규칙 {c['rules']} · 최저 없음 {c['no_minimum']} · 확인 필요 {c['needs_review']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
