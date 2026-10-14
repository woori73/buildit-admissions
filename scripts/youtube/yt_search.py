#!/usr/bin/env python3
"""YouTube 입시분석 영상 후보 발굴기 (innertube search / WEB 클라이언트).

- 요청 대상: www.youtube.com/youtubei/v1/search (YouTube 웹 클라이언트의 공개 key)
- 저장: videoId, 제목, 채널, 게시일 텍스트, 길이, 조회수 표기, 썸네일, description 일부
- 원문 전문(자막)은 이 스크립트에서 저장하지 않는다(분석용 임시 캐시만, gitignore).
"""
import json, os, sys, time, urllib.request

KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not KEY:
    print("ERROR: YOUTUBE_API_KEY 환경변수가 설정되지 않았습니다.", file=sys.stderr)
    print("  .env 파일 또는 환경변수로 YOUTUBE_API_KEY를 설정하세요.", file=sys.stderr)
    sys.exit(1)
EP = "https://www.youtube.com/youtubei/v1/search?key=" + KEY
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def search(query, token=None):
    body = {
        "context": {"client": {"clientName": "WEB", "clientVersion": "2.20250101.00.00", "hl": "ko", "gl": "KR"}},
        "query": query,
    }
    if token:
        body["continuation"] = token
    req = urllib.request.Request(
        EP,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": UA,
                 "Origin": "https://www.youtube.com", "Referer": "https://www.youtube.com/"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def walk(node, out):
    if isinstance(node, dict):
        if node.get("videoRenderer"):
            out.append(node["videoRenderer"])
        for v in node.values():
            walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)


def text_of(runs_or_simple):
    if not runs_or_simple:
        return ""
    if "simpleText" in runs_or_simple:
        return runs_or_simple["simpleText"]
    return "".join(r.get("text", "") for r in runs_or_simple.get("runs", []))


def flat(vr):
    ch = vr.get("ownerText") or vr.get("longBylineText") or {}
    subs = []
    for b in (vr.get("detailedMetadataSnippets") or []):
        subs.append(text_of(b.get("snippetText")))
    return {
        "videoId": vr.get("videoId"),
        "title": text_of(vr.get("title")),
        "channel": text_of(ch),
        "publishedText": text_of(vr.get("publishedTimeText")),
        "lengthText": text_of(vr.get("lengthText")),
        "viewCountText": text_of(vr.get("viewCountText")),
        "description_snippet": " ".join(subs)[:400],
        "badges": [b.get("metadataBadgeRenderer", {}).get("style", "") for b in (vr.get("badges") or [])],
        "url": "https://www.youtube.com/watch?v=" + str(vr.get("videoId")),
    }


def main():
    queries = json.load(open(sys.argv[1], encoding="utf-8"))
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    found = {}
    for q in queries:
        token, n = None, 0
        while n < pages:
            try:
                data = search(q, token)
            except Exception as e:
                print("ERR", q, e, file=sys.stderr)
                break
            vids = []
            walk(data.get("contents") or data, vids)
            for vr in vids:
                f = flat(vr)
                if f["videoId"] and f["videoId"] not in found:
                    f["query"] = q
                    found[f["videoId"]] = f
            conts = []
            walk(data.get("continuationContents") or {}, conts)
            token = None
            for k in ("searchContinuationItemRenderer",):
                pass
            cc = (data.get("continuationItems") or None)
            token = find_token(data)
            n += 1
            if not token:
                break
            time.sleep(0.6)
        print("done", q, len(found), file=sys.stderr)
    out = list(found.values())
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote", len(out), "videos ->", sys.argv[3], file=sys.stderr)
    else:
        sys.stdout.buffer.write(text.encode("utf-8"))


def find_token(obj):
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            if cur.get("token") and "continuationCommand" in json.dumps(list(cur.keys())[:1]):
                pass
            if "continuationEndpoint" in cur:
                tok = cur.get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
                if tok:
                    return tok
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


if __name__ == "__main__":
    main()
