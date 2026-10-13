#!/usr/bin/env python3
"""허용된 YouTube 공개 페이지 기반 수집기 (watch HTML → ytInitialPlayerResponse).

서브커맨드
  meta <ids.json> <out.json>     공개 watch 페이지에서 메타데이터·章·자막 가용성 수집
  transcript <videoId> <out.txt> 자동/수동 자막을 **분석용 로컬 캐시**로만 저장.
                                 원문 전문은 git에 커밋하지 않는다(저장소 정책: 재배포 금지).

notes
  - youtubei/v1/player 직접 호출은 이 네트워크에서 UNPLAYABLE(봇 판정) → 공개 watch 페이지 HTML 사용.
  - baseUrl에 access_token이 포함되므로 저장 시 토큰을 제거하고, 필요 시 재요청으로 갱신한다.
"""
import json, re, sys, time, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
RE_PLAYER = re.compile(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;\s*(?:var\s+\w+|</script>)", re.S)
RE_TITLE = re.compile(r'<meta name="title" content="([^"]*)"')
RE_CHANNEL = re.compile(r'"channelMetadataRenderer":\{"title":"([^"]*)"')


def fetch_html(vid, attempts=3):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request("https://www.youtube.com/watch?v=" + vid + "&hl=ko",
                                         headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9",
                                                  "Connection": "close"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:  # 일시적 연결 끊김은 재시도, 지속 실패는 호출자로 전파
            last = e
            time.sleep(2 + 3 * i)
    raise last


def player_of(vid):
    return json.loads(RE_PLAYER.search(fetch_html(vid)).group(1))


def strip_token(url):
    return re.sub(r"access_token=[^&]+", "access_token=REDACTED", url or "")


def parse_len(s):
    p = [int(x) for x in (s or "0").split(":")]
    while len(p) < 3:
        p = [0] + p
    return p[0] * 3600 + p[1] * 60 + p[2]


def meta(vid):
    p = player_of(vid)
    vd = p.get("videoDetails", {})
    mf = p.get("microformat", {}).get("playerMicroformatRenderer", {})
    st = p.get("captions", {}).get("playerCaptionsTracklistRenderer", {})
    tracks = []
    for t in st.get("captionTracks", []):
        tracks.append({
            "lang": t.get("languageCode"),
            "kind": t.get("kind") or "manual",
            "name": (t.get("name") or {}).get("simpleText")
                    or "".join(r.get("text", "") for r in (t.get("name") or {}).get("runs", [])),
            "url_redacted": strip_token(t.get("baseUrl")),
        })
    return {
        "videoId": vid,
        "title": vd.get("title"),
        "channel": vd.get("author"),
        "channelId": vd.get("channelId"),
        "durationSec": int(vd.get("lengthSeconds") or 0),
        "viewCount": vd.get("viewCount"),
        "publishDate": (mf.get("publishDate") or "")[:10],
        "uploadDate": (mf.get("uploadDate") or "")[:10],
        "description": (mf.get("description") or {}).get("simpleText", ""),
        "keywords": vd.get("keywords", []),
        "isLive": vd.get("isLiveContent", False),
        "category": mf.get("category"),
        "captionTracks": tracks,
        "playability": p.get("playabilityStatus", {}).get("status"),
    }


def chapters_from_html(vid):
    """章은 player 응답에 없는 경우가 많아 watch HTML의 engaged chapter 리스트에서 추출."""
    html = fetch_html(vid)
    out = []
    for m in re.finditer(r'"chapterRenderer":\{"title":\{"simpleText":"(.*?)".*?"playerPositionMs":"(\d+)"', html):
        out.append({"title": m.group(1), "sec": int(m.group(2)) // 1000})
    ded = {}
    for c in out:
        ded.setdefault(c["sec"], c["title"])
    return [{"title": t, "sec": s, "mmss": "%d:%02d" % (s // 60, s % 60)} for s, t in sorted(ded.items())]


def ts_chapters(vid):
    """설명문의 00:00 형식 타임스탬프를 파싱(章이 없을 때의 대안)."""
    m = meta(vid)
    lines = []
    for ln in (m["description"] or "").splitlines():
        g = re.match(r"\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*[.)\]]?\s+(.{2,90})", ln)
        if g:
            h, mi, s = int(g.group(3) or 0), int(g.group(2)), 0
            lines.append({"sec": h * 3600 + mi * 60, "mmss": ln.strip()[:90]})
    return lines


def transcript(vid, out_path, lang="ko"):
    p = player_of(vid)
    tracks = (p.get("captions", {}).get("playerCaptionsTracklistRenderer", {}) or {}).get("captionTracks", [])
    if not tracks:
        raise SystemExit("no captions for " + vid)
    pick = None
    for t in tracks:
        if t.get("languageCode") == lang:
            pick = t
            break
    pick = pick or tracks[0]
    url = pick["baseUrl"]
    if "fmt=" not in url:
        url += "&fmt=json3"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = json.loads(urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore"))
    cues = []
    for ev in data.get("events", []):
        tseg = ev.get("segs") or []
        txt = "".join(s.get("utf8", "") for s in tseg).strip()
        if txt:
            cues.append({"start_sec": round(ev.get("tStartMs", 0) / 1000), "text": txt.replace("\n", " ")})
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"videoId": vid, "lang": pick.get("languageCode"), "kind": pick.get("kind"),
                   "cue_count": len(cues), "cues": cues}, f, ensure_ascii=False, indent=1)
    return len(cues)


def main():
    cmd = sys.argv[1]
    if cmd == "meta":
        ids = json.load(open(sys.argv[2], encoding="utf-8"))
        out_path = sys.argv[3]
        try:
            res = json.load(open(out_path, encoding="utf-8"))
        except Exception:
            res = {}
        for vid in ids:
            if vid in res and not res[vid].get("error"):
                continue
            try:
                m = meta(vid)
                m["chapters"] = chapters_from_html(vid)
                res[vid] = m
                print("ok", vid, m["publishDate"], m["durationSec"], len(m["captionTracks"]), len(m["chapters"]), flush=True)
            except Exception as e:
                res[vid] = {"videoId": vid, "error": "%s: %s" % (type(e).__name__, e)}
                print("ERR", vid, res[vid]["error"], flush=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=1)
            time.sleep(0.8)
    elif cmd == "chapters":
        ids = json.load(open(sys.argv[2], encoding="utf-8"))
        out = {}
        for vid in ids:
            try:
                out[vid] = chapters_from_html(vid) or ts_chapters(vid)
            except Exception as e:
                out[vid] = {"error": str(e)}
            time.sleep(0.6)
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    elif cmd == "transcript":
        n = transcript(sys.argv[2], sys.argv[3])
        print("cues", n, file=sys.stderr)
    else:
        raise SystemExit("usage: yt_public_collect.py {meta|chapters|transcript} ...")


if __name__ == "__main__":
    main()
