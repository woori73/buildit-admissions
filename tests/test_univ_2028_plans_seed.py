"""대학별 2028 시행계획 지식 시드(build_univ_2028_plans_seed) 검사 — given/when/then."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import build_univ_2028_plans_seed as plans  # noqa: E402


def test_given_press_only_item_when_converted_then_it_is_held():
    # given: 언론 보도만 있는 주제
    it = {"topic": "susi_minimum", "text": "보도 기준", "source_url": "https://example.com/news", "source_kind": "press"}

    # when / then: 대학 세부 숫자는 원문만 싣는다
    assert plans.item_for("서강대학교", it) is None


def test_given_constructed_url_when_converted_then_it_is_held():
    # given: 검색 결과가 아니라 주소 규칙으로 만든 원문 주소
    url = next(iter(plans.HOLD_URLS))
    it = {"topic": "susi_types", "text": "원문", "source_url": url, "source_kind": "official"}

    # when / then
    assert plans.item_for("한국외국어대학교", it) is None


def test_given_official_item_when_converted_then_university_names_are_in_title_tags_and_content():
    # given
    it = {"topic": "susi_minimum", "text": "수시는 수능최저가 없다.", "source_url": "https://cdn013.negagea.net/한글.pdf",
          "source_kind": "official", "published": "2026-04-30", "source_title": "원문"}

    # when
    k = plans.item_for("서울대학교", it)

    # then: 대학 이름이 들어가야 대학을 말한 질문에서 제도 항목으로 찾힌다(policyNamesUniversity)
    assert k["id"] == "U2028-SNU-SUSI-MINIMUM"
    assert "서울대학교" in k["title"] and "서울대" in k["tags"] and k["content"].startswith("서울대학교 2028학년도")
    assert re.match(r"^https://[\x21-\x7e]+$", k["source_url"])


def test_given_built_seed_when_checked_then_ids_unique_and_only_official_items():
    # given / when
    seed = plans.build()
    ids = [k["id"] for k in seed["official_knowledge"]]

    # then
    assert ids and len(ids) == len(set(ids))
    assert all(k["academic_year"] == 2028 for k in seed["official_knowledge"])
    assert seed["ipsi_universities"]
