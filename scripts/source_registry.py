#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
source_registry — BuildIt AI 입시상담 DB의 **공식 출처 목록(canonical source registry)**.

이 파일이 출처의 단일 정본이다. discover_docs.py·build_ipsi_seed.py가 이 목록을 읽고,
최종적으로 Spring `ipsi_sources` 테이블(V1064+)로 적재된다.

각 출처는 작업지시 요구 필드를 모두 가진다:
  기관명 / 유형 / 기본URL / robots판정 / 이용·재배포 조건 / 접근방식 /
  시드 게시판(크롤링 진입점) / 우선확보 문서 / 수집·검증 상태.

robots 판정은 2026-10-13 curl 실측 기준(아래 notes). 실제 수집 시 ipsi_fetch.RobotsGate가
요청마다 재검증하므로 이 값은 '사전 조사 결과'일 뿐 하드 코딩 우회에 쓰지 않는다.
"""
from __future__ import annotations

# institution_type: MINISTRY(부처) / COUNCIL(협의회) / AGENCY(평가원) / BROADCAST(방송/EBS) / UNIVERSITY
# access_method: HTTP_STATIC(curl로 본문 확보 가능) / JS_REQUIRED(브라우저 필요) / METADATA_ONLY(robots·저작권으로 링크만)
# redistribution: OPEN(재배포 허용) / METADATA_PRIORITY(원문 재배포 제한 → 메타+링크 우선) / RESTRICTED
# our_ua_allowed: 우리 UA(비허용 봇) 기준 robots 허용 여부 — False면 본문 자동수집 금지

SOURCES = [
    {
        "source_key": "adiga",
        "institution_name": "한국대학교육협의회 대입정보포털 '어디가'(adiga.kr)",
        "institution_type": "COUNCIL",
        "base_url": "https://www.adiga.kr/",
        "robots_our_ua_allowed": False,
        "robots_notes": (
            "robots.txt 끝부분 `User-agent: * / Disallow: /` → 비화이트리스트 봇 전면 차단. "
            "게다가 우선대상 URL `/uct/ces/archiveView.do`는 화이트리스트 봇에도 개별 Disallow. "
            "2026-10-13 curl 실측: archiveView.do robots gate BLOCK 확인."
        ),
        "reuse_terms": "자동수집 금지(robots). 개별 상세 View 페이지 다수 Disallow.",
        "redistribution": "METADATA_PRIORITY",
        "access_method": "METADATA_ONLY",
        "seed_boards": [],
        "priority_docs": [
            "대학별 전형 시행계획/입시결과 상세 (univView.do 등) — robots 차단으로 메타·링크만",
        ],
        "collect_status": "BLOCKED_BY_ROBOTS",
    },
    {
        "source_key": "kcue",
        "institution_name": "한국대학교육협의회(KCUE, 대교협)",
        "institution_type": "COUNCIL",
        "base_url": "https://www.kcue.or.kr/",
        "robots_our_ua_allowed": True,
        "robots_notes": "www.kcue.or.kr/robots.txt = 404(파일 없음) → 규칙 없음, 전방 허용. 2026-10-13 실측.",
        "reuse_terms": "공공저작물(협의회 공지·보도자료). 원문 재배포는 METADATA_PRIORITY로 보수적 처리.",
        "redistribution": "METADATA_PRIORITY",
        "access_method": "HTTP_STATIC",
        "seed_boards": [
            {"name": "보도자료", "url": "https://www.kcue.or.kr/news/sub02/sub01.php"},
            {"name": "공지사항", "url": "https://www.kcue.or.kr/notice/sub01.php"},
        ],
        "priority_docs": [
            "2028학년도 대학입학전형 시행계획 (발표·모음집)",
            "2027학년도 대학입학전형 시행계획",
        ],
        "collect_status": "PENDING",
    },
    {
        "source_key": "kcue_library",
        "institution_name": "한국대학교육협의회 고등교육정보자료실(library.kcue.or.kr)",
        "institution_type": "COUNCIL",
        "base_url": "https://library.kcue.or.kr/",
        "robots_our_ua_allowed": True,
        "robots_notes": "robots.txt 없음(404 HTML) → 전방 허용. 루트는 /subhomepage1/usmn000.jsp로 JS 리다이렉트. 2026-10-13 실측.",
        "reuse_terms": "자료실 목록(신규자료·통합검색)은 ajax/JS 로드 → 정적 HTML에는 nav만. 본문 목록은 브라우저 또는 검색 엔드포인트 필요.",
        "redistribution": "METADATA_PRIORITY",
        "access_method": "JS_REQUIRED",
        "seed_boards": [
            {"name": "자료실 홈", "url": "https://library.kcue.or.kr/subhomepage1/usmn000.jsp"},
        ],
        "priority_docs": [
            "2028학년도 대학입학전형 시행계획 모음집 (PDF/HWP)",
        ],
        "collect_status": "JS_REQUIRED_PENDING",
    },
    {
        "source_key": "moe",
        "institution_name": "교육부(Ministry of Education)",
        "institution_type": "MINISTRY",
        "base_url": "https://www.moe.go.kr/",
        "robots_our_ua_allowed": True,
        "robots_notes": "robots.txt: `Disallow: /search`만. 본문·게시판(boardCnts) 허용. 루트는 /main.do?s=moe로 JS 리다이렉트. 2026-10-13 실측.",
        "reuse_terms": "공공누리(KOGL) — 공공저작물 자유이용. 단 검색(/search)은 robots 차단 → 게시판 직접 탐색.",
        "redistribution": "OPEN",
        "access_method": "HTTP_STATIC",
        "seed_boards": [
            {"name": "보도자료(boardID=294)", "url": "https://www.moe.go.kr/boardCnts/listRenew.do?boardID=294&m=0204&s=moe"},
            {"name": "보도자료(boardID=295)", "url": "https://www.moe.go.kr/boardCnts/listRenew.do?boardID=295&m=020401&s=moe"},
            {"name": "정책(boardID=312)", "url": "https://www.moe.go.kr/boardCnts/listRenew.do?boardID=312&m=0301&s=moe"},
        ],
        "priority_docs": [
            "2028학년도 대학입학전형 시행계획 확정안 (교육부 발표)",
            "대학입학전형 시행계획 관련 보도자료",
        ],
        "collect_status": "PENDING",
    },
    {
        "source_key": "suneung",
        "institution_name": "한국교육과정평가원 대학수학능력시험(suneung.re.kr)",
        "institution_type": "AGENCY",
        "base_url": "https://www.suneung.re.kr/",
        "robots_our_ua_allowed": False,
        "robots_notes": (
            "www.suneung.re.kr/robots.txt = `User-agent: * / Disallow: /` (2026-10-13 curl 실측, HTTP 200 text/plain) "
            "→ 전봇 전면 차단. RobotsGate가 index.jsp 요청 BLOCK 확인. "
            "(search.suneung.re.kr은 robots 404지만 성적조회=로그인 개인정보로 별도 접근금지.)"
        ),
        "reuse_terms": "자동수집 금지(robots). 수능 시행계획은 메타·공식링크만. 성적조회(search.) 로그인벽 절대 우회 금지.",
        "redistribution": "METADATA_PRIORITY",
        "access_method": "METADATA_ONLY",
        "seed_boards": [],
        "priority_docs": [
            "2028학년도 대학수학능력시험 시행기본계획 — robots 차단으로 메타·링크만",
        ],
        "collect_status": "BLOCKED_BY_ROBOTS",
        "exclude_urls": ["https://search.suneung.re.kr/"],  # 성적조회=로그인벽·개인정보
    },
    {
        "source_key": "ebsi",
        "institution_name": "EBSi 수능/입시(ebsi.co.kr)",
        "institution_type": "BROADCAST",
        "base_url": "https://www.ebsi.co.kr/",
        "robots_our_ua_allowed": True,
        "robots_notes": (
            "robots.txt: Qna/Epilogue/*.ajax/TotalSearch/retrieveSbjtDtl 등 Disallow, `Allow: /`. "
            "루트는 /ebs/pot/poti/main.ebs로 JS 리다이렉트. 2026-10-13 실측."
        ),
        "reuse_terms": "EBS 해설·전략 콘텐츠는 **공식 전형규정과 구분**(작업지시 3단계). 저작권 주의 → METADATA_PRIORITY.",
        "redistribution": "METADATA_PRIORITY",
        "access_method": "HTTP_STATIC",
        "seed_boards": [
            {"name": "홈", "url": "https://www.ebsi.co.kr/ebs/pot/poti/main.ebs"},
        ],
        "priority_docs": [
            "대입 전략·전형 안내 (참고자료, NON_OFFICIAL_RULE로 분류)",
        ],
        "collect_status": "PENDING",
        "content_class": "NON_OFFICIAL_RULE",  # 공식 전형규정 아님 플래그
    },
    {
        "source_key": "univ_admission_offices",
        "institution_name": "대학별 입학처(개별 공식 홈페이지)",
        "institution_type": "UNIVERSITY",
        "base_url": "",
        "robots_our_ua_allowed": None,  # 대학별 상이 → 수집 시 RobotsGate가 개별 판정
        "robots_notes": "대학마다 robots·이용조건 상이. 수집기(RobotsGate)가 요청마다 개별 판정·기록.",
        "reuse_terms": "대학별 공지·모집요강. 재배포 제한 가능 → METADATA_PRIORITY.",
        "redistribution": "METADATA_PRIORITY",
        "access_method": "HTTP_STATIC",
        "seed_boards": [],  # PoC에서 샘플대학 입학처 URL을 채워 확장
        "priority_docs": [
            "2028학년도 수시·정시 모집요강",
            "2027학년도 입시결과(경쟁률·충원합격·등록자 성적)",
        ],
        "collect_status": "PENDING",
    },
]


def by_key(key: str) -> dict | None:
    for s in SOURCES:
        if s["source_key"] == key:
            return s
    return None


def crawlable_sources() -> list[dict]:
    """본문 자동수집이 허용되는(robots True + HTTP_STATIC) 출처만."""
    return [s for s in SOURCES
            if s.get("robots_our_ua_allowed") is True
            and s.get("access_method") == "HTTP_STATIC"]


if __name__ == "__main__":
    print(f"총 출처 {len(SOURCES)}개")
    for s in SOURCES:
        flag = {True: "ALLOW", False: "BLOCK", None: "PER-URL"}[s.get("robots_our_ua_allowed")]
        print(f"  [{flag:7}] {s['source_key']:22} {s['access_method']:14} seeds={len(s['seed_boards'])}")
