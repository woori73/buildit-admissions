"""서울 주요 대학 2028학년도 대학입학전형 시행계획 요약 → 상담 근거 지식 시드.

입력: data/collect/univ_2028/group_*.json (2026-11-23 수집. 대학별 주제 6개: 전형·모집인원, 수능최저, 5등급 내신 반영,
정시 반영비율, 권장과목, 2027 대비 변경).
대학 원문(official)은 "시행계획 기준"으로, 언론 보도만 있는 주제는 본문 첫머리에 "언론 보도 기준(대학 원문 미확인)"을 적어 싣는다.
검색 결과가 아닌 주소 규칙으로 찾은 원문(한국외대·이화여대, 내용은 내려받아 확인)은 대표 결정(2026-11-23 "24건 넣기")으로 싣는다.
출력: data/seed/reform_2028/ipsi_seed_univ_2028_plans.json (load/seed → activate-all(2028)).
"""
from __future__ import annotations

import glob
import json
import os
import re
import urllib.parse
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "data", "collect", "univ_2028"))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "seed", "reform_2028", "ipsi_seed_univ_2028_plans.json"))
YEAR = 2028

TOPICS = {
    "susi_types": ("전형과 모집인원", "수시, 정시, 전형, 모집인원, 학생부교과, 학생부종합, 논술, 실기"),
    "susi_minimum": ("수시 수능최저학력기준", "수능최저, 수능 최저, 최저학력기준, 수시, 등급 합"),
    "grade_conversion": ("5등급 내신 반영 방법", "5등급제, 내신 반영, 등급 점수, 성취도, 교과 반영, 정성평가"),
    "jeongsi_ratio": ("정시 영역별 반영비율·학생부 반영", "정시, 반영비율, 수능 반영, 영어 반영, 한국사, 탐구 반영, 정시 학생부, 교과평가"),
    "recommended_courses": ("권장과목(전공 연계 과목)", "권장과목, 권장 과목, 전공 연계 과목, 핵심과목, 과목 선택, 이수 과목"),
    "changes": ("2027 대비 바뀐 점", "변경사항, 바뀐 점, 달라진 점, 신설, 폐지, 2027 대비"),
}
SHORT = {"서울대학교": "서울대", "연세대학교": "연세대", "고려대학교": "고려대", "서강대학교": "서강대", "성균관대학교": "성균관대",
         "한양대학교": "한양대", "중앙대학교": "중앙대", "경희대학교": "경희대", "한국외국어대학교": "한국외대", "서울시립대학교": "서울시립대",
         "이화여자대학교": "이화여대", "건국대학교": "건국대", "동국대학교": "동국대", "홍익대학교": "홍익대", "숙명여자대학교": "숙명여대",
         "국민대학교": "국민대"}
CODE = {"서울대학교": "SNU", "연세대학교": "YONSEI", "고려대학교": "KOREA", "서강대학교": "SOGANG", "성균관대학교": "SKKU",
        "한양대학교": "HANYANG", "중앙대학교": "CAU", "경희대학교": "KHU", "한국외국어대학교": "HUFS", "서울시립대학교": "UOS",
        "이화여자대학교": "EWHA", "건국대학교": "KONKUK", "동국대학교": "DONGGUK", "홍익대학교": "HONGIK", "숙명여자대학교": "SOOKMYUNG",
        "국민대학교": "KOOKMIN"}

# 검색 결과나 읽은 페이지에서 나오지 않고 같은 사이트의 주소 규칙으로 만든 주소(내용은 내려받아 확인). 대표 결정으로 싣는다(2026-11-23).
CONSTRUCTED_URLS = {
    "https://cdn013.negagea.net/dgsmidc/omr/seoul/web/univ_info2026/한국외국어대학교/한국외국어대학교_2028학년도_대학입학전형계획.pdf",
    "https://cdn013.negagea.net/dgsmidc/omr/seoul/web/univ_info2026/이화여자대학교/이화여자대학교_2028학년도_대학입학전형계획.pdf",
}


def load_groups() -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(SRC, "group_*.json"))):
        with open(path, encoding="utf-8") as f:
            out.extend(json.load(f)["universities"])
    return out


def item_for(univ: str, it: dict) -> dict | None:
    """수집 항목 하나를 지식 항목으로. 언론 보도만 있는 항목은 본문에 그렇게 밝힌다."""
    if it.get("source_kind") not in ("official", "press") or it["topic"] not in TOPICS:
        return None
    if not re.match(r"^https://", it["source_url"]):
        return None
    label, tags = TOPICS[it["topic"]]
    short = SHORT.get(univ, univ)
    when = f"({it['published']} 공고)" if it.get("published") else ""
    return {
        "id": f"U2028-{CODE[univ]}-{it['topic'].upper().replace('_', '-')}",
        "title": f"{univ} 2028학년도 {label}",
        "tags": f"{univ}, {short}, 2028학년도, 2028, 시행계획, 현 고2, {tags}",
        "content": (f"{univ} 2028학년도 대학입학전형 시행계획{when} 기준. {it['text'].strip()}"
                    if it["source_kind"] == "official"
                    else f"{univ} 2028학년도 {label} — 언론 보도 기준(대학 원문 미확인, {it.get('source_title', '').strip()}). {it['text'].strip()}"),
        # 한글이 든 주소(대학 원문 PDF)는 퍼센트 인코딩해 둔다.
        "source_url": urllib.parse.quote(it["source_url"], safe=":/?&=%()#+~"),
    }


def build() -> dict:
    official, held = [], []
    for u in load_groups():
        for it in u["items"]:
            k = item_for(u["name"], it)
            if k:
                official.append({**k, "academic_year": YEAR, "category": "대학 시행계획"})
            else:
                held.append({"university": u["name"], "topic": it["topic"], "source_kind": it.get("source_kind"),
                             "reason": "주제·출처 종류 불명"})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gate": "대학별 2028 시행계획 요약. load/seed 후 activate-all(2028)로 승격하기 전까지 상담 검색에 쓰이지 않는다.",
        "part": "1/1",
        "ipsi_universities": [
            {"code": "snu", "university_code": "SNU", "name": "서울대학교", "establishment_type": "국립", "region": "서울",
             "admission_office_url": "https://admission.snu.ac.kr/"}
        ],
        "official_knowledge": official,
        "youtube_knowledge": [],
        "held": held,
    }


def main() -> None:
    seed = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {OUT}: official={len(seed['official_knowledge'])} held={len(seed['held'])}")


if __name__ == "__main__":
    main()
