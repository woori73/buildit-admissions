#!/usr/bin/env python3
"""선정 영상의 상세 메타데이터 수집기.

- youtubei/v1/player (WEB client) → basic details + captionTracks 가용 여부
- youtubei/v1/next → 채ptrater/description, publisher 서브텍스트(구독자 표기), likes
- 자막 원문은 저장하지 않고, tracks 가용 여부·언어·자동/수동 여부만 메타로 남긴다.
"""
import json, os, sys, time, urllib.request

KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not KEY:
    print("ERROR: YOUTUBE_API_KEY 환경변수가 설정되지 않았습니다.", file=sys.stderr)
    print("  .env 파일 또는 환경변수로 YOUTUBE_API_KEY를 설정하세요.", file=sys.stderr)
    sys.exit(1)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def call(ep, vid):
    body = {
        "context": {"client": {"clientName": "WEB", "clientVersion": "2.20250101.00.00", "hl": "ko", "gl": "KR"}},
        "videoId": vid,
    }
    req = urllib.request.Request(
        "https://www.youtube.com/youtubei/v1/" + ep + "?key=" + KEY,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA,
                 "Origin": "https://www.youtube.com", "Referer": "https://www.youtube.com/watch?v=" + vid},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def deep(node, key, out):
    if isinstance(node, dict):
        if key in node:
            out.append(node[key])
        for v in node.values():
            deep(v, key, out)
    elif isinstance(node, list):
        for v in node:
            deep(v, key, out)
    return out


def main():
    ids = json.load(open(sys.argv[1], encoding="utf-8"))
    res = {}
    for vid in ids:
        rec = {"videoId": vid}
        try:
            p = call("player", vid)
            vd = p.get("videoDetails", {})
            rec.update({
                "title": vd.get("title"),
                "channel": vd.get("author"),
                "channelId": vd.get("channelId"),
                "durationSec": int(vd.get("lengthSeconds") or 0),
                "viewCount": vd.get("viewCount"),
                "keywords": vd.get("keywords", []),
                "isLive": vd.get("isLiveContent", False),
            })
            st = p.get("captions", {}).get("playerCaptionsTracklistRenderer", {})
            rec["captionTracks"] = [
                {"lang": t.get("languageCode"), "kind": t.get("kind"), "name": (t.get("name") or {}).get("simpleText")
                 or "".join(r.get("text", "") for r in (t.get("name") or {}).get("runs", []))}
                for t in st.get("captionTracks", [])
            ]
            rec["autoTranslations"] = bool(st.get("translationLanguages"))
        except Exception as e:
            rec["player_error"] = str(e)
        try:
            n = call("next", vid)
            micro = deep(n.get("microformat", {}), "playerMicroformatRenderer", [])[0] if deep(n.get("microformat", {}), "playerMicroformatRenderer", []) else {}
            if micro:
                rec["publishDate"] = micro.get("publishDate")
                rec["uploadDate"] = micro.get("uploadDate")
                rec["description"] = ((micro.get("description") or {}).get("simpleText") or "")[:3000]
                rec["channelUrl"] = micro.get("channelUrl")
                rec["isFamilySafe"] = micro.get("isFamilySafe")
            rows = deep(n, "videoDescriptionHeaderRenderer", [])
            if rows:
                r0 = rows[0]
                txt = lambda x: (x or {}).get("simpleText") or "".join(i.get("text", "") for i in (x or {}).get("runs", []))
                rec["subscriberText"] = txt(r0.get("subscriberCountText"))
                rec["viewCountText"] = txt(r0.get("viewCountText"))
                rec["publishText"] = txt(r0.get("publishDateText") or r0.get("publishDate"))
            chaps = deep(n, "chapterRenderer", [])
            rec["chapters"] = [{"title": (c.get("title") or {}).get("simpleText") or "",
                                "time": c.get("timeDescription", {}).get("simpleText")} for c in chaps][:40]
        except Exception as e:
            rec["next_error"] = str(e)
        res[vid] = rec
        print("ok", vid, rec.get("publishDate"), rec.get("durationSec"), len(rec.get("captionTracks") or []), file=sys.stderr)
        time.sleep(0.4)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
