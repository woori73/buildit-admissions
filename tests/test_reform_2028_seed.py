"""2028 대입 개편 상담 근거 시드(build_reform_2028_seed) 검사 — given/when/then."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import build_reform_2028_seed as reform  # noqa: E402

SEED_PATH = reform.OUT


def test_given_built_seed_when_inspected_then_loader_required_keys_exist():
    # given / when
    seed = reform.build()

    # then: 적재 API는 비어 있지 않은 ipsi_universities를 요구한다
    assert seed["ipsi_universities"] and seed["ipsi_universities"][0]["name"] == "서울대학교"
    assert seed["official_knowledge"] and seed["youtube_knowledge"]


def test_given_items_when_checked_then_ids_unique_and_fields_filled():
    # given
    seed = reform.build()
    items = seed["official_knowledge"] + seed["youtube_knowledge"]

    # when
    ids = [it["id"] for it in items]

    # then
    assert len(ids) == len(set(ids))
    for it in items:
        assert it["academic_year"] == 2028
        assert it["title"].strip() and it["content"].strip() and it["tags"].strip()
        assert re.match(r"^https://", it["source_url"])


def test_given_youtube_items_when_checked_then_ids_do_not_collide_with_video_analyses():
    # given: 서버 dedupKey는 youtube:{id}라 data/youtube 분석(YT-A###)과 겹치면 덮어쓴다
    seed = reform.build()

    # when
    ids = [it["id"] for it in seed["youtube_knowledge"]]

    # then
    assert all(not i.startswith("YT-") for i in ids)


def test_given_official_items_when_checked_then_no_unverified_conversion_or_ratio_numbers():
    # given: 원문으로 확인하지 못한 환산표·대학별 정시 반영 비율은 넣지 않는다
    seed = reform.build()

    # when
    text = " ".join(it["content"] for it in seed["official_knowledge"])

    # then
    assert "3.4등급" not in text
    assert not re.search(r"학생부\s*\d+\s*%", text)


def test_given_written_seed_when_compared_then_matches_builder_items():
    # given: 저장소에 커밋된 시드가 빌더 내용과 같아야 한다
    with open(SEED_PATH, encoding="utf-8") as f:
        saved = json.load(f)

    # when
    built = reform.build()

    # then
    assert saved["official_knowledge"] == built["official_knowledge"]
    assert saved["youtube_knowledge"] == built["youtube_knowledge"]


def test_given_added_items_when_built_then_score_credit_courses_med_and_plan_items_exist():
    # given: 2026-11-22 추가 항목(성적 표기·학점 이수·학생부 반영·권장과목·지역의사·2029 기본사항·국가교육발전계획)
    seed = reform.build()

    # when
    ids = {it["id"] for it in seed["official_knowledge"]}

    # then
    assert {"R2028-CSAT-SCORE", "R2028-CREDIT-PASS", "R2028-RECORD-ITEMS", "R2028-SNU-COURSES",
            "R2028-RECOMMENDED-STATS", "R2028-MED-REGIONAL", "R2029-BASICS", "R2028-NATIONAL-PLAN"} <= ids


def test_given_undecided_policy_when_written_then_marked_not_confirmed():
    # given: 국가교육발전계획 대입 논의는 확정되지 않았다
    item = next(it for it in reform.build()["official_knowledge"] if it["id"] == "R2028-NATIONAL-PLAN")

    # when / then: '확정 아님'을 제목과 본문에 함께 적는다
    assert "확정 아님" in item["title"]
    assert "확정된 제도가 아니" in item["content"]


def test_given_csat_date_items_when_built_then_exam_and_score_dates_match_moe_announcements():
    # given: 2026-11-23 추가 — 교육부 발표 수능 시험일(2028: 2025-06-02 발표, 2029: 2026-08-18 발표)
    seed = reform.build()
    by_id = {it["id"]: it for it in seed["official_knowledge"]}

    # when
    csat2028 = by_id["R2028-CSAT-DATE"]["content"]
    csat2029 = by_id["R2029-CSAT-DATE"]["content"]

    # then
    assert "2027년 11월 18일(목)" in csat2028 and "2027년 12월 10일(금)" in csat2028
    assert "2028년 11월 16일(목)" in csat2029 and "2028년 12월 8일(금)" in csat2029


def test_given_national_plan_item_when_built_then_delay_of_draft_is_stated():
    # given: 국가교육위원회가 2026-10-21 시안 발표를 미룸(연내 공개, 2027년 3월 말 확정 방침 유지)
    seed = reform.build()
    plan = next(it for it in seed["official_knowledge"] if it["id"] == "R2028-NATIONAL-PLAN")["content"]

    # when / then
    assert "2026-10-21" in plan and "연내" in plan and "확정 예정이며" not in plan
