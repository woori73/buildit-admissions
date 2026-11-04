"""2027 수시 수능최저학력기준(susi_minimum/v1) — 규칙 검증·판정.

대학 수시 모집요강의 수능최저학력기준을 조건식(condition)으로 적는다. 조건식은 정시 계산식과 같은 수식 언어
(scripts/jeongsi_formula.py)를 쓰고, 참(1)이면 충족이다. 형식 설명: docs/schema/SUSI_MINIMUM.md

사용:
    python3 scripts/susi_minimum.py data/parsed/susi_minimum/{key}_2027_susi_minimum.json
    python3 scripts/susi_minimum.py --all
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jeongsi_formula as jf  # noqa: E402

ROOT = jf.ROOT
MINIMUM_DIR = os.path.join(ROOT, "data", "parsed", "susi_minimum")
SUSI_DIR = os.path.join(ROOT, "data", "parsed", "univ_sample")
SCHEMA = "susi_minimum/v1"

# 수능최저에 쓰는 입력: 등급과 선택 표시. 점수(표준점수·백분위)는 쓰지 않는다.
VARIABLES = {k: v for k, v in jf.VARIABLES.items()
             if not k.endswith(("_STD", "_PCT", "_STD_MAX", "_CONV", "_CONV_MAX"))}


def best_inputs() -> dict:
    """모든 등급 1, 선택 표시 모두 1(어떤 지정 과목 조건도 만족) — 이 입력에서 충족이어야 한다."""
    return {k: 1.0 for k in VARIABLES}


def worst_inputs() -> dict:
    """모든 등급 9, 선택 표시 모두 1 — 이 입력에서 미충족이어야 한다."""
    return {k: (9.0 if k.endswith("_GRD") else 1.0) for k in VARIABLES}


BASE_SEED = os.path.join(ROOT, "data", "seed", "ipsi_seed_univ_sample.json")
_SEED_CACHE: dict = {}


def _load_susi(university_key: str) -> dict | None:
    """운영에 적재된 2027 시드에서 그 대학(코드 = university_key 대문자)의 수시 전형명·모집단위명을 읽는다."""
    if "seed" not in _SEED_CACHE:
        if not os.path.exists(BASE_SEED):
            return None
        with open(BASE_SEED, encoding="utf-8") as f:
            _SEED_CACHE["seed"] = json.load(f)
    seed = _SEED_CACHE["seed"]
    code = university_key.upper()
    types = [{"name": t["type_name"]} for t in seed["ipsi_admission_types"]
             if t["university_code"] == code and t.get("round_type") == "SUSI"]
    if not types:
        return None
    depts = [{"department": d["department_name"]} for d in seed.get("ipsi_departments", []) if d["university_code"] == code]
    return {"admission_types": types, "departments": depts}


def validate_doc(doc: dict, known_type_names: set[str] | None = None,
                 known_department_names: set[str] | None = None) -> dict:
    errors, warnings, results = [], [], []
    if doc.get("schema") != SCHEMA:
        errors.append(f"schema는 {SCHEMA}")
    for k in ("university_key", "university_name", "academic_year"):
        if not doc.get(k):
            errors.append(f"필수 칸 없음: {k}")
    if doc.get("academic_year") not in (None, 2027):
        errors.append("academic_year는 2027")
    if not doc.get("rules") and not doc.get("no_minimum") and not doc.get("gaps") and not doc.get("not_covered"):
        errors.append("rules·no_minimum·not_covered·gaps 중 하나는 있어야 한다")
    if (doc.get("rules") or doc.get("no_minimum")) and not doc.get("documents"):
        errors.append("필수 칸 없음: documents")
    doc_keys = {d.get("document_key") for d in doc.get("documents") or []}
    for d in doc.get("documents") or []:
        if not (d.get("file_url") or d.get("source_url") or d.get("source_page_url")):
            errors.append(f"문서 {d.get('document_key')}: 출처 주소 없음")
    if (known_type_names is None or known_department_names is None) and doc.get("university_key"):
        js = _load_susi(doc["university_key"])
        if js is not None:
            if known_type_names is None:
                known_type_names = {t["name"] for t in js.get("admission_types", [])}
            if known_department_names is None:
                known_department_names = {d.get("department") for d in js.get("departments", []) if d.get("department")}
    covered: set[str] = set()
    ids = set()
    for i, r in enumerate(doc.get("rules") or []):
        rid = r.get("rule_id") or f"#{i}"
        res = {"rule_id": rid}
        if rid in ids:
            errors.append(f"{rid}: rule_id 중복")
        ids.add(rid)
        for k in ("label", "applies_to", "condition", "evidence_pages", "raw_text", "document_key"):
            if not r.get(k):
                errors.append(f"{rid}: 필수 칸 없음: {k}")
        if r.get("document_key") and r["document_key"] not in doc_keys:
            errors.append(f"{rid}: document_key {r['document_key']}가 documents에 없음")
        types = (r.get("applies_to") or {}).get("type_names") or []
        if not types:
            errors.append(f"{rid}: applies_to.type_names 없음")
        if known_type_names is not None:
            for t in types:
                if t not in known_type_names:
                    errors.append(f"{rid}: 2027 수시 자료에 없는 전형명 {t!r}")
        covered.update(types)
        if known_department_names is not None:
            for dn in (r.get("applies_to") or {}).get("department_names") or []:
                if dn not in known_department_names:
                    warnings.append(f"{rid}: 2027 수시 자료에 없는 모집단위명 {dn!r}")
        try:
            variables, used_tables = jf.names_in(r.get("condition") or "0")
        except jf.FormulaError as e:
            errors.append(f"{rid}: {e}")
            results.append(res)
            continue
        unknown = sorted(v for v in variables if v not in VARIABLES)
        if unknown:
            errors.append(f"{rid}: 수능최저에 쓰지 않는 변수 {unknown}(등급과 선택 표시만)")
            results.append(res)
            continue
        if used_tables:
            errors.append(f"{rid}: 수능최저 조건에는 표를 쓰지 않는다")
        res["uses"] = sorted(variables)
        try:
            best = jf.evaluate(r["condition"], {**best_inputs(), **(r.get("sanity_best") or {})})
            worst = jf.evaluate(r["condition"], {**worst_inputs(), **(r.get("sanity_worst") or {})})
        except jf.FormulaError as e:
            errors.append(f"{rid}: 계산 실패 {e}")
            results.append(res)
            continue
        if best not in (0.0, 1.0) or worst not in (0.0, 1.0):
            errors.append(f"{rid}: 조건식 결과가 참/거짓(1/0)이 아님")
        elif best != 1.0:
            errors.append(f"{rid}: 모든 등급 1인 학생이 미충족으로 나옴")
        elif worst != 0.0:
            errors.append(f"{rid}: 모든 등급 9인 학생이 충족으로 나옴")
        for j, ex in enumerate(r.get("examples") or []):
            try:
                got = jf.evaluate(r["condition"], {**worst_inputs(), **(ex.get("inputs") or {})})
            except jf.FormulaError as e:
                errors.append(f"{rid}: 예시 {j} 계산 실패 {e}")
                continue
            if bool(got) != bool(ex["expected_met"]):
                errors.append(f"{rid}: 예시 {j} 결과 {bool(got)} ≠ 원문 {ex['expected_met']}")
        results.append(res)
    for t in (doc.get("no_minimum") or {}):
        if known_type_names is not None and t not in known_type_names:
            errors.append(f"no_minimum: 2027 수시 자료에 없는 전형명 {t!r}")
        if t in covered and not any(not ((r.get("applies_to") or {}).get("department_names")) for r in doc.get("rules") or []
                                    if t in (r.get("applies_to") or {}).get("type_names", [])):
            warnings.append(f"no_minimum과 rules에 함께 있는 전형(모집단위별로 다른지 확인): {t}")
    if known_type_names is not None:
        listed = covered | set(doc.get("no_minimum") or {}) | set(doc.get("not_covered") or {})
        for t in sorted(known_type_names - listed):
            warnings.append(f"수능최저 여부가 정리되지 않은 수시 전형: {t}")
    return {"errors": errors, "warnings": warnings, "rules": results}


def check(rule: dict, grades: dict) -> dict:
    """한 규칙 판정. 필요한 등급이 없으면 NEEDS_INPUT. 선택 표시는 없으면 0."""
    variables, _ = jf.names_in(rule["condition"])
    missing = sorted(v for v in variables if v.endswith("_GRD") and grades.get(v) is None)
    if missing:
        return {"outcome": "NEEDS_INPUT", "missing": missing}
    inputs = {v: float(grades.get(v, 0) or 0) for v in variables}
    return {"outcome": "MET" if jf.evaluate(rule["condition"], inputs) else "NOT_MET"}


def main(argv: list[str]) -> int:
    paths = sorted(glob.glob(os.path.join(MINIMUM_DIR, "*_2027_susi_minimum.json"))) if "--all" in argv else \
        [a for a in argv if not a.startswith("--")]
    bad = 0
    for p in paths:
        with open(p, encoding="utf-8") as f:
            r = validate_doc(json.load(f))
        print(f"{os.path.basename(p)}: 오류 {len(r['errors'])} · 경고 {len(r['warnings'])} · 규칙 {len(r['rules'])}")
        for e in r["errors"]:
            print("  오류:", e)
        for w in r["warnings"]:
            print("  경고:", w)
        bad += bool(r["errors"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
