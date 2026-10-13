#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_article — 수집된 게시판 글 상세 페이지에서 문서 메타·본문·첨부를 추출한다.

파이프라인: 수집(discover) → **추출(parse)** → 정규화(build_seed) → 검증 → 승인.
- robots gate는 ipsi_fetch가 담당(여기선 이미 허용된 URL만 페치).
- 추출 결과는 parsed/articles/<url_hash>.json + verification_status=EXTRACTED.
- 추출 ≠ 검증: 본문·날짜·첨부는 휴리스틱으로 뽑되, 대조 확인 전까지 EXTRACTED(승격 안 함).
- 적용 학년도·출처를 못 밝힌 문서는 academic_year=None → 이후 상담검색 제외 대상.

범용 추출 + 호스트별 미세 조정(kcue/moe/ebsi). 본문은 '최대 텍스트 블록' 휴리스틱.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from ipsi_fetch import IpsiFetcher, sha256_text

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.normpath(os.path.join(HERE, "..", "data"))
ART_DIR = os.path.join(RESEARCH, "parsed", "articles")
os.makedirs(ART_DIR, exist_ok=True)

EXTRACTED = "EXTRACTED"
YEAR_RE = re.compile(r"(20\d{2})\s*학년도")
LOOSE_YEAR_RE = re.compile(r"(20\d{2})")
DATE_RE = re.compile(r"(20\d{2})[-./년]\s*(\d{1,2})[-./월]\s*(\d{1,2})")
ATTACH_RE = re.compile(r"\.(pdf|hwp|hwpx|doc|docx|xls|xlsx|ppt|pptx|zip)(?:[?#]|$)", re.IGNORECASE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _clean(t: str) -> str:
    t = t.replace("\u200b", "")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return t.strip()


def _pick_title(soup: BeautifulSoup) -> str:
    # 호스트별 명시 셀렉터 우선 (kcue 상세)
    for sel in [".subject-name", ".board_tit", ".tit_view", "h3.tit"]:
        el = soup.select_one(sel)
        if el:
            txt = _clean(el.get_text(" ", strip=True))
            if len(txt) >= 4:
                return txt
    for sel in ["meta[property='og:title']", "meta[name='title']"]:
        m = soup.select_one(sel)
        if m and (m.get("content") or "").strip():
            return _clean(m["content"])
    for tag in soup.select("h1, h2, h3, .tit, .title, .board_tit"):
        txt = _clean(tag.get_text(" ", strip=True))
        if len(txt) >= 6:
            return txt
    if soup.title:
        t = _clean(soup.title.get_text(" ", strip=True))
        if t:
            return t
    return "(제목 미확인)"


def _pick_date(soup: BeautifulSoup, html: str) -> str | None:
    # 라벨/클래스 기반(작성일·등록일·발행일, .view_date_box) 우선
    for sel in [".view_date_box", ".date", ".day", ".period"]:
        el = soup.select_one(sel)
        if el:
            m = DATE_RE.search(el.get_text(" ", strip=True))
            if m:
                return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    for lab in soup.find_all(string=re.compile(r"작성일|등록일|발행일|게시일|작성일자")):
        parent = lab.find_parent()
        if parent:
            m = DATE_RE.search(parent.get_text(" ", strip=True))
            if m:
                return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = DATE_RE.search(html)
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else None


def _pick_body(soup: BeautifulSoup) -> str:
    """가장 텍스트가 많은 컨테이너를 본문으로 추정(범용 휴리스틱)."""
    best, best_len = None, 0
    for sel in ["article.cont", "div.board_view", "div.view_con", "div.conts", "div#conts",
                "div.board_content", "td.view_con", "article", "div.contents", "div#contents", "div.body"]:
        el = soup.select_one(sel)
        if el:
            txt = _clean(el.get_text("\n", strip=True))
            if len(txt) > best_len:
                best, best_len = txt, len(txt)
    if best is None:
        for el in soup.find_all(["div", "td", "section", "article"]):
            txt = _clean(el.get_text("\n", strip=True))
            if len(txt) > best_len:
                best, best_len = txt, len(txt)
    return best or ""


def _pick_attachments(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """첨부: 파일확장자가 href나 앵커 텍스트에 있거나, download 엔드포인트 링크."""
    from urllib.parse import urljoin
    out, seen = [], set()
    for a in soup.find_all("a"):
        href = a.get("href", "") or ""
        name = _clean(a.get_text(" ", strip=True))
        onclick = (a.get("onclick", "") or "").lower()
        text_has_ext = bool(ATTACH_RE.search(name))
        href_has_ext = bool(ATTACH_RE.search(href))
        is_dl = ("download" in onclick or "at=download" in href.lower() or "filedown" in href.lower()
                 or "/file" in href.lower() or "dnldr" in href.lower() or "down=" in href.lower())
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        if (text_has_ext or href_has_ext or (is_dl and name)) and href not in seen:
            seen.add(href)
            out.append({"name": name or os.path.basename(href.split("?")[0]) or "(첨부)",
                        "url": urljoin(base_url, href),
                        "is_file_ext": text_has_ext or href_has_ext,
                        "is_download_endpoint": is_dl})
    return out[:20]


def _academic_year(title: str, body: str) -> str | None:
    for src in (title, body[:1500]):
        m = YEAR_RE.search(src)
        if m:
            return m.group(1)
    return None


def parse_html(html: str, url: str, source_key: str, institution: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = _pick_title(soup)
    body = _pick_body(soup)
    doc = {
        "url": url,
        "url_hash": sha256_text(url),
        "source_key": source_key,
        "institution_name": institution,
        "title": title,
        "published_at": _pick_date(soup, html),
        "academic_year": _academic_year(title, body),
        "body_text": body,
        "body_char_len": len(body),
        "attachments": _pick_attachments(soup, url),
        "content_class": "OFFICIAL_RULE",  # build_seed에서 source_registry로 보정(EBSi=NON_OFFICIAL_RULE)
        "verification_status": EXTRACTED,
        "collected_at": _now_iso(),
    }
    return doc


def main(argv: list[str]) -> int:
    """인자로 받은 URL들을 페치·파싱해 parsed/articles/에 저장."""
    urls = [a for a in argv[1:] if a.startswith("http")]
    if not urls:
        print("usage: python parse_article.py <url> [<url> ...]"); return 2
    import source_registry as reg
    fetcher = IpsiFetcher(store_raw=True)
    saved = []
    for u in urls:
        res = fetcher.fetch(u, store_raw=True)
        if not res.robots_allowed:
            print(f"[BLOCK] {u}"); continue
        if not res.ok:
            print(f"[FAIL {res.http_status}] {u}"); continue
        html = fetcher.text_of(res) or ""
        # source_key 추정(host 기준)
        host = re.sub(r"^https?://(www\.)?", "", u).split("/")[0]
        skey, inst = "unknown", host
        for s in reg.SOURCES:
            if s["base_url"] and host in s["base_url"]:
                skey, inst = s["source_key"], s["institution_name"]
                if s.get("content_class"):
                    pass
                break
        doc = parse_html(html, res.final_url or u, skey, inst)
        for s in reg.SOURCES:
            if s["source_key"] == skey and s.get("content_class"):
                doc["content_class"] = s["content_class"]
        path = os.path.join(ART_DIR, f"{doc['url_hash'][:24]}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        saved.append((doc["title"][:50], doc["academic_year"], doc["body_char_len"],
                      len(doc["attachments"]), os.path.relpath(path, RESEARCH)))
        print(f"[OK] year={doc['academic_year']} len={doc['body_char_len']} att={len(doc['attachments'])} :: {doc['title'][:50]}")
    print(f"\nsaved {len(saved)} article(s) -> parsed/articles/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
