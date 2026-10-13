#!/usr/bin/env python3
"""watch 페이지 HTML 병렬 수집기: publishDate·설명문·章 타임스탬프·자막 가용성.

innertube `next` 응답에는 microformat이 비어 있어(실측) 공개 watch HTML의
ytInitialPlayerResponse를 단일 fetch로 파싱한다. timedtext(자동 자막)는 이 네트워크에서
200+빈 본문으로 응답 → 본문 전문은 저장하지 않고 메타·章·설명 타임스탬프만 수집한다.
"""
import json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
RE_PLAYER = re.compile(r"ytInitialPlayerResponse\s*=\s*(\{.+?\})\s*;\s*(?:var\s+\w+|</script>)", re.S)


def fetch(vid, attempts=2, timeout=20):
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request("https://www.youtube.com/watch?v=%s&hl=ko" % vid,
                                         headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9",
                                                  "Connection": "close"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(1.0 + i)
    raise last


def collect(vid):
    html = fetch(vid)
    p = json.loads(RE_PLAYER.search(html).group(1))
    mf = p.get("microformat", {}).get("playerMicroformatRenderer", {})
    vd = p.get("videoDetails", {})
    st = p.get("captions", {}).get("playerCaptionsTracklistRenderer", {})
    desc = (mf.get("description") or {}).get("simpleText", "")
    stamps = []
    for ln in desc.splitlines():
        m = re.match(r"\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*[).\-–]?\s*(\S.{1,90})$", ln)
        if m:
            h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
            if m.group(3):
                h, mi = int(m.group(1)), int(m.group(2))
            else:
                h, mi = 0, int(m.group(1))
            sec = h * 3600 + mi * 60 + s
            stamps.append({"sec": sec, "label": m.group(4).strip()})
    return {
        "videoId": vid,
        "publishDate": (mf.get("publishDate") or "")[:10],
        "uploadDate": (mf.get("uploadDate") or "")[:10],
        "description": desc[:2500],
        "description_len": len(desc),
        "desc_timestamps": stamps[:40],
        "category": mf.get("category"),
        "allowRatings": mf.get("allowRatings"),
        "isUnlisted": mf.get("isUnlisted"),
        "caption_langs": [t.get("languageCode") for t in st.get("captionTracks", [])],
        "caption_kinds": [t.get("kind") or "manual" for t in st.get("captionTracks", [])],
        "durationSec": int(vd.get("lengthSeconds") or 0),
        "viewCount": vd.get("viewCount"),
    }


def main():
    ids = json.load(open(sys.argv[1], encoding="utf-8"))
    out_path = sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    res = {}
    try:
        res = json.load(open(out_path, encoding="utf-8"))
    except Exception:
        pass
    todo = [v for v in ids if v not in res or res[v].get("error")]
    print("todo", len(todo), flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(collect, v): v for v in todo}
        done = 0
        for fut in list(futs):
            vid = futs[fut]
            try:
                res[vid] = fut.result()
                done += 1
                if done % 10 == 0:
                    print("progress", done, len(todo), flush=True)
                    with open(out_path, "w", encoding="utf-8") as fh:
                        json.dump(res, fh, ensure_ascii=False, indent=1)
            except Exception as e:
                res[vid] = {"videoId": vid, "error": "%s: %s" % (type(e).__name__, e)}
                print("ERR", vid, res[vid]["error"], flush=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print("wrote", len(res), flush=True)


if __name__ == "__main__":
    main()
