#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/youtube/videos.json 생성기 (Qoder B / 2028 대입 유튜브 분석 DB).

입력: 로컬 수집 산출물 work/watch_meta.json, work/details_raw.json (비커밋·원문 캐시)
출력: repo/data/youtube/videos.json  (메타+링크+분석용 선별 정보만. 자막 원문은 저장하지 않는다)

사용:
    python scripts/youtube/yt_build_videos.py [--work DIR] [--out FILE]

설계 노트
- Qoder A의 공식 문서 레지스트리(data/meta, docs/schema)와 스키마 어휘를 재사용한다:
  verification_status(COLLECTED→EXTRACTED→NORMALIZED→REVIEW→APPROVED),
  content_class, redistribution, access_method, url_hash(sha256).
- 유튜브 영상은 content_class=NON_OFFICIAL_RULE(전문가 해석)이므로 상담 검색에 자동 반영하지 않는다.
- 신뢰도는 구독자·조회수 대신 1차 출처(공식 발표·자료)에 대한 인용 가능성과 출연자 전문성을 기준으로 tier를 부여한다.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

COLLECTED_AT = "2026-10-13"

# 채널 성격 / 신뢰 티어 / 근거
TIERS = {
    "TIER_1": "정부·교육청·공교육 방송 등 공식 진로진학 지원 자료. 1차 발표문에 직접 근거.",
    "TIER_2": "EBS·대표 입시기관·현직 진학지도 교사. 1차 자료(시행계획·연계교재·입결)를 인용하며 검증 가능.",
    "TIER_3": "학원가·개인 컨설팅·개인 크리에이터. 자체 경험·추론 비중이 높아 공식자료 대조 없이 확정 진술 금지.",
}

# video_id -> curated
# (channel_kind, tier, person, person_role, years, topics, evidence, note)
CURATED = {
    # ---- 2026 ----
    "2l5MSTGx57k": ("ENTRANCE_RESEARCH_INSTITUTE", "TIER_2", "김병진", "이투스 교육평가연구소장",
                    ["2028"], ["T02", "T03", "T05"], "video_level+chapters",
                    "9등급 입결과 5등급 내신의 관계를 묶고 정시 학생부 반영을 함께 다룬 라이브 설명회."),
    "no5MxDnvrNw": ("PRIVATE_CONSULTING", "TIER_3", "신동엽", "휴브레인 입시컨설팅 대표",
                    ["2026", "2028"], ["T05", "T03"], "chapters+desc_timestamps",
                    "2026 실제 충족률·충원율 자료를 2028 최저 변화에 외삽하는 구조. 충족률 수치는 2026 결과값."),
    "zmfHF85oi0w": ("PRIVATE_CONSULTING", "TIER_3", None, "입시왕(상담 방송)",
                    ["2028"], ["T08", "T05"], "desc_timestamps",
                    "학군지·정시 지향 학생의 내신/수능 배분 상담 사례."),
    "7SXzyGMDQFU": ("PUBLIC_EDUCATION_BROADCAST", "TIER_1", "김진석", "서울 소명여자고등학교 교사",
                    ["2028"], ["T04", "T06"], "description",
                    "EBS 입시의 정석. 대학별 권장과목 기반 학생부 설계."),
    "bDQePMO_FGU": ("PRIVATE_CONSULTING", "TIER_3", None, "입시왕(상담 방송)",
                    ["2028"], ["T03", "T08"], "chapters+desc_timestamps",
                    "선택과목 인원 감소에 따른 등급 하락 상담 사례 2건."),
    "ZetDtkXqkQc": ("PRIVATE_CONSULTING", "TIER_3", "유주미", "프리클래스 입시센터 소장",
                    ["2028"], ["T03", "T08"], "description",
                    "2.0~2.5등급 학생의 대학 라인 계산. 근거는 컨설턴트 경험값."),
    "Cjwcqf_08MM": ("PRIVATE_CONSULTING", "TIER_3", "강석", "프라임랩 입시전략연구소 소장",
                    ["2028"], ["T05"], "metadata_only",
                    "설명 없는 라이브 대담. 내용 수준 분석 불가."),
    "Iv0NWvvkMYo": ("PRIVATE_CONSULTING", "TIER_3", "신동엽", "휴브레인 입시컨설팅 대표",
                    ["2027", "2028"], ["T05", "T10"], "metadata_only",
                    "2027 경쟁률로 2028 서성한 교과 전형을 추정. 제목·해시태그만 확인."),
    "TTqcGf7Qw80": ("PRIVATE_CONSULTING", "TIER_3", "신동엽", "휴브레인 입시컨설팅 대표",
                    ["2028"], ["T03", "T09"], "metadata_only+author_correction",
                    "영상 내 오류를 설명란 정정 안내로 수정함(서울대 지균 1단계 3배수 유지, 추천 인원 2→3명)."),
    "0ynYLu8aHQw": ("ACADEMY_NETWORK", "TIER_3", "이종환", "대치명인학원 입시센터 소장",
                    ["2028"], ["T03", "T04", "T08"], "chapters+desc_timestamps",
                    "5등급제 2등급 착시·고교유형별 진학 실적 분석."),
    "EDy8CrcS0Ew": ("PRIVATE_CONSULTING", "TIER_3", None, "과제탐구연구소",
                    ["2028"], ["T03", "T08"], "chapters+desc_timestamps",
                    "'실제 5등급제 성적 자료'라 지칭하나 자료 출처 특정은 불명."),
    "oAS6fOoL1Oc": ("PUBLIC_EDUCATION_AGENCY", "TIER_1", None, "충청남도교육청진로융합교육원",
                    ["2028"], ["T07"], "metadata_only",
                    "2028 수능 통합사회 준비법. 설명이 해시태그 수준이라 내용 분석 불가."),
    "5R_7Z8tv7EQ": ("PUBLIC_EDUCATION_AGENCY", "TIER_1", None, "세종특별자치시교육청 진로교육원",
                    ["2028"], ["T05"], "metadata_only",
                    "2028 대입전형 시행계획 주요 내용 해설. 내용 분석 불가(설명 최소)."),
    "irJDnkEXIwM": ("PRIVATE_CONSULTING", "TIER_3", "강석", "분당 수이학원 소장(괜찮은뉴스)",
                    ["2028"], ["T05", "T03", "T08"], "chapters+desc_timestamps",
                    "전형별 모집비율·5등급/9등급 입결 환산·학군지 전략."),
    "uDJMZxXVrNA": ("ACADEMY_NETWORK", "TIER_3", "김학수", "전 하나고 진학부장",
                    ["2028"], ["T05", "T09", "T03"], "chapters+desc_timestamps",
                    "교과 100% 소멸·서류 정성평가 확대를 대학별 사례로 제시."),
    "npcWLvR-04M": ("INDIVIDUAL_CREATOR", "TIER_3", "창쌤", "서울대 출신 공학박사(수학)",
                    ["2028"], ["T01", "T04"], "description",
                    "고교학점제·수행평가·학생부 관리 관점의 학부모 설명."),
    "IGXh_rWLEuc": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "김성길", "EBSi 입시 강사",
                    ["2028"], ["T04", "T02"], "description",
                    "위계가 있는 과목 선택(일반선택→진로·융합선택) 주장."),
    "JYa1tBBiS3g": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "윤윤구", "EBSi 입시 대표 강사",
                    ["2028"], ["T02", "T05", "T09"], "description",
                    "서울 주요대 정시 변화 총정리."),
    "FATNU4ZgdAs": ("PRIVATE_CONSULTING", "TIER_3", None, "댓츠원 That's One",
                    ["2028"], ["T03", "T04", "T08"], "description",
                    "학교알리미 공개 지표(성취도·수행평가·이수과목) 기반 고교 선택 기준."),
    "qKrS9kdRL2U": ("PRIVATE_CONSULTING", "TIER_3", "장문성", "대치 IDA 입시연구소 원장",
                    ["2028"], ["T05", "T03", "T08"], "chapters+desc_timestamps",
                    "정시 비율 감소·수능 최저 확대·전형 복합화를 순서로 해설."),
    "XICpj0wJ8kw": ("ENTRANCE_RESEARCH_INSTITUTE", "TIER_2", "김병진", "이투스 교육평가연구소장",
                    ["2028"], ["T09", "T05"], "metadata_only",
                    "연세대 2028 전형계획 상세 분석. 설명이 해시태그뿐이라 내용 분석 불가."),
    "NkPaabmc3oI": ("PRIVATE_CONSULTING", "TIER_3", None, "과제탐구연구소",
                    ["2027", "2028"], ["T09", "T06"], "chapters+desc_timestamps",
                    "6대 이공계 특성화대(AI대학 신설·정시 축소·면접 강화) 정리."),
    "u0XbM_rPJEw": ("PUBLIC_EDUCATION_AGENCY", "TIER_1", "박문수", "대학진학지도지원단 교사(청원여고)",
                    ["2028"], ["T01", "T04", "T08"], "description",
                    "서울진로진학정보센터에 강의 원고·자료가 공개된 공식 설명회."),
    "8_sP4eMTweg": ("PUBLIC_EDUCATION_AGENCY", "TIER_1", "윤상형", "대학진학지도지원단 교사(영동고)",
                    ["2028"], ["T05", "T03"], "description",
                    "서울시교육청 2028 대입 전형의 이해와 대비. 강의 자료 공개."),
    "X3G5iKZnBnA": ("PRIVATE_CONSULTING", "TIER_3", None, "과제탐구연구소",
                    ["2028"], ["T08", "T05"], "description",
                    "중위권 학생 대상 전형별 전략 4단계."),
    "PV-UYtU0FZQ": ("ACADEMY_NETWORK", "TIER_3", None, "토마토스쿨 유니고 입시TV",
                    ["2028"], ["T09", "T05"], "chapters+desc_timestamps",
                    "서울권 의대 대학별 선발 방식 비교. 짧은 요약 수준."),
    "j4C-GLrIuKY": ("PRIVATE_CONSULTING", "TIER_3", None, "맘띵입시연구소",
                    ["2027", "2028"], ["T10", "T05"], "description",
                    "2027이 개편 전 마지막 입시라는 비교 축과 수시 6장 전략."),
    "gETq7gXv4VE": ("INDIVIDUAL_EXPERT", "TIER_2", "정성민", "전 서울대 입학관리본부 입학사정관",
                    ["2028"], ["T09", "T05"], "description",
                    "고려대 2028 시행계획 정밀독해. 대학 발표문 직접 대조형."),
    "NsHFuOsdwrw": ("PUBLIC_EDUCATION_BROADCAST", "TIER_1", "윤희태", "서울 영동일고등학교 교사",
                    ["2028"], ["T03", "T05"], "description",
                    "3학년 2학기까지 내신 반영·전형 다변화 해설(EBS뉴스)."),
    "RDsxacK7uY4": ("PRIVATE_CONSULTING", "TIER_3", None, "어센틱마인드",
                    ["2028"], ["T05", "T03", "T10"], "chapters+desc_timestamps",
                    "1차 자료 12종(교육부·평가원·대교협·종로학원·베리타스알파·DART) 인용을 명시. 수치 대조 가능."),
    "BELjVqV7zB4": ("INDIVIDUAL_EXPERT", "TIER_2", "정성민", "전 서울대 입학관리본부 입학사정관",
                    ["2028"], ["T09", "T05"], "description",
                    "연세대 2028 논술·수시·정시 전형계획 정밀독해."),
    "ea1NUYjcX-I": ("PRIVATE_CONSULTING", "TIER_3", "박경진", "대치 IDA 입시연구소 소장",
                    ["2028"], ["T05", "T09"], "desc_timestamps(40)",
                    "주요 15개대 정시 4타입 분류·교과/학종 변화를 타임스탬프로 세분화."),
    "SQd3yG1ztcE": ("INDIVIDUAL_CREATOR", "TIER_3", None, "노을커피의 교육.입시 TV",
                    ["2028"], ["T05", "T09"], "description",
                    "7개 대학(서연고서성한중) 시행계획 요약 + 블로그 표 자료."),
    "Xonr89xU-L8": ("ENTRANCE_MEDIA", "TIER_2", "이해웅", "입시탐탐 소장",
                    ["2028"], ["T04", "T09"], "chapters+desc_timestamps",
                    "중앙대·경희대·동국대·인하대·경기대 분석 + 고교학점제 비판."),
    "dbN_KdkSK9I": ("AI_CONSULTING_PLATFORM", "TIER_3", None, "바이브온(VIBEON)",
                    ["2028"], ["T03", "T08"], "chapters+desc_timestamps",
                    "생기부 강점·세특 서술 전략. 자사 AI 분석 서비스 홍보 포함."),
    "m_s6G9wQ6cQ": ("ENTRANCE_MEDIA", "TIER_2", "이해웅", "입시탐탐 소장",
                    ["2028"], ["T05", "T09"], "chapters",
                    "한양대·중앙대·경희대·건국대·동국대 2028 계획안 해석."),
    "aV5dSsiQCmw": ("PRIVATE_CONSULTING", "TIER_3", "펜타킬", "올인원에듀",
                    ["2028"], ["T01", "T03"], "description",
                    "'비교과 선행' 불안 마케팅 비판. 변별력 논란에 대한 반론 성격."),
    "LyaiiweT7JM": ("ENTRANCE_RESEARCH_INSTITUTE", "TIER_2", "김병진", "이투스 교육평가연구소장",
                    ["2028"], ["T05", "T03", "T02"], "chapters",
                    "전형별 선발비율·9등급vs5등급·정시 통사/통과 반영 라이브 1부."),
    "G5vtJ0Z-hTg": ("ENTRANCE_RESEARCH_INSTITUTE", "TIER_2", "김영준", "이투스247학원 입시센터장",
                    ["2028"], ["T04", "T06", "T03"], "chapters",
                    "정성평가 핵심을 '전공의 이해'로 정의하고 과목 선택-탐구 연계로 연결."),
    "qxFjhfPiB_U": ("PUBLIC_EDUCATION_BROADCAST", "TIER_1", "윤희태", "서울 영동일고등학교 교사",
                    ["2028"], ["T05", "T03", "T09"], "description(전문 텍스트)",
                    "EBS뉴스 문자보도형 설명. 대학별 정시 학생부/내신 반영 목록 포함."),
    "-yw3lq5Cblk": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "윤윤구", "EBSi 입시 대표 강사",
                    ["2027", "2028"], ["T01", "T04"], "description",
                    "고교학점제 10분 총정리. 해시태그상 2027 대상 표기."),
    "I8mxgl7gIJY": ("ENTRANCE_MEDIA", "TIER_2", None, "진학스토리(현직 교사)",
                    ["2028"], ["T05", "T10"], "description(hashtag_claims)",
                    "2028 시행계획 분석. 해시태그로 결론(선발기조 변화 없음·수시 비율 역대 최고)을 표기."),
    "7eX6tJajx50": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "윤윤구", "EBSi 입시 대표 강사",
                    ["2028"], ["T01", "T02", "T03"], "description",
                    "5등급제·고교학점제·통합수능 사용설명서. 지역의사제 언급."),
    "Eu4Iuykea_U": ("PRIVATE_CONSULTING", "TIER_3", "4인 패널", "올인원에듀 X 대치 IDA",
                    ["2028"], ["T03", "T04", "T08", "T10"], "chapters+desc_timestamps",
                    "O/X 팩트체크 형식. 질문별로 전문가 의견이 갈리는 항목을 명시."),
    "UwvIsK7OIAs": ("PUBLIC_EDUCATION_BROADCAST", "TIER_1", "윤상형", "서울 영동고등학교 교사",
                    ["2028"], ["T01", "T05"], "description",
                    "수시·정시 경계 붕괴와 '올라운더' 요구."),
    "v1fnEY4j0SI": ("PRIVATE_CONSULTING", "TIER_3", None, "댓츠원 That's One",
                    ["2027", "2028"], ["T10", "T02", "T05"], "description",
                    "2027/2028 구조 비교 정리."),
    "gy5YTq_7jRc": ("EDUCATION_JOURNALISM", "TIER_3", "윤여정", "입시 컨설턴트(20년 경력)",
                    ["2028"], ["T05", "T08"], "chapters+desc_timestamps",
                    "합격 패턴·학군지 vs 비학군지 전략. 저서 홍보 포함."),
    "YCauyl7CywI": ("INDIVIDUAL_EXPERT", "TIER_2", "정성민", "전 서울대 입학관리본부 입학사정관",
                    ["2028"], ["T06", "T03"], "description",
                    "모집단위별 권장과목과 교과전형 학생부 반영의 연결."),
    "zCcPLGMHW_M": ("PUBLIC_EDUCATION_BROADCAST", "TIER_1", "유태혁", "서울 세화여자고등학교 교사",
                    ["2027"], ["T10", "T05"], "description(전문 텍스트)",
                    "2027 하이브리드 평가 사례(성균관대 사대·동국대 다군)와 2027 일정."),
    "4v0uAOo-my0": ("ENTRANCE_MEDIA", "TIER_2", "이해웅", "입시탐탐 소장",
                    ["2028"], ["T03", "T09"], "chapters",
                    "학종=정성평가의 정의와 연세대 3역량 평가기준. 학종 비중 23.7% 수치 제시."),
    # ---- 2025 ----
    "gJ4LwkOHRIo": ("ACADEMY_NETWORK", "TIER_3", "이종환", "대치명인학원 입시센터 소장",
                    ["2028"], ["T08", "T06", "T09"], "chapters+desc_timestamps",
                    "의대·SKY 합격 마지노선 '예측'. 2028 환산 근거가 컨설턴트 자체 추정."),
    "pvgPSsXOWw8": ("INDIVIDUAL_EXPERT", "TIER_2", "정성민", "전 서울대 입학관리본부 입학사정관",
                    ["2028"], ["T10", "T02"], "description",
                    "'수능 체제 변경 = 재수 불리' 속설 반론."),
    "GBkQGejpRTY": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", None, "EBSi 설명회(입시)",
                    ["2027", "2028"], ["T07", "T02"], "description",
                    "겨울방학 대비 학습전략설명회. 자료집은 EBSi 링크."),
    "vZxkVqzioVo": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", None, "EBSi 설명회(통합사회)",
                    ["2027"], ["T07"], "metadata_only",
                    "2027학년도 수능 대비 통합사회. 내용 분석 불가."),
    "2KrOPWG1Rnk": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", None, "EBSi 설명회(통합과학)",
                    ["2028"], ["T07"], "metadata_only",
                    "2028학년도 수능 대비 통합과학. 내용 분석 불가."),
    "STa_uExYsXo": ("INDIVIDUAL_CREATOR", "TIER_3", "미미미누", "교육 콘텐츠 크리에이터",
                    ["2028"], ["T09", "T05"], "description",
                    "서울대·경희대 2028 전형계획 주요사항 리뷰(학생 관점)."),
    "jQamVq7EPc8": ("AI_STUDY_PLATFORM", "TIER_3", None, "스터디코드",
                    ["2028"], ["T01"], "description",
                    "2028 변화 요약 카드형 콘텐츠. 내용 분석 불가."),
    "35SXMjOGJ3o": ("PUBLIC_EDUCATION_BROADCAST", "TIER_1", "이재영", "서울 면목고등학교 교사",
                    ["2028"], ["T04", "T06"], "description",
                    "선택과목 중요성·우선순위 정하기(EBS 입시의 정석)."),
    "TnpTvofuaIU": ("PUBLIC_EDUCATION_BROADCAST", "TIER_1", "이재영", "서울 면목고등학교 교사",
                    ["2028"], ["T04", "T06", "T03"], "description(전문 텍스트)",
                    "권장 과목 발표 대학 14곳과 계열별 권장 방식, 과목 선택 3기준."),
    "tMYV0rZsVVE": ("ENTRANCE_MEDIA", "TIER_2", None, "진학티비(입시시그널)",
                    ["2028"], ["T06", "T04"], "chapters+desc_timestamps",
                    "경희대·숙명여대 권장과목 자료를 직접 링크. Q&A형."),
    "XOgxCtjTMTs": ("INDIVIDUAL_EXPERT", "TIER_2", "정성민", "전 서울대 입학관리본부 입학사정관",
                    ["2028"], ["T06", "T04"], "description",
                    "서울대 권장과목 발표의 전국 파급 해석."),
    "FICQ3_r5rFY": ("BROADCAST_ENTERTAINMENT", "TIER_3", "조정식·정승제", "입시 방송 출연 강사",
                    ["2028"], ["T03", "T08"], "chapters+desc_timestamps",
                    "예능형 채널A 티처스2 하이라이트. redistributed 제한(무단 전재·AI학습 이용 금지 명시)."),
    "O4gD4WtbhpE": ("ACADEMY_LECTURER", "TIER_3", "배인영", "대치동 통합사회 강사",
                    ["2028"], ["T07", "T02"], "description",
                    "통합사회 과목 선정·강좌 안내. 자체 자료 무료 공개 정책."),
    "0cvTxH2PF9Q": ("INDIVIDUAL_CREATOR", "TIER_3", None, "더 뉴튼 에듀",
                    ["2028"], ["T06"], "metadata_only",
                    "서울대 권장과목 발표에 대한 짧은 평. 내용 분석 불가."),
    "btH5sfpjxyc": ("ACADEMY_LECTURER", "TIER_3", "이지영", "이투스 사회탐구 강사",
                    ["2028"], ["T07", "T02"], "chapters+desc_timestamps",
                    "2028 통합사회 40분 25문항·배점 1.5/2/2.5점 변화 진술(공식 체제와 대조 필요)."),
    "dOqh4HYHtUM": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "윤윤구", "EBSi 입시 대표 강사",
                    ["2028"], ["T03", "T05"], "description",
                    "수능·내신 변별력 동시 하락 전제와 대학 평가 방식."),
    "6E5R_rdDcJA": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "윤윤구", "EBSi 입시 대표 강사",
                    ["2028"], ["T04", "T01"], "description",
                    "고1 선택과목 선정 전 점검. 고교학점제 첫 세대 대상."),
    "iuB_TnNRyi0": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "윤윤구", "EBSi 입시 대표 강사",
                    ["2028"], ["T02", "T03"], "description",
                    "'난이도 평이해질 2028 통합형 수능' 전제. 변별력 관련 해석."),
    "c98hNvBbo5w": ("ACADEMY_NETWORK", "TIER_3", "이만기", "KNS 소장(종로학원 출신)",
                    ["2028"], ["T03", "T01"], "chapters+desc_timestamps",
                    "성적 부풀리기·소인수 과목·표준편차 대체 자료 등 학생부 평가 구조."),
    "ZMqfXuUZrGY": ("INDIVIDUAL_CREATOR", "TIER_3", None, "방구선생",
                    ["2028"], ["T03", "T08"], "metadata_only",
                    "설명란이 비어 있어 5등급제 고교 티어별 대학 라인 주장의 근거를 확인할 수 없음. 분석 제외."),
    "ip0PWOIXkuE": ("ENTRANCE_MEDIA", "TIER_2", None, "진학티비(입시시그널)",
                    ["2028"], ["T01", "T02"], "description",
                    "2028 대입 개편 정리(고1 대상). 짧은 해설."),
    # ---- 2024/2023 ----
    "QiJI0RXM6SU": ("ACADEMY_NETWORK", "TIER_3", "김회식", "뉴파인 과학(HHKC상위1%교육)",
                    ["2028"], ["T01", "T04", "T07"], "description",
                    "2022 개정 교육과정 과학과목·고급 과목 선택 관점. 2024년 자료로 시점 노화."),
    "cREI4_PSq_M": ("PUBLIC_EDUCATION_BROADCAST", "TIER_1", "이주호 장관 외", "EBS 필통톡(교육부 제작지원)",
                    ["2028"], ["T01", "T02"], "description",
                    "2028 개편 '시안' 단계 토론(2023-10). 이후 확정안과 비교 필요 → OUTDATED 취급 항목 존재."),
    "x0gKYhh-OSY": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "한병훈·정유빈·원정의·박봄·양은혜", "EBSi 영역별 강사",
                    ["2028"], ["T07", "T02"], "description",
                    "2025-01-21 예비 고1 대상 2028 수능 개편 체제 발표 라이브."),
    "-YjeAAWwCZU": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "한병훈·정유빈·원정의", "EBSi 국어·수학·영어 강사",
                    ["2028"], ["T07", "T02"], "description",
                    "국어·수학·영어 체제 분석 및 커리큘럼. (x0gKYhh-OSY 1부 편집본)"),
    "ucHmFjaOIUs": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "박봄·양은혜", "EBSi 통합사회·통합과학 강사",
                    ["2028"], ["T07", "T02"], "description",
                    "통합사회·통합과학 체제 분석 및 커리큘럼. (x0gKYhh-OSY 2부 편집본)"),
    "ynp2pwjxZis": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "윤윤구", "EBSi 입시 대표 강사",
                    ["2028"], ["T01", "T04", "T03"], "description",
                    "고교학점제(절대평가+상대평가 병기) 첫 세대 설명."),
    "f3iPmLK14iQ": ("EBS_ENTRANCE_ENTERPRISE", "TIER_2", "윤윤구", "EBSi 입시 대표 강사",
                    ["2027", "2028"], ["T02", "T04", "T10"], "description",
                    "2027수능 vs 2028수능 비교와 고교 선택·선택과목."),
    "SQd3yG1ztcE_note": None,  # placeholder 제거용 (사용 안 함)
}
CURATED.pop("SQd3yG1ztcE_note", None)


def sha256(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default=os.path.join("..", "work"))
    ap.add_argument("--out", default=os.path.join("data", "youtube", "videos.json"))
    ap.add_argument("--analyses", default=os.path.join("data", "youtube", "analyses.json"))
    args = ap.parse_args()

    wm = json.load(open(os.path.join(args.work, "watch_meta.json"), encoding="utf-8"))
    dt = json.load(open(os.path.join(args.work, "details_raw.json"), encoding="utf-8"))

    rows, missing = [], []
    for vid, w in wm.items():
        d = dt.get(vid, {})
        cur = CURATED.get(vid)
        if not cur:
            missing.append(vid)
            continue
        kind, tier, person, role, years, topics, evidence, note = cur
        chapters = d.get("chapters") or []
        desc_ts = w.get("desc_timestamps") or []
        url = "https://www.youtube.com/watch?v=" + vid
        rows.append({
            "video_id": vid,
            "url": url,
            "url_hash": sha256(url),
            "title": d.get("title"),
            "channel": d.get("channel"),
            "channel_id": d.get("channelId"),
            "subscriber_text": d.get("subscriberText"),
            "channel_kind": kind,
            "reliability_tier": tier,
            "presenter": person,
            "presenter_role": role,
            "published_at": w.get("publishDate"),
            "upload_date": w.get("uploadDate"),
            "duration_sec": w.get("durationSec") or d.get("durationSec"),
            "view_count": w.get("viewCount") or d.get("viewCount"),
            "category": w.get("category"),
            "analyzed_academic_years": years,
            "topic_ids": topics,
            "content_evidence": evidence,
            "chapter_count": len(chapters),
            "desc_timestamp_count": len(desc_ts),
            "chapters": [{"title": c.get("title")} for c in chapters][:40],
            "timeline_anchors": [{"sec": t.get("sec"), "label": t.get("label")} for t in desc_ts][:40],
            "caption_tracks_listed": bool(w.get("caption_langs")),
            "caption_langs": w.get("caption_langs") or [],
            "caption_available": False,
            "caption_fetch_status": "BLOCKED_EMPTY_BODY(timedtext 200/0바이트)",
            "analysis_status": ("CONTENT_ANALYZED" if (w.get("description_len") or 0) >= 100 or len(chapters) > 0
                                else "METADATA_ONLY"),
            "content_class": "NON_OFFICIAL_RULE",
            "redistribution": "METADATA_PRIORITY",
            "access_method": "HTTP_STATIC",
            "verification_status": "NORMALIZED",
            "collected_at": COLLECTED_AT,
            "collector": "qoder-b",
            "analyst_note": note,
        })
    if args.analyses and os.path.exists(args.analyses):
        with open(args.analyses, encoding="utf-8") as f:
            extra = json.load(f)["analyses"]
        # video topic_ids = 큐레이터 1차 태그 ∪ 분석 항목이 부여한 태그(상담 검색 정합성 확보)
        by_vid = {r["video_id"]: r for r in rows}
        for a in extra:
            r = by_vid.get(a["video_id"])
            if not r:
                continue
            r["topic_ids"] = sorted(set(r["topic_ids"]) | set(a["topics"]))

    rows.sort(key=lambda r: (r["published_at"] or ""), reverse=True)

    by_status = {}
    for r in rows:
        by_status[r["analysis_status"]] = by_status.get(r["analysis_status"], 0) + 1
    payload = {
        "schema_version": "yt-v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collector": "qoder-b",
        "source_of_truth": "수집 스크립트(scripts/youtube) + 큐레이터 테이블(CURATED). 원문 자막은 커밋하지 않음.",
        "note_caption_limitation": (
            "본 네트워크에서는 YouTube timedtext 응답이 HTTP 200 + 본문 0바이트로 차단되어 "
            "(bot attestation 요구) 자막 전문을 확보할 수 없었다. 따라서 인용 근거는 "
            "영상 공식 설명란의 타임스탬프·챕터 제목과 채널 제공 요약문이며, "
            "content_evidence 필드에 확보 수준을 명시했다."
        ),
        "reliability_tier_definitions": TIERS,
        "counts": {
            "videos": len(rows),
            "by_analysis_status": by_status,
            "uncurated": missing,
        },
        "videos": rows,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")
    sys.stdout.buffer.write((
        "wrote %s videos=%d analyzed=%s metadata_only=%s uncurated=%s\n" % (
            args.out, len(rows), by_status.get("CONTENT_ANALYZED"),
            by_status.get("METADATA_ONLY"), len(missing))
    ).encode("utf-8"))
    if missing:
        sys.stdout.buffer.write(("UNCURATED: " + ",".join(missing) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
