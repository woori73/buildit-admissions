"""정시 수능 환산 계산식(jeongsi_formula/v1) → feel2real 적재 시드 + Java 계산기 일치 검사용 자료.

계산식 파일을 모두 검증(오류가 하나라도 있으면 중단)한 뒤 계산식이 있는 대학만 시드로 만든다.
대학은 기존 2027 시드(data/seed/ipsi_seed_univ_sample.json)의 코드·이름을 그대로 쓰고,
근거 자료는 그 대학의 기존 2027 정시 모집요강 자료 제목으로 연결한다(적재기가 같은 제목 자료에 붙인다).

사용:
    python3 scripts/build_jeongsi_formula_seed.py                       # 시드 쓰기
    python3 scripts/build_jeongsi_formula_seed.py --conformance-out F   # Java 일치 검사 자료도 쓰기
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jeongsi_formula as jf  # noqa: E402

ROOT = jf.ROOT
BASE_SEED = os.path.join(ROOT, "data", "seed", "ipsi_seed_univ_sample.json")
OUT_PATH = os.path.join(ROOT, "data", "seed", "jeongsi_formula_2027", "ipsi_seed_jeongsi_formula_2027.json")


class BuildError(RuntimeError):
    pass


def _base(name: str) -> str:
    return re.sub(r"\(.*?\)", "", name or "").strip()


def _university_entry(doc: dict, base_seed: dict) -> dict:
    """계산식 파일의 대학을 기존 시드 대학으로 찾는다. university_key 대문자 = 코드가 기본이다."""
    code = doc["university_key"].upper()
    by_code = {u["university_code"]: u for u in base_seed["ipsi_universities"]}
    if code in by_code and _base(by_code[code]["name"]) == _base(doc["university_name"]):
        return by_code[code]
    raise BuildError(f"{doc['university_key']}: 기존 2027 시드에서 대학을 찾지 못함(코드 {code}, 이름 {doc['university_name']})")


def _jeongsi_document(code: str, doc: dict, base_seed: dict) -> dict:
    """기존 2027 정시 모집요강 자료가 있으면 그 제목으로, 없으면 계산식 문서 이름으로 근거 자료를 만든다."""
    fdoc = doc["documents"][0]
    key = f"doc_{code.lower()}_2027_jeongsi"
    existing = next((d for d in base_seed["ipsi_documents"] if d["document_key"] == key), None)
    return {
        "document_key": key,
        "document_name": existing["document_name"] if existing else f"{doc['university_name']} {fdoc.get('document_name')}",
        "institution_name": fdoc.get("institution_name") or f"{doc['university_name']} 입학처",
        "source_url": fdoc.get("file_url") or fdoc.get("source_page_url"),
        "applicable_academic_year": 2027,
        "published_at": None,
    }


def build(paths: list[str] | None = None, base_seed: dict | None = None) -> tuple[dict, list[dict]]:
    """(시드, 일치 검사 자료). 검증 오류가 있으면 BuildError."""
    paths = paths or sorted(glob.glob(os.path.join(jf.FORMULA_DIR, "*_2027_jeongsi_formula.json")))
    if base_seed is None:
        with open(BASE_SEED, encoding="utf-8") as f:
            base_seed = json.load(f)
    universities, documents, formulas, conformance = [], [], [], []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            doc = json.load(f)
        report = jf.validate_doc(doc)
        if report["errors"]:
            raise BuildError(f"{os.path.basename(p)}: 검증 오류 {report['errors'][:3]}")
        if not doc.get("formulas"):
            continue
        univ = _university_entry(doc, base_seed)
        code = univ["university_code"]
        mdoc = _jeongsi_document(code, doc, base_seed)
        universities.append({k: univ.get(k) for k in ("university_code", "name", "region", "establishment_type", "admission_office_url")})
        documents.append(mdoc)
        fdoc = {d["document_key"]: d for d in doc["documents"]}
        for fm in doc["formulas"]:
            src = fdoc.get(fm["document_key"], {})
            formulas.append({
                "university_code": code, "academic_year": 2027, "formula_key": fm["formula_id"], "label": fm["label"],
                "type_names": fm["applies_to"]["type_names"],
                "department_names": fm["applies_to"].get("department_names") or [],
                "unit_scope_text": fm["applies_to"].get("unit_scope_text"),
                "csat_points": fm.get("csat_points"), "perfect_score_expected": fm.get("perfect_score_expected"),
                "expression": fm["expression"], "tables": fm.get("tables") or {},
                "rounding_text": fm.get("rounding_text"), "eligibility_text": fm.get("eligibility_text"),
                "not_in_csat_score_text": fm.get("not_in_csat_score_text"),
                "evidence_pages": fm.get("evidence_pages") or [], "raw_text": fm.get("raw_text"),
                "uncertain": fm.get("uncertain") or [],
                "needs_review_reason": (fm.get("needs_review") or {}).get("reason"),
                "source_document_key": mdoc["document_key"],
                "source_url": src.get("file_url") or src.get("source_page_url"),
            })
            for name, inputs in (("perfect", jf.perfect_inputs()), ("sample", jf.sample_inputs())):
                conformance.append({"formula_key": f"{code}:{fm['formula_id']}", "case": name, "expression": fm["expression"],
                                    "tables": fm.get("tables") or {}, "inputs": inputs,
                                    "expected": jf.evaluate(fm["expression"], inputs, fm.get("tables") or {})})
    seed = {"schema": "ipsi_seed/jeongsi_formula", "academic_year": 2027,
            "ipsi_universities": universities, "ipsi_documents": documents, "jeongsi_formulas": formulas,
            "counts": {"universities": len(universities), "formulas": len(formulas),
                       "needs_review": sum(1 for f in formulas if f["needs_review_reason"])}}
    return seed, conformance


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT_PATH)
    ap.add_argument("--conformance-out")
    args = ap.parse_args(argv)
    seed, conformance = build()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=1)
    print(f"시드: {args.out} — 대학 {seed['counts']['universities']} · 계산식 {seed['counts']['formulas']} · 확인 필요 {seed['counts']['needs_review']}")
    if args.conformance_out:
        with open(args.conformance_out, "w", encoding="utf-8") as f:
            json.dump(conformance, f, ensure_ascii=False)
        print(f"일치 검사 자료: {args.conformance_out} — {len(conformance)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
