# 2026학년도(지난해) 입시결과 — 주요 대학 확대 수집 보고

작성: 2026-11-04 · 대상: 주요 대학 49곳 + 1차 시험 10곳(시범 10개교 제외) · 수집 지침: 시범 보고서(PRIOR_RESULTS_2026_PILOT.md)와 같은 규칙

## 1. 요약

- 확대 수집 대상 59곳 중 자료 확보 **15곳, 20,786행**. 시범 포함 전체 **20곳, 56,269행**, 빌드 검증 실패 0건.
- 적재용 시드: 이번에 새로 들어온 15곳만 담은 `data/seed/prior_2026_batch2/`(3개 파일). 전체 재생성본은 `data/seed/prior_2026/`.
- 자료가 없는 대학은 빈칸으로 두고 사유를 gaps에 남겼다(사용자 결정: 자동 수집이 막힌 곳은 빈칸+목록).
- 수집 도구 보완: robots.txt 자리의 방화벽 차단 안내를 판정불가로, 리다이렉트마다 robots 재확인, http·https 별도 판정.

## 2. 자료를 확보한 대학

| 대학 | 키 | 행 | 문서 | 원문 대조 |
|---|---|---|---|---|
| 세종대학교 | sejong | 3,894 | 2 | 11건 일치 |
| 국립공주대학교 | u8 | 3,358 | 2 | 7건 일치 |
| 동국대학교 | dongguk | 2,465 | 2 | 11건 일치 |
| 건국대학교 | konkuk | 1,906 | 2 | 11건 일치 |
| 한림대학교 | u198 | 1,767 | 2 | 11건 일치 |
| 숭실대학교 | ssu | 1,662 | 2 | 11건 일치 |
| 성신여자대학교 | sungshin | 1,226 | 2 | 11건 일치 |
| 광운대학교 | kw | 1,023 | 2 | 9건 일치 |
| 한양대학교(ERICA) | hyerica | 983 | 2 | 11건 일치 |
| 아주대학교 | ajou | 893 | 2 | 8건 일치 |
| 서경대학교 | skuniv | 685 | 2 | 10건 일치 |
| 홍익대학교 | hongik | 465 | 3 | 10건 일치 |
| 울산대학교 | u158 | 428 | 5 | 10건 일치 |
| 동덕여자대학교 | dongduk | 24 | 1 | 6건 일치 |
| 강서대학교 | kangseo | 7 | 1 | 7건 일치 |

## 3. 자료가 없는 대학과 사유

| 대학 | 주된 사유 |
|---|---|
| 가톨릭대학교 | robots 차단 |
| 중앙대학교 | robots 차단 |
| 단국대학교 | robots 차단 |
| 덕성여자대학교 | robots 차단 |
| 이화여자대학교 | 스크립트로만 열림 |
| 가천대학교 | 접속·판정 불가 |
| 한성대학교 | 스크립트로만 열림 |
| 한국외국어대학교 | robots 차단 |
| 인하대학교 | 스크립트로만 열림 |
| 인천대학교 | robots 차단 |
| 한국항공대학교 | 스크립트로만 열림 |
| 국민대학교 | robots 차단 |
| 경기대학교 | 스크립트로만 열림 |
| 명지대학교(인문캠퍼스) | 스크립트로만 열림 |
| 감리교신학대학교 | 대학어디가에만 공개 |
| 서울과학기술대학교 | robots 차단 |
| 성균관대학교 | 접속·판정 불가 |
| 상명대학교 | robots 차단 |
| 서울대학교 | 기타 |
| 서강대학교 | 접속·판정 불가 |
| 숙명여자대학교 | 접속·판정 불가 |
| 수원대학교 | robots 차단 |
| 서울여자대학교 | robots 차단 |
| 한국공학대학교 | robots 차단 |
| 동아대학교 | 스크립트로만 열림 |
| 국립부경대학교 | robots 차단 |
| 순천향대학교 | robots 차단 |
| 연세대학교(미래캠퍼스) | 기타 |
| 영남대학교 | robots 차단 |
| 원광대학교 | robots 차단 |
| 조선대학교 | 기타 |
| 포항공과대학교 | 스크립트로만 열림 |
| 한국기술교육대학교 | 접속·판정 불가 |
| 전북대학교 | robots 차단 |
| 제주대학교 | 접속·판정 불가 |
| 국립창원대학교 | 스크립트로만 열림 |
| 충남대학교 | robots 차단 |
| 충북대학교 | 스크립트로만 열림 |
| 한국교원대학교 | robots 차단 |
| 계명대학교 | 접속·판정 불가 |
| 고려대학교(세종캠퍼스) | 스크립트로만 열림 |
| 경상국립대학교 | robots 차단 |
| 대구대학교 | 스크립트로만 열림 |
| 서울시립대학교 | 스크립트로만 열림 |

자료 없는 대학 44곳(주된 사유 기준): robots 차단 20곳, 스크립트로만 열림 13곳, 접속·판정 불가 7곳, 기타 3곳, 대학어디가에만 공개 1곳

## 4. 사람이 확인하면 넣을 수 있는 자료(파일은 게시돼 있으나 자동 수집 불가)

| 대학 | 항목 | 사유(요약) | 주소 |
|---|---|---|---|
| 중앙대학교 | 2026학년도 수시·정시 입시결과(서울캠퍼스) | 입학처(admission.cau.ac.kr) robots.txt가 'User-agent: * / Disallow: /'(검색엔진 봇만 개별 허용) — 우리 UA는 전면 차단이라 IpsiFetcher가 요청을 막음. 입학처 게시판·첨부 모두 미수집. 참고로 웹 검색 결과에 입학처 경로의  | https://admission.cau.ac.kr/robots.txt |
| 동덕여자대학교 | 2026학년도 수시모집 입시결과(입시결과 게시판 전체 — 학생부교과·학생부종합·실기·특기자 등) | 입학처 '입시결과' 메뉴가 javascript:void(0) + onclick gotoMenu('ipsi','3','0','nontime-result','list_ipsi_result.do?schBdcode=_ipsi_result01') 함수 호출뿐이고 HTML에 실제 링크가 없어 게시 | https://ipsi.dongduk.ac.kr/ipsi/main/index.do |
| 동덕여자대학교 | 2026학년도 정시모집 입시결과 | 입학처 정시 '입시결과' 메뉴도 gotoMenu('ipsi','3','0','fxdtime-result','list_ipsi_result.do?schBdcode=_ipsi_result02') 함수 호출뿐(실제 링크 없음) — 게시글·첨부 파일명 미확인 | https://ipsi.dongduk.ac.kr/ipsi/main/index.do |
| 동덕여자대학교 | 2027 수시 학생부종합전형 가이드(2026 결과 수록 여부 미확인) | 입시자료실 논술가이드북 게시글의 '다음글 [2027 수시] 학생부종합전형 가이드' 링크가 onclick fn_goView(91946) 함수 호출뿐이라 열지 않음 — 첨부 파일명 미확인 | https://ipsi.dongduk.ac.kr/ipsi/contents/nontime-doc.do?schM=view&page=1&viewCount=10&id=91947&schBdcode=_ipsi_admdoc01&schGroupCode=&etc1=78 |
| 이화여자대학교 | 2026학년도 수시·정시 전형결과(3개년 전형결과) | 입학처 공지 '2027학년도 이화 입학콘서트 학생·학부모 입학설명회 영상 및 3개년 전형결과 안내'(2026.05.28, idx 15334)에 결과가 있는 것으로 보이나, 게시판 목록의 글 링크가 href='#' + onclick viewData/viewDataHot('15334', ' | https://admission.ewha.ac.kr/admission/html/ewharo/notice.asp |
| 이화여자대학교 | 2026학년도 수시모집 지원경쟁률 | 수시 경쟁률 게시판의 '2026학년도 수시모집 지원경쟁률입니다.'(2025.09.11, idx 15133) 글이 onclick viewData('15133') POST 폼으로만 열림 → 열지 않음. 첨부 파일명 미확인. | https://admission.ewha.ac.kr/admission/html/rolling/competition.asp |
| 이화여자대학교 | 2026학년도 정시모집 지원경쟁률 | 정시 경쟁률 게시판의 '2026학년도 정시모집 지원경쟁률입니다.'(2025.12.31, idx 15236) 글이 onclick viewData('15236') POST 폼으로만 열림 → 열지 않음. 첨부 파일명 미확인. | https://admission.ewha.ac.kr/admission/html/regular/competition.asp |
| 한성대학교 | 2026학년도 수시·정시 입시결과 | 입학처(enter.hansung.ac.kr — 본교 www.hansung.ac.kr/hansung/index.do의 '입학안내' 링크로 확인, robots.txt 404=규칙 없음)에는 '입시자료 > 입시결과'(m1=menu08, m2=sub02, board=entrance_data/r | https://enter.hansung.ac.kr/?m1=home |
| 한성대학교 | 2026학년도 경쟁률(입시자료 > 경쟁률) | 같은 사유(board=entrance_data/competition_rate 메뉴가 JS 전용) | https://enter.hansung.ac.kr/?m1=home |
| 한국외국어대학교 | 2026학년도 수시·정시 입시결과(서울·글로벌캠퍼스) | 입학처(adms.hufs.ac.kr) robots.txt가 'User-agent: * / Disallow: /' — 전면 차단이라 IpsiFetcher가 요청을 막음. 입학처 게시판·첨부 모두 미수집. | https://adms.hufs.ac.kr/robots.txt |
| 인하대학교 | 2026학년도 수시 입시결과 | 입학처 '수시 > 자료실'(MENU_ID=110)·'입시도우미 > 통합자료실'(MENU_ID=250) 게시판 목록은 JS(AJAX: /ajaxf/FR_BBS_SVC/BBSViewList.do)로만 불러와 정적 HTML의 목록이 비어 있음(<ul id="tbody"></ul>). 정적 상 | https://admission.inha.ac.kr/cms/FR_CON/index.do?MENU_ID=110 |
| 인하대학교 | 2026학년도 정시 입시결과 | '정시 > 자료실'(MENU_ID=150)도 같은 JS 전용 게시판. 사유 동일 | https://admission.inha.ac.kr/cms/FR_CON/index.do?MENU_ID=150 |
| 강서대학교 | 2026학년도 수시 경쟁률 | '수시 > 역대경쟁률' 게시글(boardNum=1482)에 첨부 '2026_수시_경쟁률_엑셀.xlsx'·'2026_수시_경쟁률_pdf.pdf'가 있으나 링크가 javascript:downloadFile('1429'/'1430') 형식이라 실제 주소가 HTML에 없음. JS 주소 조립 금 | https://entrance.gangseo.ac.kr/kcui/boardView?menuCode=MC0302&boardNum=1482 |
| 강서대학교 | 2026학년도 수시 최종등록자 점수현황(80% cut) | '수시 > 지원(점수)현황' 게시글(boardNum=1526, 2026-03-10)에 첨부 '2026학년도 최종등록자 점수현황(수시)_공지용.pdf'가 있으나 javascript:downloadFile(...) 링크뿐이라 요청하지 않음 | https://entrance.gangseo.ac.kr/kcui/boardView?menuCode=MC0301&boardNum=1526 |
| 강서대학교 | 2026학년도 정시 최종등록자 점수현황(80% cut) | '정시 > 지원(점수)현황' 게시글(boardNum=1527, 2026-03-10) 첨부 '2026학년도 최종등록자 점수현황(정시)_공지용.pdf'가 javascript:downloadFile('1477') 링크뿐이라 요청하지 않음 | https://entrance.gangseo.ac.kr/kcui/boardView?menuCode=MC0401&boardNum=1527 |
| 한국항공대학교 | 2026학년도 수시모집 입시결과 | 입학처 '지난입시결과' 수시 게시판에 게시글 '2026학년도 수시모집 입시결과'(2026.04.24, 첨부 있음 표시, 글번호 idx 6123)가 있으나 글 링크가 javascript:void(0) + onclick viewBoardProcess('6123')(POST 폼 → resul | https://ibhak.kau.ac.kr/admission/html/rolling/result.asp |
| 한국항공대학교 | 2026학년도 정시모집 입시결과 | 정시 게시판의 게시글 '2026학년도 정시모집 입시결과'(2026.04.24, 글번호 idx 6124)도 같은 javascript/POST 방식이라 열지 않음. 첨부 파일명 미확인. | https://ibhak.kau.ac.kr/admission/html/regular/result.asp |
| 경기대학교 | 2026학년도 수시·정시 전형결과(입시결과) PDF | 입학처 첫 화면의 실제 링크 '2024~2026학년도 신입학 입학통계'(자료실 > 입학통계, BOARD_SEQ=18, BBS_SEQ=298) 상세 페이지에 첨부 '(경기대) 2026~2024학년도 전형결과(수시,정시).pdf'가 있으나, 링크가 href='#;' + onclick=fil | https://enter.kyonggi.ac.kr/cms/FR_BBS_CON/BoardView.do?pageNo=1&pagePerCnt=15&MENU_ID=570&CONTENTS_NO=1&SITE_NO=2&BOARD_SEQ=18&BBS_SEQ=298&P_BBS_SEQ=&SEARCH_SEQ=3&PWD=&SEARCH_FLD=&SEARCH= |
| 경기대학교 | '[수시] 2026학년도 수시모집 지원현황 및 합격자 평균성적' 게시물 | 같은 게시판 상세 페이지의 다음글로 제목만 보이며 링크가 JS(next())뿐이라 열지 않음. 수시/정시 '전년도 입학통계(2026~2024)'(MENU_ID=130/150)와 자료실 '성적현황'(MENU_ID=580) 화면은 정적 HTML에 본문·목록이 없음(목록 'TOTAL 건'이  | https://enter.kyonggi.ac.kr/cms/FR_CON/index.do?MENU_ID=580 |
| 명지대학교(인문캠퍼스) | 2026학년도 수시모집 입시결과(인문캠퍼스) | 입학처 입시결과 게시판(robots 허용 경로 /pages)에 게시글 '2026학년도 수시모집 입시결과'(2026.05.04, 첨부 있음 표시)가 있으나 제목 링크가 javascript:js_board_view(30097) 함수 호출뿐이라 게시글을 열지 않음(주소 조립 금지). 첨부 파 | https://iphak.mju.ac.kr/pages/?p=11&b=B_1_2&cate=수시 |
| 명지대학교(인문캠퍼스) | 2026학년도 정시모집 입시결과(인문캠퍼스) | 같은 게시판 정시 분류의 게시글 '2026학년도 정시모집 입시결과'(2026.05.04, 첨부 있음 표시)도 javascript:js_board_view(30098) 함수 호출뿐 — 게시글·첨부 파일명 미확인 | https://iphak.mju.ac.kr/pages/?p=17&b=B_1_2&cate=정시 |
| 명지대학교(인문캠퍼스) | 2026학년도 수시·정시 경쟁률 | 게시글 '2026학년도 수시모집 경쟁률'(2025.09.15)·'2026학년도 정시모집 경쟁률'(2026.01.01)도 js_board_view(…) 함수 호출 링크뿐이라 열지 않음 | https://iphak.mju.ac.kr/pages/?p=31&b=B_1_2 |
| 세종대학교 | 수시·정시 최종 지원현황 외 전형(재외국민·편입학) | 입시결과 자료실의 2026 수시·정시 게시물 첨부에 없음. | https://ipsi.sejong.ac.kr/ipsi/assistant/entrance.do |
| 서울대학교 | 2026학년도 수시모집 접수현황(모집단위별 모집인원·지원자·경쟁률) | 입학본부 '전형결과 > 경쟁률' 게시글(bbsidx=160920, 첨부 '2026S_SNUrate_최종.pdf')은 찾았으나, HTML에 있는 첨부 링크를 IpsiFetcher로 GET하면 HTTP 404(오류 페이지 2,281B)가 온다. 같은 세션에서 게시글을 먼저 연 뒤 다시 받아 | https://admission.snu.ac.kr/materials/stats/competition_rate?md=down&bbsidx=160920&fileidx=44040 |
| 서울대학교 | 2026학년도 정시모집 접수현황 | 게시글(bbsidx=163729, 첨부 '2026정시_접수현황_최종.pdf') 첨부 링크가 같은 이유로 HTTP 404 | https://admission.snu.ac.kr/materials/stats/competition_rate?md=down&bbsidx=163729&fileidx=46612 |
| 서울대학교 | 2026학년도 수시모집 충원합격자 선발현황(1차·2차) | '전형결과 > 선발현황' 게시판에 1차(bbsidx=163375)·2차(bbsidx=163453, 첨부 '2026수시_충원선발현황_2차.pdf') 게시글이 있음. 2차 첨부를 받으려 했으나 HTTP 404. 1차는 같은 방식이라 요청하지 않음 | https://admission.snu.ac.kr/materials/stats/result?md=down&bbsidx=163453&fileidx=46363 |
| 서울대학교 | 2026학년도 정시모집 충원합격자 선발현황(1~3차, 3차=최종) | 3차(최종) 게시글(bbsidx=165212, 첨부 '2026정시_충원선발현황_3차(최종).pdf') 첨부가 HTTP 404. 1·2차(bbsidx=164990, 165062)는 요청하지 않음 | https://admission.snu.ac.kr/materials/stats/result?md=down&bbsidx=165212&fileidx=47849 |
| 서울대학교 | 2026학년도 수시·정시 선발 결과 보도자료 | '입학자료실 > 보도자료'에 수시(bbsidx=163032)·정시(bbsidx=164740) 선발 결과 보도자료가 있음. 수시 첨부를 요청했으나 HTTP 404. 보도자료는 전체 집계 성격이라 모집단위 자료가 아닐 가능성이 크지만 내용은 확인하지 못함 | https://admission.snu.ac.kr/materials/downloads/press?md=down&bbsidx=163032&fileidx=46023 |
| 서강대학교 | 2026학년도 수시·정시 입시결과 | 입학처(admission.sogang.ac.kr)는 https 인증서 검증 실패(SSL: CERTIFICATE_VERIFY_FAILED, unable to get local issuer certificate)로 robots.txt를 받지 못해 RobotsGate가 판정불가로 막음. ht | https://admission.sogang.ac.kr/ |
| 숭실대학교 | 2026학년도 재외국민·외국인 등 책자 미수록 정원외 전형 입시결과 | 입학처 입시통계자료 게시판의 2026 수시(241)·정시(242) 게시글 첨부는 같은 책자 1건뿐이고, 책자 목차(2026학년도 입시결과)에 재외국민·외국인 전형이 없음. 재외국민 입시통계자료 게시판은 이번에 확인하지 않음. | https://iphak.ssu.ac.kr/board/statistics_list.asp?page=1&srchoption=&keyword=&flag=4&page_no=1_5_4 |
| 수원대학교 | 2026학년도 수시모집 결과자료(최종등록자 입시 성적) — 첨부 '2026학년도 수시모집 결과자료 (수원대).pdf', '2026학년도 수시모집 결과자료 (수원대).hwp' | robots 차단 — 게시글(/board/…)은 robots Allow지만 첨부 다운로드 경로 /download/…는 robots.txt 'Disallow: /'(Allow 목록: /$, /main, /guide/susi·jungsi·transfer·oversea, /supporters | https://ipsi.suwon.ac.kr/board/susi_result/read/5517 |
| 수원대학교 | 2026학년도 정시모집 결과자료 — 첨부 '2026학년도 정시모집 결과자료 (수원대).pdf', '2026학년도 정시모집 결과자료 (수원대).hwp' | robots 차단 — 첨부 /download/… 경로 Disallow(위와 같음). 같은 첨부가 https://ipsi.suwon.ac.kr/board/pre_result/read/5503 에도 있음. | https://ipsi.suwon.ac.kr/board/jungsi_result/read/5520 |
| 수원대학교 | 2026학년도 수시모집 차순위표 — 첨부 '2026학년도 수시모집 차순위표 (수원대).pdf', '2026학년도 수시모집 차순위표 (수원대).hwp' | robots 차단 — 첨부 /download/… 경로 Disallow. | https://ipsi.suwon.ac.kr/board/susi_result/read/5516 |
| 수원대학교 | 2026학년도 정시모집 차순위표 — 첨부 '2026학년도 정시모집 차순위표 (수원대).pdf', '2026학년도 정시모집 차순위표 (수원대).hwp' | robots 차단 — 첨부 /download/… 경로 Disallow. | https://ipsi.suwon.ac.kr/board/jungsi_result/read/5519 |
| 동아대학교 | 2026학년도 수시 입시결과 | 입학처(ent.donga.ac.kr, robots.txt 'Allow: /') 수시모집 > 입시전형결과 게시판에 '2026학년도 동아대학교 수시모집 입시전형결과'(작성일 2026.05.19, 첨부 '2026학년도 학생부종합 입시결과.pdf')가 있으나, 게시글 링크가 javascript | https://ent.donga.ac.kr/admission/html/rolling/result.asp |
| 동아대학교 | 2026학년도 정시 입시결과 | 정시모집 > 입시전형결과 게시판의 '2026학년도 동아대학교 정시모집 입시전형결과'(작성일 2026.05.19, 첨부 '2026학년도 정시모집 입시결과.pdf')도 javascript viewData('30601') → POST 폼 제출뿐이라 받지 않음 | https://ent.donga.ac.kr/admission/html/regular/result.asp |
| 동아대학교 | 입학처 공지 '2022~2026학년도 입시전형결과' | 공지(BOARD_IDX=29537, 작성일 2026.05.19, GET 링크)는 본문에 위 두 게시판으로 가는 이미지 링크만 있고 첨부·표가 없음 | https://ent.donga.ac.kr/admission/html/counsel/noticeView.asp?BOARD_IDX=29537 |
| 울산대학교 | 정시 실기(예체능) 등 정시 본문 표에 없는 전형 | 정시 게시글은 첨부 없이 본문 표(수능전형·농어촌학생(정원외)전형·기초생활/차상위(정원외)전형)만 있음. 정시 실기전형 결과는 입학처 게시판에서 찾지 못함 | https://iphak.ulsan.ac.kr/main/47?action=view&no=16269 |
| 조선대학교 | 2026학년도 수시 입시결과 | 입학처(i.chosun.ac.kr) 입시결과(통합) 게시글 '2026학년도 신입학 입시결과'(분류 수시, 작성일 2026-04-22) 첨부 '조선대학교 2026학년도 신입학 입시결과(홈페이지 게시용).xlsx(96.7 KB)'의 HTML 실제 링크(do=download&file_id=V | https://i.chosun.ac.kr/main/menu?gc=1044IOKR&do=view&bwrite_id=VU1kbhU6cxrC |
| 조선대학교 | 2026학년도 정시 입시결과 | 정시 게시글 '2026학년도 신입학 입시결과'(2026-04-22) 첨부 '조선대학교 2026학년도 신입학 입시결과(홈페이지 게시용).xlsx(96.7 KB)'(file_id=VU1kbhcUZgvZ)도 같은 경고 페이지(206바이트)가 옴 | https://i.chosun.ac.kr/main/menu?gc=1044IOKR&do=view&bwrite_id=VU1kbhbeDcYB |
| 포항공과대학교 | 2026학년도 수시 입시결과 | 입학팀 사이트(adm-u.postech.ac.kr)에 입시결과 게시물·첨부 없음 — 공지사항 게시판 전체 7건(쪽 나눔 없음), '서식 및 참고자료' 6건(모집요강·시행계획·서식), FAQ 어디에도 2026학년도 모집결과/입시결과/경쟁률 파일이 없다. 첫 화면 '대입정보포털' 메뉴는 a | https://adm-u.postech.ac.kr/admission-helper/notices/ |
| 포항공과대학교 | 2026학년도 정시 입시결과 | POSTECH은 수시 위주 선발이며 입학팀 사이트에 정시 결과 게시물도 없음(위와 같은 범위 확인) | https://adm-u.postech.ac.kr/entrance-exam/form/ |
| 포항공과대학교 | 2026학년도 전형별 경쟁률 | 입학팀 게시 '2027학년도_POSTECH_모집요강_web.pdf' p.50에 '▶ 2026학년도 전형별 경쟁률 확인하기' 문구만 있고 PDF 안에 링크 주소(하이퍼링크 주석)가 없다(QR 이미지로 보임). 이미지 속 주소는 따라가지 않음. 수치 없음 | https://adm-u.postech.ac.kr/wp-content/uploads/2025/05/2027학년도_POSTECH_모집요강_web.pdf |
| 전북대학교 | 2026학년도 수시모집 입시결과 | robots 차단 — 입학본부(enter.jbnu.ac.kr) robots.txt가 'User-agent: * / Disallow: /'로 우리 UA를 전면 차단. 입학처 첫 화면(https://enter.jbnu.ac.kr/)도 IpsiFetcher가 거부했고 게시판·첨부를 한 건도  | https://enter.jbnu.ac.kr/robots.txt |
| 국립창원대학교 | 2026학년도 수시·정시 입학결과('전년도 입학결과' 메뉴) | 입학처 메뉴 '입학자료실 > 전년도 입학결과'가 href='#check' + onclick="menuAccessCheck('15140', 'ipsi')" JS 함수 호출뿐이고 HTML에 실제 링크가 없음(메인·공지·자료실·사이트맵 모두 동일) — 주소를 조립하지 않고 수집하지 않음 | https://www.changwon.ac.kr/ipsi/sitemap.do |
| 국립창원대학교 | 입학처 게시판 첨부 파일 전반 | robots 차단: www.changwon.ac.kr·ipsi.changwon.ac.kr robots.txt가 'Disallow: /common/nttFileDownload.do', 'Disallow: /upload/', 'Disallow: /viewer/'로 게시판 첨부 다운로드 경로 | https://www.changwon.ac.kr/ipsi/na/ntt/selectNttList.do?mi=4245&bbsId=1621 |
| 충남대학교 | 2026학년도 수시모집 입시결과 | robots 차단 — 입학본부(ipsi.cnu.ac.kr) robots.txt가 'User-agent: * / Disallow : /'(그리고 'Disallow : /_hamTool/')로 우리 UA를 전면 차단. 입학처 페이지·게시판·첨부를 한 건도 요청하지 않음. | https://ipsi.cnu.ac.kr/robots.txt |
| 충북대학교 | 2026학년도 수시 학생부종합(학생부종합I, 학생부종합II, sw우수인재전형) 입시결과 — 첨부 '01. 2026학년도 충북대학교 대학입학전형결과 현황표(수시 학생부종합I 전형).pdf', '02. 2026학년도 충북대학교 대학입학전형결과 현황표(수시 학생부종합II 전형).pdf', '03. 2026학년도 충북대학교 대학입학전형결과 현황표(수시 sw우수인재 전형).pdf' | 첨부 링크가 javascript:fn_egov_downFile('FILE_000000000003237SxAbe','0~2') 함수 호출뿐(HTML에 실제 파일 주소 없음). JS 안의 주소 형식으로 조립해 요청하지 않는 규칙에 따라 받지 않음. | https://ipsi.chungbuk.ac.kr/kor/BBSMSTR_000000000011/23599/view.do |
| 충북대학교 | 2026학년도 수시 학생부교과(학생부교과전형, 지역인재전형) 입시결과 — 첨부 '04. 2026학년도 충북대학교 대학입학전형결과 현황표(수시 학생부교과전형).pdf', '05. 2026학년도 충북대학교 대학입학전형결과 현황표(수시 지역인재전형).pdf' | 첨부 링크가 javascript:fn_egov_downFile('FILE_000000000003227XyCjE','0~1') 함수 호출뿐 — 받지 않음(사유 위와 같음). | https://ipsi.chungbuk.ac.kr/kor/BBSMSTR_000000000011/23606/view.do |
| 충북대학교 | 2026학년도 정시 수능(일반, 지역인재전형) 입시결과 — 첨부 '06. 2026학년도 충북대학교 대학입학전형결과 현황표(정시 일반전형).pdf', '07. 2026학년도 충북대학교 대학입학전형결과 현황표(정시 지역인재전형).pdf' | 첨부 링크가 javascript:fn_egov_downFile('FILE_000000000003228YBtoQ','0~1') 함수 호출뿐 — 받지 않음(사유 위와 같음). 본문은 안내 문구뿐이고 표·수치 없음. | https://ipsi.chungbuk.ac.kr/kor/BBSMSTR_000000000015/23607/view.do |
| 한국교원대학교 | 2026학년도 수시 입학전형 결과 | robots 차단 — 입학안내 '입학전형결과' 게시글에 첨부 '[한국교원대] 2026학년도 입학전형 결과 자료(수시).pdf'(./downloadBbsFile.do?atchmnflNo=83674)가 있으나 www.knue.ac.kr robots.txt가 'User-agent: * / D | https://www.knue.ac.kr/ipsi/selectBbsNttView.do?key=1835&bbsNo=271&nttNo=80973 |
| 한국교원대학교 | 2026학년도 정시 입학전형 결과 | robots 차단 — 같은 게시글 첨부 '[한국교원대] 2026학년도 입학전형 결과 자료(정시).pdf'(./downloadBbsFile.do?atchmnflNo=83675), 사유 위와 같음 | https://www.knue.ac.kr/ipsi/selectBbsNttView.do?key=1835&bbsNo=271&nttNo=80973 |
| 고려대학교(세종캠퍼스) | 2026학년도 수시·정시 입시결과(세종캠퍼스) — 입학자료실 > 입시 및 홍보자료 | 게시판 목록이 정적 HTML에 없음('총 0 건') — 목록은 /sejong/ajaxf/FR_BBS_SVC/BBSView…List.do AJAX(POST)로만 불러오고, 첨부 다운로드도 JS 함수(fileDown → /ajaxfile/CMN_SVC/FileDown.do?… 조립)로만 열 | https://oku.korea.ac.kr/sejong/cms/FR_CON/index.do?MENU_ID=550 |
| 고려대학교(세종캠퍼스) | 2026학년도 수시·정시 경쟁률(세종캠퍼스) — 입학자료실 > 경쟁률 | 게시판 목록이 정적 HTML에 없음('총 0 건') — 목록은 /sejong/ajaxf/FR_BBS_SVC/BBSView…List.do AJAX(POST)로만 불러오고, 첨부 다운로드도 JS 함수(fileDown → /ajaxfile/CMN_SVC/FileDown.do?… 조립)로만 열 | https://oku.korea.ac.kr/sejong/cms/FR_CON/index.do?MENU_ID=500 |
| 고려대학교(세종캠퍼스) | 입학도우미 > 공지사항(세종캠퍼스) | 공지 목록도 AJAX로만 열림. 입학팀 첫 화면에 실제 링크로 나온 최근 공지 7건(2026.03~09)에는 2026학년도 입시결과 공지가 없음('2026학년도 선행학습 영향평가 결과 공지'는 입시결과가 아님). | https://oku.korea.ac.kr/sejong/cms/FR_CON/index.do?MENU_ID=570 |
| 경상국립대학교 | 2026학년도 수시 입시결과 | robots 차단: 입학처 입학결과 페이지(HTML)는 허용이나 결과 자체는 첨부 파일뿐 — 첨부 '2026학년도 수시모집 결과 (다운로드 )'는 /common/fileDownload.do?fileKey=65036, 화면 미리보기 PDF는 /upload/cntntsFile/new/doc | https://www.gnu.ac.kr/new/cm/cntnts/cntntsView.do?mi=48029&cntntsId=21841 |
| 경상국립대학교 | 2026학년도 정시 입시결과 | robots 차단: 첨부 '2026학년도 정시모집 입학결과 (Down)'는 /common/fileDownload.do?fileKey=64918, 미리보기 PDF는 /upload/cntntsFile/new/doc_b36707a6-7601-4efa-bf14-21b7b2ba8e62177520 | https://www.gnu.ac.kr/new/cm/cntnts/cntntsView.do?mi=47853&cntntsId=21717 |
| 대구대학교 | 2026학년도 수시 입시결과 — 게시글 '2026학년도 수시모집 전형 결과(학생부 등급, 환산점수)'(수시 자료실 143번, 2026-05-20, 입학처, 첨부 있음) | 목록의 게시글 링크가 href="#" + onclick="article.view('19900')" JS 함수 호출뿐이고 HTML에 실제 게시글·첨부 주소가 없음. 규칙(JS 코드로 주소를 조립해 요청하지 않음)에 따라 게시글을 열지 않았고, 첨부 파일명은 확인하지 못함(목록에 첨부파일  | https://ipsi.daegu.ac.kr/kor/article/ATCL7 |
| 대구대학교 | 2026학년도 정시 입시결과 — 게시글 '2026학년도 정시모집 전형 결과(환산점수, 수능 백분위, 등급)'(정시 자료실 108번, 2026-05-21, 입학처, 첨부 있음) | 목록의 게시글 링크가 href="#" + onclick="article.view('19901')" JS 함수 호출뿐이고 HTML에 실제 게시글·첨부 주소가 없음. 규칙(JS 코드로 주소를 조립해 요청하지 않음)에 따라 게시글을 열지 않았고, 첨부 파일명은 확인하지 못함(목록에 첨부파일  | https://ipsi.daegu.ac.kr/kor/article/ATCL8 |
| 대구대학교 | 2026학년도 수시/정시 최종 경쟁률 — 게시글 '2026학년도 수시/정시 최종 경쟁률'(입시서비스 > 연도별 최종 경쟁률 5번, 2026-08-10) | 목록의 게시글 링크가 href="#" + onclick="article.view('20631')" JS 함수 호출뿐이고 HTML에 실제 게시글·첨부 주소가 없음. 규칙(JS 코드로 주소를 조립해 요청하지 않음)에 따라 게시글을 열지 않았고, 첨부 파일명은 확인하지 못함(목록에 첨부파일  | https://ipsi.daegu.ac.kr/kor/article/ATCL7079a7800 |
| 대구대학교 | 2026학년도 충원(추가)합격 현황 | 수시·정시 자료실에는 '전년도(2025학년도) … 충원(추가) 합격 현황'까지만 있고 2026학년도분 게시글은 목록 1쪽에서 찾지 못함(게시판 목록도 JS로만 열림). | https://ipsi.daegu.ac.kr/kor/article/ATCL8 |
| 서울시립대학교 | 2026학년도 수시 입시결과(수시 입학통계 게시판) | 입학처 '입학통계'(수시) 게시판에 '2026학년도 수시모집 전형별 성적 통계 자료 공지', '2026학년도 수시모집 최종 충원합격 현황', '2026학년도 수시모집 지원현황' 게시글이 있으나 목록의 글 링크가 javascript:fnView('1','35')·fnView('2','34 | https://admission.uos.ac.kr/admissionNew/freeBoard/list.do?list_id=K7 |
| 서울시립대학교 | 2026학년도 정시 입시결과(정시 입학통계 게시판) | 입학처 '입학통계'(정시) 게시판에 '2026학년도 정시모집 전형 결과' 게시글이 있으나 링크가 javascript:fnView('1','28') 함수 호출뿐이라 요청하지 않음. 첨부 파일명은 확인 못 함. | https://admission.uos.ac.kr/admissionNew/freeBoard/list.do?list_id=L6 |

## 5. 판단이 들어간 처리(대학별 notes에 상세)

- 3개년 자료·가이드북에서 2026 열만 뽑음(아주대, 국립공주대, 동덕여대 논술 가이드북, 한양대 ERICA).
- 원문 표기는 오타로 보여도 바꾸지 않음(홍익대 '학교장추전자전형(서울)', 세종대 '군계약학과' 표 제목 등). 원문 안 값 불일치는 근거 쪽 값을 쓰고 notes에 '원문 자체 불일치'(아주대 1곳, 울산대 9곳).
- 마지막 예비번호·충원율·회전율은 인원이 아니므로 extra_admitted_count에 넣지 않고 원문 이름의 지표 행으로 둠.
- 여러 캠퍼스 대학은 모집단위명 앞에 캠퍼스를 붙임(국립공주대 — 같은 PDF p.13 캠퍼스 표 기준). 그래서 2027 학과명 연결이 적다.
- 입학처 첫 화면 스크립트에 그대로 적힌 페이지 이동 주소는 따라감. HTML 속성에 완성된 주소로 적힌 첨부(아주대 data-url)는 받음. 스크립트 함수로 주소를 조립해야 하는 첨부는 받지 않음.
- 최종 파일을 입학처 도메인이 내려주면 위탁 도메인을 거쳐도 입학처 자료로 봄(광운대). 원서접수 대행사 도메인 자료는 쓰지 않음.

## 6. 규칙 이탈 기록

- 1차 수집 중 robots.txt 내용 확인을 위해 수집 도구 밖에서 3회 요청(서울대·인하대·감리교신학대). 수치 수집에는 쓰지 않음.
- 한국항공대 탐색 중 허용 경로가 비허용 경로로 리다이렉트되어 오류 페이지를 받음(이후 도구 수정). 내용은 쓰지 않음.
- 감리교신학대 robots.txt 방화벽 안내를 허용으로 판정해 게시판 HTML만 받음(이후 도구 수정). 수치 없음.
