"""정시 환산에 필요한 수능 발표 값 — 검증.

두 가지 원문 값을 다룬다. 형식 설명: docs/schema/JEONGSI_STATS.md
- csat_std_max/v1: 한국교육과정평가원 수능 채점결과의 영역·과목별 표준점수 최고점(KOR_STD_MAX, MATH_STD_MAX, INQ*_STD_MAX)
- conversion_score/v1: 대학이 발표한 탐구 변환표준점수표(백분위 → 변환표준점수, INQ*_CONV, INQ*_CONV_MAX)

사용:
    python3 scripts/jeongsi_stats.py data/parsed/jeongsi_stats/{파일}.json
    python3 scripts/jeongsi_stats.py --all
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jeongsi_formula as jf  # noqa: E402

ROOT = jf.ROOT
STATS_DIR = os.path.join(ROOT, "data", "parsed", "jeongsi_stats")
FORMULA_DIR = os.path.join(ROOT, "data", "parsed", "jeongsi_formula")
STD_MAX_SCHEMA = "csat_std_max/v1"
CONVERSION_SCHEMA = "conversion_score/v1"
TRACKS = {"SOC", "SCI", "VOC"}  # 사회탐구·과학탐구·직업탐구 (formula 변수 INQ*_SOC/SCI/VOC와 같은 구분)
PERCENTILES = [str(p) for p in range(0, 101)]


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check_source(doc: dict, errors: list[str]) -> None:
    src = doc.get("source") or {}
    for k in ("institution_name", "document_name"):
        if not src.get(k):
            errors.append(f"source.{k} 없음")
    if not (src.get("file_url") or src.get("source_page_url")):
        errors.append("source.file_url 또는 source.source_page_url 없음")


def validate_std_max(doc: dict) -> dict:
    """표준점수 최고점 문서 검증. 값이 아직 발표되지 않았으면(null) 오류가 아니라 published=false로 본다."""
    errors: list[str] = []
    warnings: list[str] = []
    if doc.get("schema") != STD_MAX_SCHEMA:
        errors.append(f"schema가 {STD_MAX_SCHEMA}가 아님")
    if not isinstance(doc.get("academic_year"), int):
        errors.append("academic_year 없음")
    _check_source(doc, errors)
    areas = doc.get("areas") or {}
    for a in ("KOR", "MATH"):
        if a not in areas:
            errors.append(f"areas.{a} 항목 없음(발표 전이면 null)")
    values = [v for v in areas.values() if v is not None]
    seen = set()
    for i, s in enumerate(doc.get("inquiry") or []):
        name = s.get("subject")
        if not name:
            errors.append(f"inquiry[{i}].subject 없음")
            continue
        if name in seen:
            errors.append(f"inquiry 과목 중복: {name}")
        seen.add(name)
        if s.get("track") not in TRACKS:
            errors.append(f"inquiry[{name}].track은 {sorted(TRACKS)} 중 하나")
        if s.get("std_max") is not None:
            values.append(s["std_max"])
    for v in values:
        if not _num(v) or not (0 < v <= 200):
            errors.append(f"표준점수 최고점 범위(0~200) 밖: {v}")
    published = all(areas.get(a) is not None for a in ("KOR", "MATH")) and all(
        s.get("std_max") is not None for s in doc.get("inquiry") or [])
    if values and not published:
        warnings.append("일부 값만 있음 — 모두 채워야 적재한다")
    if published and not doc.get("inquiry"):
        warnings.append("탐구 과목별 최고점이 없음")
    if published and not doc.get("evidence_pages"):
        warnings.append("evidence_pages 없음")
    return {"errors": errors, "warnings": warnings, "published": published and not errors}


def _formula_uses_conversion(university_key: str) -> bool | None:
    path = os.path.join(FORMULA_DIR, f"{university_key}_2027_jeongsi_formula.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    return any(re.search(r"INQ[12]_CONV", x.get("expression", "")) for x in doc.get("formulas") or [])


def validate_conversion(doc: dict) -> dict:
    """대학 변환표준점수표 검증. 백분위 0~100 전부, 백분위가 낮을수록 점수가 같거나 낮아야 한다."""
    errors: list[str] = []
    warnings: list[str] = []
    if doc.get("schema") != CONVERSION_SCHEMA:
        errors.append(f"schema가 {CONVERSION_SCHEMA}가 아님")
    for k in ("university_key", "university_name"):
        if not doc.get(k):
            errors.append(f"{k} 없음")
    if not isinstance(doc.get("academic_year"), int):
        errors.append("academic_year 없음")
    _check_source(doc, errors)
    tables = doc.get("tables") or []
    if not tables and not doc.get("gaps"):
        errors.append("tables 또는 gaps 중 하나는 있어야 함")
    tracks = set()
    for i, t in enumerate(tables):
        track = t.get("track")
        if track not in TRACKS:
            errors.append(f"tables[{i}].track은 {sorted(TRACKS)} 중 하나")
        if track in tracks:
            errors.append(f"tables[{i}]: 같은 track 표가 두 개({track})")
        tracks.add(track)
        scores = t.get("scores") or {}
        missing = [p for p in PERCENTILES if p not in scores]
        extra = [p for p in scores if p not in PERCENTILES]
        if missing:
            errors.append(f"tables[{track}]: 백분위 빠짐 {missing[:5]}{'…' if len(missing) > 5 else ''}")
        if extra:
            errors.append(f"tables[{track}]: 백분위가 아닌 키 {extra[:5]}")
        prev = None
        for p in reversed(PERCENTILES):  # 100 → 0
            v = scores.get(p)
            if v is None:
                continue
            if not _num(v) or not (0 <= v <= 200):
                errors.append(f"tables[{track}] 백분위 {p}: 점수 범위(0~200) 밖 {v}")
            elif prev is not None and v > prev:
                errors.append(f"tables[{track}] 백분위 {p}: 점수가 위 백분위보다 큼({v} > {prev})")
            prev = v if _num(v) else prev
        if not t.get("evidence_pages"):
            warnings.append(f"tables[{track}]: evidence_pages 없음")
    uses = _formula_uses_conversion(doc.get("university_key") or "")
    if uses is None:
        warnings.append("이 대학의 정시 계산식 파일이 없음")
    elif uses is False and tables:
        warnings.append("이 대학 계산식은 변환표준점수(INQ*_CONV)를 쓰지 않음")
    return {"errors": errors, "warnings": warnings}


def validate_file(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    if doc.get("schema") == STD_MAX_SCHEMA:
        return validate_std_max(doc)
    return validate_conversion(doc)


def main(argv: list[str]) -> int:
    paths = sorted(glob.glob(os.path.join(STATS_DIR, "*.json"))) if argv == ["--all"] else argv
    if not paths:
        print("검증할 파일이 없습니다.")
        return 0
    failed = 0
    for p in paths:
        r = validate_file(p)
        failed += bool(r["errors"])
        print(f"{os.path.basename(p)}: 오류 {len(r['errors'])} · 경고 {len(r['warnings'])}")
        for e in r["errors"]:
            print(f"  오류: {e}")
        for w in r["warnings"]:
            print(f"  경고: {w}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
