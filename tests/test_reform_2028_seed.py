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
