#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
discover_docs — 시드 게시판을 robots-존중 크롤링해 입시 문서 후보를 추출·기록한다.

파이프라인 위치: [수집(discover)] → 추출 → 정규화 → 검증 → 승인. 이 스크립트는 '수집' 첫 단계다.
- source_registry의 crawlable_sources() 시드 게시판만 방문(robots False 출처는 자동 제외).
- 각 게시판 HTML에서 <a> 링크·앵커 텍스트를 뽑아 입시 키워드/첨부 확장자로 필터링한다.
- 후보는 parsed/discovery_<source_key>.json에, 집계는 parsed/discovery_state.json에 남긴다.
- 본문 원문은 ipsi_fetch가 raw/에 저장(재배포 제한 출처는 store_raw=False로 메타만).
- 수집 ≠ 검증: 모든 후보 verification_status=COLLECTED로 시작.

사용:
  python discover_docs.py                # 전체 crawlable 출처
  python discover_docs.py kcue moe       # 지정 출처만
  python discover_docs.py --no-raw       # raw 저장 없이 링크·메타만
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

from bs4 import BeautifulSoup

import source_registry as reg
from ipsi_fetch import IpsiFetcher, absolutize, sha256_text, COLLECTED

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.normpath(os.path.join(HERE, "..", "data"))
PARSED = os.path.join(RESEARCH, "parsed")
os.makedirs(PARSED, exist_ok=True)

# 입시 문서 후보 판별 키워드 (제목/앵커 텍스트)
KEYWORDS = [
    "시행계획", "모집요강", "대입전형", "입학전형", "전형계획", "전형일정",
    "입시결과", "경쟁률", "충원합격", "등록자", "수시", "정시", "대학입학",
    "입학가이드", "전형안내", "지원자격", "학생부", "수능", "2028", "2027", "2026",
]
KW_RE = re.compile("|".join(re.escape(k) for k in KEYWORDS))
ATTACH_EXT = re.compile(r"\.(pdf|hwp|hwpx|doc|docx|xls|xlsx|ppt|pptx|zip)(?:[?#]|$)", re.IGNORECASE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def extract_candidates(html: str, board_url: str, source_key: str, board_name: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    out: list[dict] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        abs_url = absolutize(board_url, href)
        if not abs_url.startswith("http"):
            continue
        text = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
        is_attach = bool(ATTACH_EXT.search(abs_url))
        kw_hits = sorted(set(KW_RE.findall(text))) if text else []
        # 후보 조건: 키워드 매칭 OR 첨부파일 OR 학년도 토큰 in url
        url_year = re.search(r"20(2[6-9])", abs_url)
        if not (kw_hits or is_attach or url_year):
            continue
        if abs_url in seen:
            continue
        seen.add(abs_url)
        out.append({
            "source_key": source_key,
            "board_name": board_name,
            "board_url": board_url,
            "title": text or "(무제 앵커)",
            "url": abs_url,
            "url_hash": sha256_text(abs_url),
            "matched_keywords": kw_hits,
            "is_attachment": is_attach,
            "verification_status": COLLECTED,
            "collected_at": _now_iso(),
        })
    return out


def discover_source(fetcher: IpsiFetcher, source: dict, store_raw: bool) -> dict:
    key = source["source_key"]
    result = {
        "source_key": key,
        "institution_name": source["institution_name"],
        "robots_our_ua_allowed": source.get("robots_our_ua_allowed"),
        "access_method": source.get("access_method"),
        "boards_total": len(source.get("seed_boards", [])),
        "boards_fetched": 0,
        "boards_blocked": 0,
        "boards_failed": 0,
        "candidates": 0,
        "attachments": 0,
        "errors": [],
        "redistribution": source.get("redistribution"),
        "content_class": source.get("content_class", "OFFICIAL_RULE"),
    }
    # 재배포 제한 출처는 본문 raw 저장 안 함(메타+링크 우선)
    do_store_raw = store_raw and source.get("redistribution") != "METADATA_PRIORITY"

    all_candidates: list[dict] = []
    for board in source.get("seed_boards", []):
        bname, burl = board["name"], board["url"]
        res = fetcher.fetch(burl, store_raw=do_store_raw, save_meta=True)
        if not res.robots_allowed:
            result["boards_blocked"] += 1
            result["errors"].append(f"BLOCKED robots: {burl}")
            continue
        if not res.ok:
            result["boards_failed"] += 1
            result["errors"].append(f"FAIL {res.http_status} {res.error}: {burl}")
            continue
        result["boards_fetched"] += 1
        html = fetcher.text_of(res) or ""
        cands = extract_candidates(html, res.final_url or burl, key, bname)
        all_candidates.extend(cands)

    # url 기준 중복 제거
    dedup: dict[str, dict] = {}
    for c in all_candidates:
        dedup.setdefault(c["url"], c)
    final = list(dedup.values())
    result["candidates"] = len(final)
    result["attachments"] = sum(1 for c in final if c["is_attachment"])

    out_path = os.path.join(PARSED, f"discovery_{key}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    result["output_file"] = os.path.relpath(out_path, RESEARCH).replace(os.sep, "/")
    return result


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    store_raw = "--no-raw" not in argv
    only = set(args)

    sources = reg.crawlable_sources()
    if only:
        sources = [s for s in sources if s["source_key"] in only]

    fetcher = IpsiFetcher(store_raw=store_raw)
    states = []
    for s in sources:
        print(f"\n=== discover: {s['source_key']} ({s['institution_name']}) ===")
        st = discover_source(fetcher, s, store_raw)
        states.append(st)
        print(f"  boards {st['boards_fetched']}/{st['boards_total']} fetched, "
              f"blocked={st['boards_blocked']} failed={st['boards_failed']}")
        print(f"  candidates={st['candidates']} (attachments={st['attachments']}) -> {st['output_file']}")
        for e in st["errors"][:5]:
            print("   !", e)

    state_path = os.path.join(PARSED, "discovery_state.json")
    summary = {
        "generated_at": _now_iso(),
        "sources_crawled": len(states),
        "total_boards_fetched": sum(s["boards_fetched"] for s in states),
        "total_boards_blocked": sum(s["boards_blocked"] for s in states),
        "total_boards_failed": sum(s["boards_failed"] for s in states),
        "total_candidates": sum(s["candidates"] for s in states),
        "total_attachments": sum(s["attachments"] for s in states),
        "sources": states,
    }
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n=== SUMMARY ===")
    print(f"sources={summary['sources_crawled']} boards_fetched={summary['total_boards_fetched']} "
          f"blocked={summary['total_boards_blocked']} failed={summary['total_boards_failed']}")
    print(f"candidates={summary['total_candidates']} attachments={summary['total_attachments']}")
    print(f"state -> {os.path.relpath(state_path, RESEARCH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
