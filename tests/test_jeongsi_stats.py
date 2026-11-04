"""수능 최고점·변환표준점수 검증과 시드 빌더 단위 테스트 (given/when/then). 실행: python3 -m unittest discover -s tests"""
import copy
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import build_jeongsi_stats_seed as builder  # noqa: E402
import jeongsi_stats as js  # noqa: E402

SOURCE = {"institution_name": "한국교육과정평가원", "document_name": "2027학년도 수능 채점 결과",
          "file_url": "https://www.example.kr/scores.pdf"}
STD = {"schema": js.STD_MAX_SCHEMA, "academic_year": 2027, "source": SOURCE, "evidence_pages": [3],
       "areas": {"KOR": 147, "MATH": 139},
       "inquiry": [{"subject": "생활과 윤리", "track": "SOC", "std_max": 73},
                   {"subject": "물리학Ⅰ", "track": "SCI", "std_max": 72}]}
SCORES = {str(p): round(40 + p * 0.3, 2) for p in range(101)}
CONV = {"schema": js.CONVERSION_SCHEMA, "university_key": "yonsei", "university_name": "연세대학교", "academic_year": 2027,
        "source": {"institution_name": "연세대학교 입학처", "document_name": "2027 정시 탐구 변환표준점수",
                   "source_page_url": "https://admission.example.ac.kr/notice/1"},
        "tables": [{"track": "SOC", "label": "사회탐구", "scores": SCORES, "evidence_pages": [1]}]}
BASE = {"ipsi_universities": [{"university_code": "YONSEI", "name": "연세대학교", "region": "서울"}], "ipsi_documents": []}


def write_tmp(doc: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    return path


class StdMaxValidationTest(unittest.TestCase):
    def test_given_complete_values_when_validated_then_published(self):
        # when
        r = js.validate_std_max(STD)
        # then
        self.assertEqual(r["errors"], [])
        self.assertTrue(r["published"])

    def test_given_values_not_yet_announced_when_validated_then_not_published_without_error(self):
        # given: 발표 전 — 값이 모두 null
        doc = copy.deepcopy(STD)
        doc["areas"] = {"KOR": None, "MATH": None}
        for s in doc["inquiry"]:
            s["std_max"] = None
        # when
        r = js.validate_std_max(doc)
        # then
        self.assertEqual(r["errors"], [])
        self.assertFalse(r["published"])

    def test_given_unknown_track_or_out_of_range_when_validated_then_errors(self):
        # given
        doc = copy.deepcopy(STD)
        doc["inquiry"][0]["track"] = "사탐"
        doc["areas"]["KOR"] = 250
        # when
        r = js.validate_std_max(doc)
        # then
        self.assertTrue(any("track" in e for e in r["errors"]))
        self.assertTrue(any("범위" in e for e in r["errors"]))


class ConversionValidationTest(unittest.TestCase):
    def test_given_full_monotonic_table_when_validated_then_no_error(self):
        self.assertEqual(js.validate_conversion(CONV)["errors"], [])

    def test_given_missing_percentile_when_validated_then_error(self):
        # given
        doc = copy.deepcopy(CONV)
        del doc["tables"][0]["scores"]["37"]
        # when
        r = js.validate_conversion(doc)
        # then
        self.assertTrue(any("백분위 빠짐" in e for e in r["errors"]))

    def test_given_lower_percentile_with_higher_score_when_validated_then_error(self):
        # given: 백분위 50 점수가 백분위 51보다 큼
        doc = copy.deepcopy(CONV)
        doc["tables"][0]["scores"]["50"] = 99
        # when
        r = js.validate_conversion(doc)
        # then
        self.assertTrue(any("위 백분위보다 큼" in e for e in r["errors"]))


class BuildStatsSeedTest(unittest.TestCase):
    def test_given_published_std_max_and_table_when_built_then_rows_link_documents(self):
        # when
        seed = builder.build([write_tmp(STD), write_tmp(CONV)], BASE)
        # then
        keys = [r["subject_key"] for r in seed["csat_std_max"]]
        self.assertEqual(keys, ["KOR", "MATH", "INQ:생활과 윤리", "INQ:물리학Ⅰ"])
        self.assertEqual(seed["conversion_scores"][0]["university_code"], "YONSEI")
        self.assertEqual(len(seed["conversion_scores"][0]["scores"]), 101)
        doc_keys = {d["document_key"] for d in seed["ipsi_documents"]}
        self.assertEqual(doc_keys, {"doc_kice_2027_csat_scores", "doc_yonsei_2027_jeongsi_conversion"})

    def test_given_unpublished_std_max_when_built_then_skipped(self):
        # given
        doc = copy.deepcopy(STD)
        doc["areas"]["KOR"] = None
        # when
        seed = builder.build([write_tmp(doc)], BASE)
        # then
        self.assertEqual(seed["csat_std_max"], [])

    def test_given_invalid_table_when_built_then_build_stops(self):
        # given
        doc = copy.deepcopy(CONV)
        doc["tables"][0]["scores"]["10"] = 199
        # when / then
        with self.assertRaises(builder.BuildError):
            builder.build([write_tmp(doc)], BASE)


if __name__ == "__main__":
    unittest.main()
