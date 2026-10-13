#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ipsi_seed — 연구 산물(discovery·article JSON)을 Spring 입시 DB 스키마(V1064+) 형태로 정규화.

역할(작업지시 2·3단계):
  · 출처 레지스트리(source_registry.SOURCES) → ipsi_sources 행
  · 수집된 후보·본문 → ipsi_documents(url_hash dedup) + ipsi_document_versions(버전 1)
  · 검증 규칙 적용:
      - 적용학년도·출처가 없는 자료는 표시(상담 검색 제외 대상)
      - 재배포 제한(METADATA_PRIORITY) 자료는 원문/본문을 시드에 넣지 않고 메타+링크만
      - EBS 해설·전략은 content_class=NON_OFFICIAL_RULE로 공식 규정과 분리
  · collected vs failed / dedup / missing-year / missing-source 카운트 리포트

이 스크립트는 **로컬 시드 산물(JSON)**만 만든다. 운영 DB에 직접 쓰지 않는다(작업지시 5단계 금지).
적재는 IpsiDocumentIngestService(Java) 또는 dev 시드 경로를 통해서만 수행.
"""
from __future__ import annotations
import json, glob, os, hashlib, datetime
from source_registry import SOURCES, by_key

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
PARSED = os.path.join(DATA, "parsed")
ARTICLES = os.path.join(PARSED, "articles")
OUTDIR = os.path.join(DATA, "seed")

DISCOVERY_FILES = {  # source_key -> discovery json
    "kcue": "discovery_kcue.json",
    "moe": "discovery_moe.json",
    "ebsi": "discovery_ebsi.json",
    "kcue_library": "discovery_kcue_library.json",
    "suneung": "discovery_suneung.json",
}


def sha256(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def derive_document_type(title: str, has_attachment: bool) -> str:
    t = title or ""
    if "시행계획" in t or "시행계획모음" in t:
        return "IMPLEMENTATION_PLAN"
    if "모집요강" in t:
        return "GUIDE_BOOK"
    if "확정" in t or "발표" in t:
        return "MOE_CONFIRMED"
    if has_attachment:
        return "ATTACHMENT"
    return "PRESS_RELEASE"


def build_sources() -> list[dict]:
    rows = []
    for s in SOURCES:
        rows.append({
            "source_key": s["source_key"],
            "institution_name": s["institution_name"],
            "institution_type": s["institution_type"],
            "base_url": s.get("base_url") or None,
            "robots_our_ua_allowed": s.get("robots_our_ua_allowed"),
            "redistribution": s["redistribution"],
            "access_method": s["access_method"],
            "content_class": s.get("content_class", "OFFICIAL_RULE"),
            "collect_status": s.get("collect_status"),
            "is_active": True,
        })
    return rows


def build_documents_and_versions(now_iso: str):
    """url_hash로 dedup하며 문서+버전1을 만든다. article(본문 파싱)이 후보보다 우선(정도가 높음)."""
    docs: dict[str, dict] = {}

    def ensure(url, url_hash, source_key, institution, title, published_at,
               academic_year, content_class, status, has_attachment, excerpt):
        if not url_hash:
            url_hash = sha256(url)
        existing = docs.get(url_hash)
        rank = {"COLLECTED": 0, "EXTRACTED": 1}
        if existing and rank.get(status, 0) <= rank.get(existing["_status"], 0):
            # 이미 같은/더 높은 단계 — 갱신하지 않음(dedup)
            return
        src = by_key(source_key) or {}
        redistribution = src.get("redistribution", "METADATA_PRIORITY")
        store_body = (redistribution == "OPEN")
        docs[url_hash] = {
            "url_hash": url_hash,
            "source_key": source_key,
            "original_url": url,
            "institution_name": institution or src.get("institution_name"),
            "document_name": (title or "").strip() or "(제목없음)",
            "document_type": derive_document_type(title, has_attachment),
            "applicable_academic_year": academic_year or None,
            "published_at": published_at or None,
            "content_class": content_class or src.get("content_class", "OFFICIAL_RULE"),
            "redistribution": redistribution,
            "_status": status,
            "_collected_at": now_iso,
            "_search_text": (excerpt[:1200] if store_body and excerpt else None),
            "_raw_present": store_body,
        }

    # 1) 후보(발견만 된 것) — COLLECTED
    for source_key, fname in DISCOVERY_FILES.items():
        arr = load_json(os.path.join(PARSED, fname))
        if not isinstance(arr, list):
            continue
        src = by_key(source_key) or {}
        for c in arr:
            ensure(c.get("url"), c.get("url_hash"), source_key,
                   src.get("institution_name"), c.get("title"), None, None,
                   src.get("content_class", "OFFICIAL_RULE"), "COLLECTED",
                   bool(c.get("is_attachment")), None)

    # 2) 본문 파싱된 article — EXTRACTED(우선)
    for path in glob.glob(os.path.join(ARTICLES, "*.json")):
        a = load_json(path)
        if not a:
            continue
        src = by_key(a.get("source_key", "")) or {}
        ensure(a.get("url"), a.get("url_hash"), a.get("source_key"),
               a.get("institution_name"), a.get("title"), a.get("published_at"),
               a.get("academic_year"), a.get("content_class") or src.get("content_class"),
               "EXTRACTED", bool(a.get("attachments")), a.get("body_text"))

    documents, versions = [], []
    for i, d in enumerate(sorted(docs.values(), key=lambda x: x["url_hash"]), start=1):
        status = d.pop("_status")
        collected_at = d.pop("_collected_at")
        search_text = d.pop("_search_text")
        raw_present = d.pop("_raw_present")
        content_hash = sha256("|".join([d["document_name"], str(d["published_at"]),
                                        str(d["applicable_academic_year"]), status]))
        documents.append(d)
        versions.append({
            "url_hash": d["url_hash"],
            "version_no": 1,
            "content_hash": content_hash,
            "raw_storage_key": ("research/raw/" + d["url_hash"][:16]) if raw_present else None,
            "structured_json": None,
            "search_text": search_text,
            "collected_at": collected_at,
            "verification_status": status,
            "change_note": "1차 시드(발견/추출). 미승인 — 상담검색 비노출.",
        })
    return documents, versions


def verification_counts(documents, versions):
    vmap = {v["url_hash"]: v for v in versions}
    missing_year = [d for d in documents if not d["applicable_academic_year"]]
    missing_source = [d for d in documents if not d["original_url"]]
    official = [d for d in documents if d["content_class"] == "OFFICIAL_RULE"]
    nonofficial = [d for d in documents if d["content_class"] == "NON_OFFICIAL_RULE"]
    extracted = [v for v in versions if v["verification_status"] == "EXTRACTED"]
    return {
        "documents": len(documents),
        "unique_after_dedup": len(documents),  # keyed by url_hash → 이미 dedup
        "versions": len(versions),
        "extracted_with_body": len(extracted),
        "metadata_only": len(versions) - len(extracted),
        "official_rule": len(official),
        "non_official_rule": len(nonofficial),
        "missing_applicable_academic_year": len(missing_year),
        "missing_source_url": len(missing_source),
    }


def failed_sources():
    blocked = [s["source_key"] for s in SOURCES if s.get("collect_status") == "BLOCKED_BY_ROBOTS"]
    js = [s["source_key"] for s in SOURCES if s.get("access_method") == "JS_REQUIRED"]
    pending = [s["source_key"] for s in SOURCES
               if s.get("robots_our_ua_allowed") is True
               and s.get("access_method") == "HTTP_STATIC"
               and s.get("collect_status") == "PENDING"]
    return {"blocked_by_robots": blocked, "js_required": js, "pending_unexpanded": pending}


def main():
    now_iso = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    os.makedirs(OUTDIR, exist_ok=True)
    sources = build_sources()
    documents, versions = build_documents_and_versions(now_iso)
    counts = verification_counts(documents, versions)
    counts["failed"] = failed_sources()
    seed = {"generated_at": now_iso, "sources": sources,
            "documents": documents, "document_versions": versions}
    with open(os.path.join(OUTDIR, "ipsi_seed.json"), "w", encoding="utf-8") as f:
        json.dump(seed, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUTDIR, "build_report.json"), "w", encoding="utf-8") as f:
        json.dump(counts, f, ensure_ascii=False, indent=1)

    print(f"ipsi_sources   : {len(sources)}")
    print(f"ipsi_documents : {len(documents)} (dedup by url_hash)")
    print(f"ipsi_versions  : {len(versions)}")
    print(f"  EXTRACTED(본문) : {counts['extracted_with_body']} / 메타만 : {counts['metadata_only']}")
    print(f"  공식규정 : {counts['official_rule']} / 비공식(EBS) : {counts['non_official_rule']}")
    print(f"  적용학년도 누락 : {counts['missing_applicable_academic_year']} "
          f"/ 출처URL 누락 : {counts['missing_source_url']}")
    print(f"failed/blocked : {counts['failed']}")


if __name__ == "__main__":
    main()
