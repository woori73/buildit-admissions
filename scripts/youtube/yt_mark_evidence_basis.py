#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analyses.json 항목에 근거 수준(evidence_basis)을 명시하고, 근거 수준과 맞지 않는
확실성 라벨을 소거한다. 추가 수집·재분석 없이 이미 저장된 필드만 결정적으로 파생한다.

근거 수준은 anchor.src(앵커가 나온 층위)와 해당 영상의 content_evidence(무엇을 확보했는지)로 결정된다.
자막(timedtext)을 확보한 영상이 없으므로 speech_verified는 전체 false다.

usage: python scripts/youtube/yt_mark_evidence_basis.py [--dry-run] [--out FILE]
"""
import argparse
import io
import json
import os
import re
import sys

BASIS_DEFS = {
    "AS_PUBLISHED_TEXT": "채널이 설명란 등에 공개한 텍스트 자체를 근거로 삼은 항목(발언 청취가 아니라 공개 문언 기준).",
    "INFERRED_FROM_TIMELINE_LABEL": "설명란 타임스탬프(챕터) 라벨이 해당 구간의 존재를 가리키므로, 그 라벨 어휘로 주장을 복원한 항목. 실제 발화 내용은 미청취.",
    "INFERRED_FROM_CHAPTER_LABEL": "YouTube 챕터 제목 라벨만 근거로 한 항목. 실제 발화 내용은 미청취.",
    "INFERRED_FROM_DESCRIPTION_SUMMARY": "채널이 제공한 설명란 요약문·해시태그를 근거로 한 항목. 실제 발화 내용은 미청취.",
    "INFERRED_FROM_METADATA": "제목·채널·게시일 등 메타데이터와 영상 단위 개요로 복원한 항목. 실제 발화 내용은 미청취.",
}
INFERRED = {k for k in BASIS_DEFS if k.startswith("INFERRED_")}

# 영상 설명란에 실제로 적혀 있던 공식 링크 (work/watch_meta.json에서 채취한 값만 사용, 추측 URL 금지)
DESCRIPTION_OFFICIAL_LINKS = {
    "YT-A077": [
        "https://iphak.khu.ac.kr/detail.do?menuurl=wvOt10B5et6zMa%2FM59G%2BxQ%3D%3D&board_seq=16401&pageNo=1&categoryid=0&userpwd=",
        "https://admission.sookmyung.ac.kr/upload/info/20250724162837CGJKFQ.PDF",
    ],
}

PENDING_DOC = re.compile(
    r"원문 URL 미확보|원문 대조|문서 대조 전|개별 대학 원문|대학 공지 원문|확인 필요|확인 가능한 방향|시행계획에서 확인|통계로 확인|1차 자료로 확인"
)


def basis_of(item, video):
    src = item["anchor"].get("src")
    if src == "description_transcript":
        return "AS_PUBLISHED_TEXT"
    if src == "desc_timestamp":
        return "INFERRED_FROM_TIMELINE_LABEL"
    ev = video.get("content_evidence") or ""
    if "description" in ev:
        return "INFERRED_FROM_DESCRIPTION_SUMMARY"
    if "chapters" in ev:
        return "INFERRED_FROM_CHAPTER_LABEL"
    return "INFERRED_FROM_METADATA"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analyses", default="data/youtube/analyses.json")
    ap.add_argument("--videos", default="data/youtube/videos.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="", help="UTF-8 변경 보고서 파일(생략 시 ASCII 요약만 stdout)")
    args = ap.parse_args()

    doc = json.load(open(args.analyses, encoding="utf-8"))
    vdoc = json.load(open(args.videos, encoding="utf-8"))
    vids = {v["video_id"]: v for v in vdoc["videos"]}
    items = doc["analyses"]

    log = []
    capped, reclassified, linked, reworded, moved = [], [], [], [], []
    for a in items:
        v = vids[a["video_id"]]
        b = basis_of(a, v)
        a["evidence_basis"] = b
        a["speech_verified"] = bool(v.get("caption_available"))
        if b in INFERRED and a["confidence"] == "HIGH":
            a["confidence"] = "MEDIUM"
            a["confidence_capped"] = True
            capped.append(a["id"])
            log.append("%s: confidence HIGH->MEDIUM (%s)" % (a["id"], b))
        elif a.get("confidence_capped") and not (b in INFERRED and a["confidence"] == "MEDIUM"):
            a.pop("confidence_capped", None)
        ref = a["official_ref"]
        # url 필드는 실제 URL만 보관한다. 자료명 서술은 note로 옮긴다(필드 의미 고정).
        u = ref.get("url") or ""
        if u and not u.startswith("http"):
            ref["url"] = ""
            marker = "대조 대상 자료(URL 미확보): " + u
            if marker not in (ref.get("note") or ""):
                ref["note"] = (marker + " | " + (ref.get("note") or "")).strip(" |")
            moved.append(a["id"])
            log.append("%s: url field descriptor -> note" % a["id"])
        has_url = (ref.get("url") or "").startswith("http")
        if ref["status"] == "CONSISTENT_WITH_OFFICIAL" and not has_url:
            ref["status"] = "NEEDS_OFFICIAL_DOC"
            marker = "[공식 원문 URL 미확보"
            if marker not in (ref.get("note") or ""):
                ref["note"] = (ref.get("note") or "") + " " + marker + " — 대조 완료로 오독되지 않도록 NEEDS_OFFICIAL_DOC으로 강등]"
            reclassified.append(a["id"])
            log.append("%s: official_ref CONSISTENT_WITH_OFFICIAL->NEEDS_OFFICIAL_DOC" % a["id"])
        if not has_url and a["id"] in DESCRIPTION_OFFICIAL_LINKS:
            ref["url"] = DESCRIPTION_OFFICIAL_LINKS[a["id"]][0]
            marker = "[영상 설명란에 게시된 공식 링크"
            if marker not in (ref.get("note") or ""):
                ref["note"] = (ref.get("note") or "") + " " + marker + "을 채취해 원문 경로로 기록; 본문 대조는 미완료]"
            ref["status"] = "NEEDS_OFFICIAL_DOC" if ref["status"] == "UNSUPPORTED" else ref["status"]
            linked.append(a["id"])
            log.append("%s: official_ref.url <- description link" % a["id"])
        if b in INFERRED and re.search(r"발표자는 .*해설했다", a["claim"] or ""):
            a["claim"] = re.sub(
                r"발표자는 각 기준별 세부 평가 내용을 대학 공개 자료 순서대로 해설했다.",
                "장(챕터) 제목 순서가 대학 공개 자료의 평가 요소 체계와 일치하므로, 해당 순서로 해설이 구성되었을 것으로 추정된다(발음 내용 미청취).",
                a["claim"],
            )
            reworded.append(a["id"])
            log.append("%s: claim reworded away from asserted speech" % a["id"])

    doc["evidence_basis_definitions"] = BASIS_DEFS
    rules = doc.get("usage_rules") or []
    add = [
        "evidence_basis가 INFERRED_*인 항목은 전문가의 확정 발언으로 인용하지 말고 '채널이 공개한 설명란·챕터 라벨 기반 복원'임을 함께 표기한다(본 네트워크에서 자막 미확보).",
        "speech_verified=false인 항목은 발언 전체 내용을 영상에서 직접 확인하지 않은 것이므로, 수치·비율·문구 인용은 공식 1차 자료 확인 전에는 예시로만 사용한다.",
        "confidence는 근거 수준에 의해 상한된다 — AS_PUBLISHED_TEXT가 아닌 항목의 HIGH는 허용하지 않는다(confidence_capped=true에 기록).",
    ]
    for r in add:
        if r not in rules:
            rules.append(r)
    doc["usage_rules"] = rules

    report = {
        "items": len(items),
        "evidence_basis": {},
        "capped_confidence": capped,
        "reclassified_official_ref": reclassified,
        "attached_description_links": linked,
        "reworded_claims": reworded,
        "url_descriptors_moved_to_note": moved,
        "speech_verified_true": [a["id"] for a in items if a["speech_verified"]],
    }
    for a in items:
        k = a["evidence_basis"]
        report["evidence_basis"][k] = report["evidence_basis"].get(k, 0) + 1

    if args.out:
        with io.open(args.out, "w", encoding="utf-8") as f:
            f.write(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
            f.write("\n".join(log) + "\n")

    sys.stdout.buffer.write((
        "items=%d basis=%s capped=%d reclassified=%d linked=%d reworded=%d url_descriptors_moved=%d speech_verified=%d\n" % (
            len(items),
            " ".join("%s:%d" % (k[:22], c) for k, c in sorted(report["evidence_basis"].items())),
            len(capped), len(reclassified), len(linked), len(reworded), len(moved),
            len(report["speech_verified_true"]))
    ).encode("utf-8"))
    if args.dry_run:
        sys.stdout.buffer.write(b"DRY_RUN (no write)\n")
        return
    tmp = args.analyses + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, args.analyses)
    sys.stdout.buffer.write(("wrote %s\n" % args.analyses).encode("utf-8"))


if __name__ == "__main__":
    main()
