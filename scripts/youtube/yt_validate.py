"""Validate the YouTube analysis DB (videos/topics/analyses/conflicts).

Counts in docs/YOUTUBE_ANALYSIS_REPORT.md must come from this script, never
from hand-written numbers.  Run from the repository root:

    python scripts/youtube/yt_validate.py
"""

import io
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "youtube")

CLASSIFICATIONS = {"OFFICIAL_FACT", "EXPERT_ANALYSIS", "PREDICTION", "STRATEGY", "DISPUTED", "OUTDATED"}
REF_STATUSES = {"OFFICIAL_CONFIRMED", "CONSISTENT_WITH_OFFICIAL", "NEEDS_OFFICIAL_DOC", "CONFLICT", "UNSUPPORTED"}
CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}
VERIFICATION = {"COLLECTED", "EXTRACTED", "NORMALIZED", "REVIEW", "APPROVED"}
EVIDENCE_TOKENS = {"metadata_only", "description", "chapters", "desc_timestamps", "video_level", "transcript", "author_correction"}
CONTENT_CLASS = {"OFFICIAL_RULE", "NON_OFFICIAL_RULE"}
REDIST = {"OPEN", "METADATA_PRIORITY", "RESTRICTED"}
ACCESS = {"HTTP_STATIC", "HTTP_PLAYWRIGHT", "MANUAL"}
ANALYSIS_STATUS = {"METADATA_ONLY", "CONTENT_ANALYZED"}
ANCHOR_SRC = {"desc_timestamp", "chapter_title", "video_level", "description_transcript", "none"}
TIER = {"TIER_1", "TIER_2", "TIER_3"}


def load(name):
    with io.open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def cjk(text):
    return [c for c in text if 0x3400 <= ord(c) <= 0x9FFF or 0xF900 <= ord(c) <= 0xFAFF or 0x3040 <= ord(c) <= 0x30FF]


def main():
    videos = load("videos.json")
    topics = load("topics.json")
    analyses = load("analyses.json")
    conflicts = load("conflicts.json")

    vrows = videos["videos"]
    arows = analyses["analyses"]
    crow = conflicts["conflicts"]
    trows = topics["topics"]

    errors = []
    vmap = {}
    for v in vrows:
        if v["video_id"] in vmap:
            errors.append("duplicate video_id %s" % v["video_id"])
        vmap[v["video_id"]] = v
        for key, allowed in (
            ("reliability_tier", TIER),
            ("content_class", CONTENT_CLASS),
            ("content_class", CONTENT_CLASS),
            ("redistribution", REDIST),
            ("access_method", ACCESS),
            ("verification_status", VERIFICATION),
            ("analysis_status", ANALYSIS_STATUS),
        ):
            if v[key] not in allowed:
                errors.append("video %s bad %s=%s" % (v["video_id"], key, v[key]))
        head = re.split(r"[+(]", v["content_evidence"])[0]
        if head not in EVIDENCE_TOKENS:
            errors.append("video %s unknown content_evidence %s" % (v["video_id"], v["content_evidence"]))
        if len(v["url_hash"]) != 64:
            errors.append("video %s bad url_hash" % v["video_id"])
        for tid in v["topic_ids"]:
            if tid not in {t["topic_id"] for t in trows}:
                errors.append("video %s unknown topic %s" % (v["video_id"], tid))
        if not v["title"] or not v["channel"]:
            errors.append("video %s missing title/channel" % v["video_id"])

    amap = {a["id"]: a for a in arows}
    if len(amap) != len(arows):
        errors.append("duplicate analysis id")
    known_conflicts = {c["id"] for c in crow}
    for a in arows:
        if a["video_id"] not in vmap:
            errors.append("%s orphan video_id %s" % (a["id"], a["video_id"]))
        else:
            v = vmap[a["video_id"]]
            if v["analysis_status"] == "METADATA_ONLY":
                errors.append("%s analyzes a METADATA_ONLY video" % a["id"])
            for tid in a["topics"]:
                if tid not in v["topic_ids"]:
                    errors.append("%s topic %s not on video %s" % (a["id"], tid, a["video_id"]))
            dur = v.get("duration_sec")
            an = a["anchor"]
            if an["src"] not in ANCHOR_SRC:
                errors.append("%s bad anchor src %s" % (a["id"], an["src"]))
            if an["t1"] is not None:
                if an["t0"] is None or an["t0"] >= an["t1"]:
                    errors.append("%s bad anchor range" % a["id"])
                if dur and an["t1"] > dur + 5:
                    errors.append("%s anchor %s exceeds duration %s" % (a["id"], an["t1"], dur))
        if a["classification"] not in CLASSIFICATIONS:
            errors.append("%s bad classification" % a["id"])
        if a["confidence"] not in CONFIDENCE:
            errors.append("%s bad confidence" % a["id"])
        if a["official_ref"]["status"] not in REF_STATUSES:
            errors.append("%s bad official_ref status" % a["id"])
        if a["verification_status"] not in VERIFICATION:
            errors.append("%s bad verification_status" % a["id"])
        if a["verification_status"] == "APPROVED":
            errors.append("%s must not be APPROVED before human sign-off" % a["id"])
        for cid in a["conflict_ids"]:
            if cid not in known_conflicts:
                errors.append("%s unknown conflict %s" % (a["id"], cid))
        if not a["claim"] or not a["evidence"]:
            errors.append("%s empty claim/evidence" % a["id"])

    cids = set()
    for c in crow:
        if c["id"] in cids:
            errors.append("duplicate conflict %s" % c["id"])
        cids.add(c["id"])
        if c["resolution"] not in {"UNRESOLVED_PENDING_DOC", "UNRESOLVED_LEGITIMATE_DISPUTE", "RESOLVED_BY_CORRECTION"}:
            errors.append("%s bad resolution" % c["id"])
        for side in ("side_a", "side_b"):
            for aid in c.get(side, {}).get("analysis_ids", []):
                if aid not in amap:
                    errors.append("%s unknown analysis id %s in %s" % (c["id"], aid, side))
        for tid in c["topic_ids"]:
            if tid not in {t["topic_id"] for t in trows}:
                errors.append("%s unknown topic %s" % (c["id"], tid))
        if not c["difference_reason"]:
            errors.append("%s missing difference_reason" % c["id"])

    stray = []
    for a in arows:
        found = cjk(json.dumps(a, ensure_ascii=False))
        if found:
            stray.append((a["id"], "".join(sorted(set(found)))))
    for c in crow:
        found = cjk(json.dumps(c, ensure_ascii=False))
        if found:
            stray.append((c["id"], "".join(sorted(set(found)))))
    for t in trows:
        found = cjk(json.dumps(t, ensure_ascii=False))
        if found:
            stray.append((t["topic_id"], "".join(sorted(set(found)))))

    analyzed = [v for v in vrows if v["analysis_status"] == "CONTENT_ANALYZED"]
    uncovered = sorted(v["video_id"] for v in analyzed if v["video_id"] not in {a["video_id"] for a in arows})

    report = {
        "videos_total": len(vrows),
        "videos_content_analyzed": len(analyzed),
        "videos_metadata_only": len(vrows) - len(analyzed),
        "videos_by_tier": dict(Counter(v["reliability_tier"] for v in vrows)),
        "videos_by_channel_kind": dict(Counter(v["channel_kind"] for v in vrows)),
        "videos_with_chapters": sum(1 for v in vrows if v["chapter_count"]),
        "videos_with_desc_timestamps": sum(1 for v in vrows if v["desc_timestamp_count"]),
        "videos_with_caption_tracks_listed": sum(1 for v in vrows if v["caption_tracks_listed"]),
        "videos_with_caption_text": sum(1 for v in vrows if v["caption_available"]),
        "distinct_channels": len({v["channel_id"] for v in vrows}),
        "distinct_presenters": len({v["presenter"] for v in vrows if v["presenter"]}),
        "topics": len(trows),
        "analyses_total": len(arows),
        "analyses_by_classification": dict(Counter(a["classification"] for a in arows)),
        "analyses_by_topic": dict(Counter(t for a in arows for t in a["topics"])),
        "analyses_by_official_ref_status": dict(Counter(a["official_ref"]["status"] for a in arows)),
        "analyses_by_confidence": dict(Counter(a["confidence"] for a in arows)),
        "analyses_by_academic_year": dict(Counter(a["academic_year"] for a in arows)),
        "analyses_by_verification_status": dict(Counter(a["verification_status"] for a in arows)),
        "analyses_linking_conflict": sum(1 for a in arows if a["conflict_ids"]),
        "videos_referenced_by_analyses": len({a["video_id"] for a in arows}),
        "conflicts_total": len(crow),
        "conflicts_by_type": dict(Counter(c["type"] for c in crow)),
        "conflicts_by_resolution": dict(Counter(c["resolution"] for c in crow)),
        "videos_without_analysis_rows": uncovered,
        "cjk_stray_rows": stray,
        "errors": errors,
    }
    with io.open(os.path.join(DATA, "validation_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    out = []
    for key in (
        "videos_total", "videos_content_analyzed", "videos_metadata_only", "distinct_channels",
        "topics", "analyses_total", "videos_referenced_by_analyses", "conflicts_total",
        "analyses_linking_conflict", "videos_without_analysis_rows", "cjk_stray_rows", "errors",
    ):
        val = report[key]
        out.append("%s=%s" % (key, len(val) if isinstance(val, (list, dict)) and key.endswith("rows") or key == "errors" or key == "cjk_stray_rows" else json.dumps(val, ensure_ascii=False) if isinstance(val, dict) else val))
    for key in ("videos_by_tier", "videos_by_channel_kind", "analyses_by_classification",
                "analyses_by_topic", "analyses_by_official_ref_status", "analyses_by_confidence",
                "analyses_by_academic_year", "analyses_by_verification_status",
                "conflicts_by_type", "conflicts_by_resolution", "videos_with_chapters",
                "videos_with_desc_timestamps", "videos_with_caption_tracks_listed",
                "videos_with_caption_text", "distinct_presenters"):
        out.append("%s=%s" % (key, json.dumps(report[key], ensure_ascii=False, sort_keys=True) if isinstance(report[key], dict) else report[key]))
    text = "\n".join(out).encode("ascii", "replace").decode("ascii")
    sys.stdout.write(text + "\n")
    sys.stdout.write("VALIDATION_%s\n" % ("FAIL" if errors else "PASS"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
