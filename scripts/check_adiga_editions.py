"""2027 모집요강 판(edition) 대조: adiga.kr 게시본으로 만든 구조화 값이 입학처 게시본에도 그대로 있는지 확인한다.

데이터는 바꾸지 않는다. 결과는 data/validation/adiga_edition_check_2027.json 에 쓴다.

대상: data/parsed/univ_sample/*.json 중 원문 링크가 adiga.kr 인 문서 가운데, 같은 대학·같은 모집(수시/정시)의
입학처 게시본을 수능최저(data/parsed/susi_minimum) 또는 정시 계산식(data/parsed/jeongsi_formula) 작업에서 이미 받아 둔 것.
입학처 파일은 data/meta 의 sha256 으로 data/raw 원문을 찾는다(원문은 git 미저장, 로컬에만 있음).

검사(값이 입학처판 글자 층에 있는지)
- 전형: 전형명(또는 그 구성 단어)이 있는가, 모집인원이 그 이름이 나오는 쪽에 있는가.
  전형 모집인원이 그 전형 학과별 인원의 합이면(원문에 합계가 따로 없는 경우) 학과 인원 검사로 갈음한다.
- 학과: 학과명(또는 구성 단어)이 있는가, 학과별 전형 인원이 그 학과가 나오는 쪽에 있는가(인문·자연으로 나뉜 두 수의 합 포함).
- 일정: 날짜(월.일)와 시각이 문서 어딘가에 있는가.
남은 '후보'는 사람이 쪽을 직접 보고 판정한다(docs/ADIGA_EDITION_CHECK_2027.md).

실행: python3 scripts/check_adiga_editions.py
"""
import collections
import glob
import hashlib
import itertools
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "validation", "adiga_edition_check_2027.json")

_STRIP = re.compile(r"[\s·ㆍ•∙\-–—_,/()\[\]{}「」『』<>〈〉\"'’‘“”:;~]+")
_MARKS = re.compile(r"[★☆◆◇※*†‡#○●♣]+")
_DATE = re.compile(r"(?<!\d)(\d{1,2})\s*[.월]\s*(\d{1,2})\s*[.일]?(?!\d)")
_TIME = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
_NUM = re.compile(r"(?<![\d.])(\d{1,4})(?![\d.])")
_SKIP_WORDS = {"자연", "인문", "정원외", "정원내"}


def norm(s):
    """공백·문장부호를 지워 줄바꿈·띄어쓰기 차이를 없앤다."""
    return _STRIP.sub("", (s or "").replace(" ", " "))


def strip_marks(s):
    return _MARKS.sub("", s or "").strip()


def name_parts(name):
    """'정시 일반전형 수능위주(가군)' -> 비교에 쓸 구성 단어들(정규화). 모집군·정원 표기는 뺀다."""
    n = re.sub(r"^(정시|수시)\s*", "", strip_marks(name))
    n = re.sub(r"\((가|나|다)군\)", "", n)
    parts = [norm(p) for p in re.split(r"[()\s_/·\-\[\]]+", n)]
    return [p for p in parts if len(p) >= 2 and p not in _SKIP_WORDS]


def name_found(name, normalized_text):
    whole = norm(strip_marks(name))
    if whole and whole in normalized_text:
        return True
    parts = name_parts(name)
    return bool(parts) and all(p in normalized_text for p in parts)


def numbers(s):
    return {int(x) for x in _NUM.findall(s or "")}


def date_tokens(s):
    out = set()
    for m, d in _DATE.findall(s or ""):
        m, d = int(m), int(d)
        if 1 <= m <= 12 and 1 <= d <= 31:
            out.add((m, d))
    return out


def time_tokens(s):
    return {(int(h), int(mi)) for h, mi in _TIME.findall(s or "")}


def _pages_with(name, npages):
    keys = [norm(strip_marks(name))] + name_parts(name)
    keys = [k for k in keys if k]
    return [i for i, p in enumerate(npages) if any(k in p for k in keys)]


def check_parsed_against_pages(parsed, pages):
    """parsed(univ_sample 구조화 파일)의 값이 pages(입학처판 쪽별 글자)에 있는지 본다. 후보 목록을 돌려준다."""
    npages = [norm(p) for p in pages]
    nall = "".join(npages)
    all_dates = date_tokens("\n".join(pages))
    all_times = time_tokens("\n".join(pages))
    stats = collections.Counter()
    cands = collections.defaultdict(list)

    dept_ok_by_type = collections.defaultdict(lambda: True)
    dept_sum_by_type = collections.Counter()
    for dep in parsed.get("departments") or []:
        name = strip_marks(dep.get("department") or "")
        stats["학과"] += 1
        if not name:
            continue
        if not name_found(name, nall):
            cands["학과명"].append({"학과": name})
            for t in dep.get("counts_by_type") or {}:
                dept_ok_by_type[t] = False
            continue
        hit = _pages_with(name, npages)
        ev = [p - 1 for p in (dep.get("evidence_pages") or []) if 0 < p <= len(pages)]
        nums = set()
        lines_nums = []
        core = norm(re.sub(r"\(.*?\)", "", name)) or norm(name)
        for i in sorted(set(hit) | set(ev)):
            nums |= numbers(pages[i])
            lines = pages[i].split("\n")
            for li, line in enumerate(lines):
                if core and core in norm(line):
                    lines_nums += [int(v) for v in _NUM.findall(" ".join(lines[li:li + 3]))]
        for tname, c in (dep.get("counts_by_type") or {}).items():
            if not isinstance(c, int) or c == 0:
                continue
            stats["학과별 인원"] += 1
            dept_sum_by_type[tname] += c
            if c in nums or any(a + b == c for a, b in itertools.combinations(lines_nums, 2)):
                continue
            dept_ok_by_type[tname] = False
            cands["학과별 인원"].append({"학과": name, "전형": tname, "값": c, "근거쪽(adiga판)": dep.get("evidence_pages")})

    group_sum = collections.Counter()
    for t in parsed.get("admission_types") or []:
        if isinstance(t.get("recruitment_count"), int):
            group_sum[re.sub(r"\((가|나|다)군\)", "", t["name"]).strip()] += t["recruitment_count"]
    for t in parsed.get("admission_types") or []:
        name = t.get("name") or ""
        stats["전형"] += 1
        if not name_found(name, nall):
            cands["전형명"].append({"전형": name})
            continue
        c = t.get("recruitment_count")
        if not isinstance(c, int) or c == 0:
            continue
        stats["전형 인원"] += 1
        hit = _pages_with(name, npages)
        if any(c in numbers(pages[i]) for i in hit):
            continue
        gsum = group_sum.get(re.sub(r"\((가|나|다)군\)", "", name).strip())
        if gsum and gsum != c and gsum in numbers("\n".join(pages)):
            continue  # 군별로 나눈 값의 합이 원문 합계와 같음
        if dept_sum_by_type.get(name) == c and dept_ok_by_type[name]:
            continue  # 원문에 전형 합계 없음 — 학과별 인원이 모두 확인됨
        cands["전형 인원"].append({"전형": name, "값": c})

    for sc in parsed.get("schedules") or []:
        stats["일정"] += 1
        miss_d = sorted(x for x in date_tokens(sc.get("date")) if x not in all_dates)
        miss_t = sorted(x for x in time_tokens(sc.get("date")) if x not in all_times)
        if miss_d or miss_t:
            cands["일정"].append({"항목": sc.get("item"), "전형": sc.get("type_name"), "일정": sc.get("date"),
                                "없는 날짜": miss_d, "없는 시각": miss_t})
    return dict(stats), {k: v for k, v in cands.items()}


# ---------- 파일 찾기·글자 추출 (로컬 원문 필요) ----------

def _sha_to_raw():
    out = {}
    for f in glob.glob(os.path.join(ROOT, "data", "meta", "**", "*.json"), recursive=True):
        try:
            m = json.load(open(f))
        except Exception:
            continue
        if isinstance(m, dict) and m.get("ok") and m.get("sha256") and m.get("raw_path"):
            out[m["sha256"]] = os.path.join(ROOT, "data", m["raw_path"])
    return out


def find_pairs():
    sha2raw = _sha_to_raw()
    official = collections.defaultdict(list)
    for pat, rnd in (("susi_minimum", "susi"), ("jeongsi_formula", "jeongsi")):
        for f in glob.glob(os.path.join(ROOT, "data", "parsed", pat, "*.json")):
            d = json.load(open(f))
            for doc in d.get("documents") or []:
                if doc.get("file_url") and "adiga.kr" not in doc["file_url"]:
                    official[(d["university_key"], rnd)].append(doc)
    pairs = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "parsed", "univ_sample", "*.json"))):
        d = json.load(open(f))
        s = d.get("document") or {}
        if "adiga.kr" not in (s.get("file_url") or ""):
            continue
        b = os.path.basename(f)
        key = b.split("_2027")[0].split("_2028")[0]
        rnd = "jeongsi" if "jeongsi" in b else "susi"
        for o in official.get((key, rnd), []):
            pairs.append({"key": key, "round": rnd, "parsed": os.path.relpath(f, ROOT), "adiga_document": s.get("document_name"),
                          "official_document": o.get("document_name"), "official_file_url": o.get("file_url"),
                          "official_source_page_url": o.get("source_page_url"), "official_sha256": o.get("file_sha256"),
                          "raw": sha2raw.get(o.get("file_sha256"))})
    return pairs


def extract_pages(path):
    """쪽별 글자. pymupdf → 한글이 없으면 pdftotext. HWP·글자 층 없음은 None과 사유."""
    head = open(path, "rb").read(8)
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return None, "HWP 파일(배포용 문서) — 보호를 풀어 읽지 않음"
    import pymupdf
    pages = [p.get_text() for p in pymupdf.open(path)]
    if sum(len(re.findall("[가-힣]", t)) for t in pages) > 0:
        return pages, None
    txt = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout
    pages = txt.split("\f")
    if sum(len(re.findall("[가-힣]", t)) for t in pages) > 0:
        return pages, None
    return None, "글자 층 없음 — 쪽 이미지로 확인"


def main():
    results = []
    for p in find_pairs():
        row = {k: p[k] for k in ("key", "round", "parsed", "adiga_document", "official_document", "official_file_url",
                                 "official_source_page_url", "official_sha256")}
        if "재외국민" in (p["official_document"] or "") and "재외국민" not in (p["adiga_document"] or ""):
            row["skipped"] = "다른 문서(재외국민·외국인 전형 전용 요강) — 같은 판 비교 대상 아님"
        elif not p["raw"] or not os.path.exists(p["raw"]):
            row["skipped"] = "입학처 원문 파일이 로컬에 없음"
        else:
            pages, why = extract_pages(p["raw"])
            row["official_pages"] = len(pages) if pages else None
            if pages is None:
                row["skipped"] = why
            else:
                stats, cands = check_parsed_against_pages(json.load(open(os.path.join(ROOT, p["parsed"]))), pages)
                row["checked"] = stats
                row["candidates"] = cands
        results.append(row)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"schema": "adiga_edition_check/v1", "academic_year": 2027, "pairs": results}, open(OUT, "w"),
              ensure_ascii=False, indent=1)
    for r in results:
        if "skipped" in r:
            print(r["key"], r["round"], "SKIP", r["skipped"])
        else:
            print(r["key"], r["round"], r["checked"], {k: len(v) for k, v in r["candidates"].items()})


if __name__ == "__main__":
    main()
