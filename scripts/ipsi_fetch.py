#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ipsi_fetch — BuildIt AI 입시상담 DB 수집용 robots-존중 HTTP 페처 (공통 라이브러리).

설계 원칙 (작업지시 1·3단계 준수):
- robots.txt를 호스트별로 파싱·캐싱하고, 우리 UA에 대해 Disallow면 **요청 자체를 거부**한다(hard gate).
  로그인 우회·차단 우회 없음. 거부 사유를 메타데이터에 남긴다.
- 원문(raw)·메타데이터·구조화 데이터를 분리 저장한다.
  원문 재배포가 제한된 자료는 메타데이터 + 공식 링크만 남길 수 있도록 store_raw=False를 지원한다.
- 모든 페치에 출처 메타데이터(원문URL, 최종URL, http상태, content-type, 크기, sha256, 수집일시, UA, robots판정)를 기록한다.
- collection ≠ verification: 이 모듈은 '수집'만 한다. 검증상태는 항상 COLLECTED로 시작한다.

의존성: requests, beautifulsoup4 (로컬 확인됨). 표준 라이브러리 urllib.robotparser 사용.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
from urllib import robotparser
from urllib.parse import urlparse, urljoin

import requests

# --- 상수 -------------------------------------------------------------------
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) BuildItIpsiResearch/1.0 (+contact: buildit-study)"
)
DEFAULT_TIMEOUT = 30
DEFAULT_DELAY = 1.0  # 호스트별 요청 사이 최소 간격(초) — polite crawling

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.normpath(os.path.join(HERE, "..", "data"))
RAW_DIR = os.path.join(RESEARCH, "raw")
META_DIR = os.path.join(RESEARCH, "meta")

# 수집 상태(파이프라인 단계). 검증 승격은 사람/대조 단계에서만.
COLLECTED = "COLLECTED"


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data or b"").hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


@dataclass
class FetchResult:
    """한 번의 페치 결과 + 출처 메타데이터."""
    url: str
    ok: bool
    robots_allowed: bool
    http_status: Optional[int] = None
    final_url: Optional[str] = None
    content_type: Optional[str] = None
    size: int = 0
    sha256: Optional[str] = None
    raw_path: Optional[str] = None
    collected_at: str = field(default_factory=_now_iso)
    user_agent: str = USER_AGENT
    error: Optional[str] = None
    verification_status: str = COLLECTED
    # in-memory 본문(메타 JSON에는 직렬화하지 않음). raw 미저장 출처도 파싱 가능하게.
    body_text: Optional[str] = field(default=None, repr=False)

    def meta_dict(self) -> dict:
        d = asdict(self)
        d.pop("body_text", None)  # 원문 본문은 메타파일에 남기지 않는다(저작권·용량)
        return d


class RobotsGate:
    """호스트별 robots.txt 파싱·캐싱. 우리 UA 기준 allow/disallow 판정."""

    def __init__(self, session: requests.Session, timeout: int = DEFAULT_TIMEOUT):
        self._session = session
        self._timeout = timeout
        self._cache: dict[str, Optional[robotparser.RobotFileParser]] = {}
        self._robots_url_cache: dict[str, str] = {}

    def _robots_url(self, url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}/robots.txt"

    def _parser(self, url: str) -> Optional[robotparser.RobotFileParser]:
        rurl = self._robots_url(url)
        host = urlparse(url).netloc
        if host in self._cache:
            return self._cache[host]
        rp = robotparser.RobotFileParser()
        rp.set_url(rurl)
        try:
            resp = self._session.get(rurl, timeout=self._timeout, headers={"User-Agent": USER_AGENT})
            if resp.status_code == 200 and "text/plain" in (resp.headers.get("Content-Type", "") or ""):
                rp.parse(resp.text.splitlines())
            elif resp.status_code == 200:
                # robots.txt가 HTML(=없음/404페이지)로 오는 경우 → 규칙 없음으로 취급하지만 기록
                body = (resp.text or "")[:200].lower()
                if "<html" in body or "<!doctype" in body:
                    rp = None
                else:
                    rp.parse(resp.text.splitlines())
            else:
                # 404 등 → robots 없음 = 허용(단, 기록)
                rp = None
            self._robots_url_cache[host] = f"{rurl} -> HTTP {resp.status_code}"
        except Exception as e:  # 네트워크 실패 시 보수적으로 '판정불가'
            self._robots_url_cache[host] = f"{rurl} -> ERROR {e}"
            rp = None
        self._cache[host] = rp
        return rp

    def allowed(self, url: str) -> bool:
        rp = self._parser(url)
        if rp is None:
            return True  # robots 없음/판정불가 → 허용(기록은 남김)
        return rp.can_fetch(USER_AGENT, url)

    def note(self, url: str) -> str:
        host = urlparse(url).netloc
        self._parser(url)  # 캐시 확보
        return self._robots_url_cache.get(host, "")


class IpsiFetcher:
    """robots-존중 폴라이트 페처. 세션·호스트별 지연·raw/meta 저장을 담당."""

    def __init__(self, store_raw: bool = True, delay: float = DEFAULT_DELAY,
                 raw_dir: str = RAW_DIR, meta_dir: str = META_DIR):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT})
        self.gate = RobotsGate(self._session)
        self.store_raw = store_raw
        self.delay = delay
        self.raw_dir = raw_dir
        self.meta_dir = meta_dir
        self._last_host_time: dict[str, float] = {}
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.meta_dir, exist_ok=True)

    def _throttle(self, url: str) -> None:
        host = urlparse(url).netloc
        last = self._last_host_time.get(host)
        if last is not None:
            wait = self.delay - (time.time() - last)
            if wait > 0:
                time.sleep(wait)
        self._last_host_time[host] = time.time()

    def _raw_subdir(self, url: str) -> str:
        host = urlparse(url).netloc.replace(":", "_")
        d = os.path.join(self.raw_dir, host)
        os.makedirs(d, exist_ok=True)
        return d

    def fetch(self, url: str, *, store_raw: Optional[bool] = None,
              save_meta: bool = True, allow_redirects: bool = True) -> FetchResult:
        """robots gate 통과 시에만 GET. 결과는 항상 FetchResult로 반환(예외 대신 기록)."""
        # 1) robots hard gate
        if not self.gate.allowed(url):
            res = FetchResult(url=url, ok=False, robots_allowed=False,
                              error=f"robots.txt disallows our UA: {self.gate.note(url)}")
            if save_meta:
                self._write_meta(res)
            return res

        self._throttle(url)
        try:
            resp = self._session.get(url, timeout=DEFAULT_TIMEOUT, allow_redirects=allow_redirects)
        except Exception as e:
            res = FetchResult(url=url, ok=False, robots_allowed=True, error=f"request failed: {e}")
            if save_meta:
                self._write_meta(res)
            return res

        body = resp.content or b""
        digest = sha256_bytes(body)
        res = FetchResult(
            url=url,
            ok=resp.status_code == 200,
            robots_allowed=True,
            http_status=resp.status_code,
            final_url=str(resp.url),
            content_type=resp.headers.get("Content-Type"),
            size=len(body),
            sha256=digest,
            error=None if resp.status_code == 200 else f"HTTP {resp.status_code}",
        )

        # 텍스트성 응답이면 본문을 메모리에 보관(raw 미저장 출처도 파싱 가능)
        ct = (res.content_type or "").lower()
        if res.ok and ("html" in ct or "text" in ct or "json" in ct or "xml" in ct):
            enc = _encoding_from_ct(res.content_type)
            res.body_text = body.decode(enc, errors="replace")

        do_store = self.store_raw if store_raw is None else store_raw
        if do_store and res.ok:
            ext = self._guess_ext(res.final_url or url, res.content_type or "")
            raw_path = os.path.join(self._raw_subdir(url), f"{digest[:32]}{ext}")
            with open(raw_path, "wb") as f:
                f.write(body)
            res.raw_path = os.path.relpath(raw_path, RESEARCH).replace(os.sep, "/")

        if save_meta:
            self._write_meta(res)
        return res

    @staticmethod
    def _guess_ext(url: str, content_type: str) -> str:
        ct = (content_type or "").lower()
        if "pdf" in ct or url.lower().endswith(".pdf"):
            return ".pdf"
        if "json" in ct:
            return ".json"
        if "xml" in ct:
            return ".xml"
        if "html" in ct:
            return ".html"
        m = re.search(r"\.([a-z0-9]{2,5})(?:[?#]|$)", url.lower())
        return f".{m.group(1)}" if m else ".bin"

    def _write_meta(self, res: FetchResult) -> str:
        host = urlparse(res.url).netloc.replace(":", "_")
        d = os.path.join(self.meta_dir, host)
        os.makedirs(d, exist_ok=True)
        key = sha256_text(res.url)[:24]
        path = os.path.join(d, f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(res.meta_dict(), f, ensure_ascii=False, indent=2)
        return path

    def read_text(self, res: FetchResult, encoding: Optional[str] = None) -> Optional[str]:
        """저장된 raw를 텍스트로 읽어 반환한다(없으면 None)."""
        if not res.raw_path:
            return None
        path = os.path.join(RESEARCH, res.raw_path)
        if not os.path.exists(path):
            return None
        enc = encoding or _encoding_from_ct(res.content_type)
        with open(path, "rb") as f:
            return f.read().decode(enc, errors="replace")

    def text_of(self, res: FetchResult, encoding: Optional[str] = None) -> Optional[str]:
        """본문 텍스트: 메모리(body_text) 우선, 없으면 저장된 raw에서."""
        if res.body_text is not None:
            return res.body_text
        return self.read_text(res, encoding=encoding)


def _encoding_from_ct(content_type: Optional[str]) -> str:
    ct = (content_type or "").lower()
    m = re.search(r"charset=([\w-]+)", ct)
    if m:
        return m.group(1)
    return "utf-8"


def absolutize(base: str, href: str) -> str:
    return urljoin(base, href)


if __name__ == "__main__":
    # 스모크: robots gate 동작 확인 (adiga는 거부돼야 정상)
    f = IpsiFetcher(store_raw=False)
    for u in [
        "https://www.adiga.kr/uct/ces/archiveView.do?menuId=PCUCTCES1000&prtlBbsId=23626",
        "https://www.moe.go.kr/main.do?s=moe",
    ]:
        r = f.fetch(u, save_meta=False)
        print(f"[{'ALLOW' if r.robots_allowed else 'BLOCK'}] ok={r.ok} status={r.http_status} {u}")
        if r.error:
            print("   err:", r.error)
