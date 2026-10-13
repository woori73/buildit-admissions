#!/usr/bin/env python3
"""watch 페이지 HTML에서 보강 신호 추출: 章(chapter), 고정 댓글, 채널 구독자 표기.

자동 자막(timedtext)은 이 네트워크에서 200+빈 본문으로 차단되어 내용은
공개 章/설명문/키워드를 근거로 분석한다(검증 상태에 근거 유형 기록).
"""
import json, re, sys, time, urllib.request
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from yt_public_collect import fetch_html  # noqa: E402

RE_CHAPTER = re.compile(r'"chapterRenderer":\{"title":\{"simpleText":"(.*?)".{0,400}?"playerPositionMs":"(\d+)"')
RE_SUBS = re.compile(r'"subscriberCountText":\{"accessibility".{0,600}?"simpleText":"([^"]{2,30})"')
RE_COMMENT = re.compile(r'"commentEntityPayload":\{.*?"content":"(.*?)".*?"publishedTime":', re.S)


def clean(s):
    try:
        s = s.encode("utf-8", "ignore").decode("unicode_escape", "ignore").encode("latin-1", "ignore").decode("utf-8", "ignore")
    except Exception:
        pass
    return (s or "").replace("\\n", " ").replace("\r", " ").strip()


def grab(vid):
    html = fetch_html(vid)
    chs, seen = [], set()
    for m in RE_CHAPTER.finditer(html):
        sec = int(m.group(2)) // 1000
        if sec not in seen:
            seen.add(sec)
            chs.append({"sec": sec, "mmss": "%02d:%02d" % (sec // 60, sec % 60), "title": clean(m.group(1))})
    chs.sort(key=lambda c: c["sec"])
    subs = re.search(RE_SUBS, html)
    comments = [clean(c)[:280] for c in RE_COMMENT.findall(html)[:8]]
    return {"videoId": vid, "chapters": chs[:40],
            "subscriberText": clean(subs.group(1)) if subs else None,
            "top_comments": comments, "html_len": len(html)}


def main():
    ids = json.load(open(sys.argv[1], encoding="utf-8"))
    out = {}
    for vid in ids:
        try:
            out[vid] = grab(vid)
            print("ok", vid, len(out[vid]["chapters"]), out[vid]["subscriberText"], file=sys.stderr)
        except Exception as e:
            out[vid] = {"videoId": vid, "error": str(e)}
            print("ERR", vid, e, file=sys.stderr)
        time.sleep(0.7)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
