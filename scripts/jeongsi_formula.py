"""2027 정시 수능 환산 계산식(jeongsi_formula/v1) — 수식 해석·계산·검증.

대학 모집요강의 수능 반영 방법을 하나의 수식(expression)과 등급표(tables)로 적고, 이 모듈로 계산·검증한다.
형식 설명: docs/schema/JEONGSI_FORMULA.md

사용:
    python3 scripts/jeongsi_formula.py data/parsed/jeongsi_formula/uos_2027_jeongsi_formula.json   # 검증 결과 출력
    python3 scripts/jeongsi_formula.py --all                                                        # 전체 검증
"""
from __future__ import annotations

import ast
import glob
import json
import math
import os
import sys
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORMULA_DIR = os.path.join(ROOT, "data", "parsed", "jeongsi_formula")
JEONGSI_DIR = os.path.join(ROOT, "data", "parsed", "univ_sample")
SCHEMA = "jeongsi_formula/v1"

_AREA_SCORE = {"STD": "표준점수", "PCT": "백분위", "GRD": "등급", "STD_MAX": "전국 최고 표준점수(해당 과목)"}
VARIABLES: dict[str, str] = {}
for _area, _ko in (("KOR", "국어"), ("MATH", "수학")):
    for _s, _d in _AREA_SCORE.items():
        VARIABLES[f"{_area}_{_s}"] = f"{_ko} {_d}"
VARIABLES.update({
    "KOR_SEL_HW": "국어 선택과목 화법과 작문이면 1", "KOR_SEL_EM": "국어 선택과목 언어와 매체면 1",
    "MATH_SEL_PROB": "수학 선택과목 확률과 통계면 1", "MATH_SEL_CALC": "수학 선택과목 미적분이면 1",
    "MATH_SEL_GEOM": "수학 선택과목 기하면 1",
    "ENG_GRD": "영어 등급", "HIST_GRD": "한국사 등급",
    "FL_GRD": "제2외국어/한문 등급", "FL_TAKEN": "제2외국어/한문 응시하면 1",
})
for _i in (1, 2):
    for _s, _d in _AREA_SCORE.items():
        VARIABLES[f"INQ{_i}_{_s}"] = f"탐구{_i} {_d}"
    VARIABLES.update({
        f"INQ{_i}_CONV": f"탐구{_i} 대학 변환표준점수(대학별 표, 수능 성적 발표 뒤 공개)",
        f"INQ{_i}_CONV_MAX": f"탐구{_i} 대학 변환표준점수 최고점(대학별 표)",
        f"INQ{_i}_SOC": f"탐구{_i}이 사회탐구면 1", f"INQ{_i}_SCI": f"탐구{_i}이 과학탐구면 1",
        f"INQ{_i}_VOC": f"탐구{_i}이 직업탐구면 1", f"INQ{_i}_SCI2": f"탐구{_i}이 과학탐구 Ⅱ과목이면 1",
    })

# 수능 성적이 나와야(전국 최고점) 또는 대학이 표를 발표해야(변환표준점수) 정해지는 값.
PENDING_VARIABLES = {
    "KOR_STD_MAX": "평가원 채점결과(전국 최고 표준점수)", "MATH_STD_MAX": "평가원 채점결과(전국 최고 표준점수)",
    "INQ1_STD_MAX": "평가원 채점결과(전국 최고 표준점수)", "INQ2_STD_MAX": "평가원 채점결과(전국 최고 표준점수)",
    "INQ1_CONV": "대학 변환표준점수표", "INQ2_CONV": "대학 변환표준점수표",
    "INQ1_CONV_MAX": "대학 변환표준점수표", "INQ2_CONV_MAX": "대학 변환표준점수표",
}

FUNCTIONS = {"max", "min", "round", "trunc", "cond", "table", "top_sum", "low_sum", "sum"}
GRADE_KEYS = [str(g) for g in range(1, 10)]


class FormulaError(ValueError):
    pass


def _dec_round(x: float, digits: int, mode) -> float:
    q = Decimal(1).scaleb(-int(digits))
    return float(Decimal(str(x)).quantize(q, rounding=mode))


def parse(expression: str) -> ast.Expression:
    """수식 문자열을 허용된 문법만으로 해석한다. 허용 밖이면 FormulaError."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise FormulaError(f"수식 문법 오류: {e.msg}") from e
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.Call, ast.Name, ast.Constant,
               ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or,
               ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise FormulaError(f"허용되지 않는 문법: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                raise FormulaError(f"허용되지 않는 함수: {ast.dump(node.func)}")
            if node.keywords:
                raise FormulaError("함수에 이름 붙은 인자는 쓰지 않는다")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float, str)):
            raise FormulaError(f"허용되지 않는 상수: {node.value!r}")
    return tree


def names_in(expression: str) -> tuple[set[str], set[str]]:
    """(변수 이름들, table()이 참조하는 표 이름들)."""
    tree = parse(expression)
    variables, tables = set(), set()
    func_nodes = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and id(node) in func_nodes:
            continue
        if isinstance(node, ast.Call) and node.func.id == "table":
            if len(node.args) != 2 or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                raise FormulaError("table은 table('표이름', 값) 형태여야 한다")
            tables.add(node.args[0].value)
        elif isinstance(node, ast.Name):
            variables.add(node.id)
    return variables, tables


def evaluate(expression: str, inputs: dict, tables: dict | None = None) -> float:
    """수식을 계산한다. 비교·논리식은 참이면 1, 거짓이면 0."""
    tables = tables or {}
    tree = parse(expression)

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            if n.id not in inputs or inputs[n.id] is None:
                raise FormulaError(f"입력값 없음: {n.id}")
            return float(inputs[n.id])
        if isinstance(n, ast.UnaryOp):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else (+v if isinstance(n.op, ast.UAdd) else float(not v))
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if isinstance(n.op, ast.Mult):
                return a * b
            if b == 0:
                raise FormulaError("0으로 나눔")
            return a / b
        if isinstance(n, ast.BoolOp):
            vals = [ev(v) for v in n.values]
            return float(all(vals)) if isinstance(n.op, ast.And) else float(any(vals))
        if isinstance(n, ast.Compare):
            left = ev(n.left)
            for op, comp in zip(n.ops, n.comparators):
                right = ev(comp)
                ok = {ast.Eq: left == right, ast.NotEq: left != right, ast.Lt: left < right,
                      ast.LtE: left <= right, ast.Gt: left > right, ast.GtE: left >= right}[type(op)]
                if not ok:
                    return 0.0
                left = right
            return 1.0
        if isinstance(n, ast.Call):
            f = n.func.id
            if f == "cond":
                if len(n.args) != 3:
                    raise FormulaError("cond(조건, 참일 때, 거짓일 때)")
                return ev(n.args[1]) if ev(n.args[0]) else ev(n.args[2])
            if f == "table":
                name = n.args[0].value
                if name not in tables:
                    raise FormulaError(f"표 없음: {name}")
                key = ev(n.args[1])
                k = str(int(key)) if float(key).is_integer() else str(key)
                if k not in tables[name] or tables[name][k] is None:
                    raise FormulaError(f"표 {name}에 {k} 값 없음")
                return float(tables[name][k])
            args = [ev(a) for a in n.args]
            if f == "max":
                return max(args)
            if f == "min":
                return min(args)
            if f == "sum":
                return sum(args)
            if f == "top_sum":
                k = int(args[0])
                return sum(sorted(args[1:], reverse=True)[:k])
            if f == "low_sum":
                k = int(args[0])
                return sum(sorted(args[1:])[:k])
            if f in ("round", "trunc"):
                digits = int(args[1]) if len(args) > 1 else 0
                return _dec_round(args[0], digits, ROUND_HALF_UP if f == "round" else ROUND_DOWN)
        raise FormulaError(f"계산할 수 없는 노드: {type(n).__name__}")

    out = ev(tree)
    if isinstance(out, str) or math.isnan(out) or math.isinf(out):
        raise FormulaError("결과가 숫자가 아님")
    return out


def perfect_inputs() -> dict:
    """만점 입력: 표준점수=전국 최고점, 백분위 100, 등급 1, 변환표준점수=최고점, 선택 표시는 모두 0."""
    p = {}
    for name in VARIABLES:
        if name.endswith("_STD_MAX"):
            p[name] = 140.0
        elif name.endswith("_STD"):
            p[name] = 140.0
        elif name.endswith("_CONV_MAX") or name.endswith("_CONV"):
            p[name] = 70.0
        elif name.endswith("_PCT"):
            p[name] = 100.0
        elif name.endswith("_GRD"):
            p[name] = 1.0
        else:
            p[name] = 0.0
    return p


def sample_inputs() -> dict:
    """중간 수준 표본 입력(계산이 끝까지 되는지 확인용)."""
    p = perfect_inputs()
    p.update({"KOR_STD": 120, "MATH_STD": 125, "INQ1_STD": 62, "INQ2_STD": 60, "INQ1_CONV": 63.5, "INQ2_CONV": 61.2,
              "KOR_PCT": 85, "MATH_PCT": 88, "INQ1_PCT": 86, "INQ2_PCT": 80, "KOR_GRD": 2, "MATH_GRD": 2,
              "INQ1_GRD": 2, "INQ2_GRD": 3, "ENG_GRD": 2, "HIST_GRD": 3, "FL_GRD": 4,
              "KOR_SEL_EM": 1, "MATH_SEL_CALC": 1, "INQ1_SCI": 1, "INQ2_SCI": 1})
    return p


def _load_jeongsi(university_key: str) -> dict | None:
    path = os.path.join(JEONGSI_DIR, f"{university_key}_2027_jeongsi.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_doc(doc: dict, known_type_names: set[str] | None = None,
                 known_department_names: set[str] | None = None) -> dict:
    """계산식 문서 하나를 검증한다. {errors, warnings, formulas:[{formula_id, perfect, sample, examples}]}."""
    errors, warnings, results = [], [], []
    if doc.get("schema") != SCHEMA:
        errors.append(f"schema는 {SCHEMA}")
    for k in ("university_key", "university_name", "academic_year"):
        if not doc.get(k):
            errors.append(f"필수 칸 없음: {k}")
    if not doc.get("formulas") and not doc.get("gaps") and not doc.get("not_covered"):
        errors.append("formulas가 비었으면 gaps(원문 미확보) 또는 not_covered(전형별 사유)를 적어야 한다")
    if doc.get("formulas") and not doc.get("documents"):
        errors.append("필수 칸 없음: documents")
    if doc.get("academic_year") not in (None, 2027):
        errors.append("academic_year는 2027")
    doc_keys = {d.get("document_key") for d in doc.get("documents") or []}
    for d in doc.get("documents") or []:
        if not (d.get("file_url") or d.get("source_url")):
            errors.append(f"문서 {d.get('document_key')}: 출처 주소 없음")
    if (known_type_names is None or known_department_names is None) and doc.get("university_key"):
        js = _load_jeongsi(doc["university_key"])
        if js is not None:
            if known_type_names is None:
                known_type_names = {t["name"] for t in js.get("admission_types", [])}
            if known_department_names is None:
                known_department_names = {d.get("department") for d in js.get("departments", []) if d.get("department")}
    covered: set[str] = set()
    ids = set()
    for i, fm in enumerate(doc.get("formulas") or []):
        fid = fm.get("formula_id") or f"#{i}"
        if fid in ids:
            errors.append(f"{fid}: formula_id 중복")
        ids.add(fid)
        res = {"formula_id": fid}
        for k in ("label", "applies_to", "expression", "evidence_pages", "raw_text", "document_key"):
            if not fm.get(k):
                errors.append(f"{fid}: 필수 칸 없음: {k}")
        if fm.get("document_key") and fm["document_key"] not in doc_keys:
            errors.append(f"{fid}: document_key {fm['document_key']}가 documents에 없음")
        types = (fm.get("applies_to") or {}).get("type_names") or []
        if not types:
            errors.append(f"{fid}: applies_to.type_names 없음")
        if known_type_names is not None:
            for t in types:
                if t not in known_type_names:
                    errors.append(f"{fid}: 2027 정시 자료에 없는 전형명 {t!r}")
        covered.update(types)
        depts = (fm.get("applies_to") or {}).get("department_names") or []
        if known_department_names is not None:
            for dn in depts:
                if dn not in known_department_names:
                    errors.append(f"{fid}: 2027 정시 자료에 없는 모집단위명 {dn!r}")
        tables = fm.get("tables") or {}
        for tname, tb in tables.items():
            if not isinstance(tb, dict) or not tb:
                errors.append(f"{fid}: 표 {tname}가 비었거나 형식이 틀림")
                continue
            if tname.startswith(("ENG", "HIST", "FL")) or tname.endswith("_GRADE"):
                missing = [g for g in GRADE_KEYS if g not in tb]
                if missing:
                    errors.append(f"{fid}: 등급표 {tname}에 {','.join(missing)}등급 없음")
            for kk, vv in tb.items():
                if vv is not None and not isinstance(vv, (int, float)):
                    errors.append(f"{fid}: 표 {tname}[{kk}] 값이 숫자가 아님")
        try:
            variables, used_tables = names_in(fm.get("expression") or "0")
        except FormulaError as e:
            errors.append(f"{fid}: {e}")
            results.append(res)
            continue
        unknown = sorted(v for v in variables if v not in VARIABLES)
        if unknown:
            errors.append(f"{fid}: 모르는 변수 {unknown}")
        for t in used_tables - set(tables):
            errors.append(f"{fid}: 수식이 쓰는 표 {t}가 tables에 없음")
        for t in set(tables) - used_tables:
            warnings.append(f"{fid}: 표 {t}를 수식이 쓰지 않음")
        res["uses"] = sorted(variables)
        res["pending_inputs"] = sorted(v for v in variables if v in PENDING_VARIABLES)
        if unknown or used_tables - set(tables):
            results.append(res)
            continue
        try:
            res["perfect"] = evaluate(fm["expression"], perfect_inputs(), tables)
            res["sample"] = evaluate(fm["expression"], sample_inputs(), tables)
        except FormulaError as e:
            errors.append(f"{fid}: 계산 실패 {e}")
            results.append(res)
            continue
        exp_max = fm.get("perfect_score_expected")
        if exp_max is not None and abs(res["perfect"] - float(exp_max)) > 0.01:
            errors.append(f"{fid}: 만점 입력 결과 {res['perfect']:.4f} ≠ 원문 만점 {exp_max}")
        ex_out = []
        for j, ex in enumerate(fm.get("examples") or []):
            inp = dict(perfect_inputs())
            inp.update(ex.get("inputs") or {})
            try:
                got = evaluate(fm["expression"], inp, tables)
            except FormulaError as e:
                errors.append(f"{fid}: 예시 {j} 계산 실패 {e}")
                continue
            tol = float(ex.get("tolerance", 0.01))
            ok = abs(got - float(ex["expected"])) <= tol
            ex_out.append({"expected": ex["expected"], "got": round(got, 4), "match": ok, "page": ex.get("page")})
            if not ok:
                errors.append(f"{fid}: 예시 {j} 결과 {got:.4f} ≠ 원문 {ex['expected']}")
        res["examples"] = ex_out
        results.append(res)
    if known_type_names is not None:
        not_covered = sorted(t for t in known_type_names - covered)
        listed = set((doc.get("not_covered") or {}).keys())
        for t in not_covered:
            if t not in listed:
                warnings.append(f"계산식이 없는 정시 전형(사유는 not_covered에 적을 것): {t}")
    return {"errors": errors, "warnings": warnings, "formulas": results}


def validate_file(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    return validate_doc(doc)


def main(argv: list[str]) -> int:
    paths = sorted(glob.glob(os.path.join(FORMULA_DIR, "*_2027_jeongsi_formula.json"))) if "--all" in argv else \
        [a for a in argv if not a.startswith("--")]
    bad = 0
    for p in paths:
        r = validate_file(p)
        name = os.path.basename(p)
        print(f"{name}: 오류 {len(r['errors'])} · 경고 {len(r['warnings'])} · 계산식 {len(r['formulas'])}")
        for e in r["errors"]:
            print("  오류:", e)
        for w in r["warnings"]:
            print("  경고:", w)
        if r["errors"]:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
