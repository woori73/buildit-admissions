"""수능최저 시드 빌더 단위 테스트 (given/when/then). 실행: python3 -m unittest discover -s tests"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import build_susi_minimum_seed as builder  # noqa: E402
import susi_minimum as sm  # noqa: E402

HANYANG = os.path.join(sm.MINIMUM_DIR, "hanyang_2027_susi_minimum.json")
BASE = {"ipsi_universities": [{"university_code": "HANYANG", "name": "한양대학교(서울)", "region": "서울"}],
        "ipsi_documents": [{"document_key": "doc_hanyang_2027_susi", "document_name": "한양대학교 2027학년도 수시모집 요강 - 수시 모집인원 총괄표"}]}


def write_tmp(doc: dict) -> str:
    fd, path = tempfile.mkstemp(suffix="_2027_susi_minimum.json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    return path


class BuildSusiSeedTest(unittest.TestCase):
    def test_given_rules_and_no_minimum_when_built_then_both_kinds_link_existing_material(self):
        # given
        with open(HANYANG, encoding="utf-8") as f:
            doc = json.load(f)
        # when
        seed = builder.build([HANYANG], BASE)
        # then
        kinds = [r["rule_kind"] for r in seed["susi_minimums"]]
        self.assertEqual(kinds.count("RULE"), len(doc["rules"]))
        self.assertEqual(kinds.count("NO_MINIMUM"), len(doc["no_minimum"]))
        self.assertTrue(all(r["source_document_key"] == "doc_hanyang_2027_susi" for r in seed["susi_minimums"]))
        nomin = [r for r in seed["susi_minimums"] if r["rule_kind"] == "NO_MINIMUM" and r["label"] == "학생부종합(서류형)"][0]
        self.assertEqual(nomin["evidence_pages"], [32])
        self.assertEqual(len({r["rule_key"] for r in seed["susi_minimums"]}), len(seed["susi_minimums"]))

    def test_given_gap_only_file_when_built_then_university_is_skipped(self):
        # given
        doc = {"schema": sm.SCHEMA, "university_key": "hanyang", "university_name": "한양대학교(서울)", "academic_year": 2027,
               "rules": [], "gaps": [{"item": "원문", "reason": "robots 차단", "url": "https://example.ac.kr"}]}
        # when
        seed = builder.build([write_tmp(doc)], BASE)
        # then
        self.assertEqual(seed["susi_minimums"], [])

    def test_given_invalid_rule_when_built_then_build_stops(self):
        # given: 부등호를 거꾸로 적은 규칙
        with open(HANYANG, encoding="utf-8") as f:
            doc = json.load(f)
        doc["rules"][0]["condition"] = doc["rules"][0]["condition"].replace("<= 7", ">= 7")
        # when / then
        with self.assertRaises(builder.BuildError):
            builder.build([write_tmp(doc)], BASE)

    def test_given_university_missing_from_base_when_built_then_build_stops(self):
        with self.assertRaisesRegex(builder.BuildError, "찾지 못함"):
            builder.build([HANYANG], {"ipsi_universities": [], "ipsi_documents": []})


if __name__ == "__main__":
    unittest.main()
