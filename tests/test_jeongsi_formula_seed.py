"""정시 계산식 시드 빌더 단위 테스트 (given/when/then). 실행: python3 -m unittest discover -s tests"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import build_jeongsi_formula_seed as builder  # noqa: E402
import jeongsi_formula as jf  # noqa: E402

UOS = os.path.join(jf.FORMULA_DIR, "uos_2027_jeongsi_formula.json")
BASE = {"ipsi_universities": [{"university_code": "UOS", "name": "서울시립대학교", "region": "서울"}],
        "ipsi_documents": [{"document_key": "doc_uos_2027_jeongsi", "document_name": "서울시립대학교 2027학년도 정시모집 신입생 모집요강"}]}


def write_tmp(doc: dict) -> str:
    fd, path = tempfile.mkstemp(suffix="_2027_jeongsi_formula.json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False)
    return path


class BuildSeedTest(unittest.TestCase):
    def test_given_valid_formula_file_when_built_then_seed_links_existing_material_and_conformance_has_two_cases(self):
        # given
        with open(UOS, encoding="utf-8") as f:
            n = len(json.load(f)["formulas"])
        # when
        seed, conf = builder.build([UOS], BASE)
        # then
        self.assertEqual(len(seed["jeongsi_formulas"]), n)
        self.assertEqual(seed["ipsi_documents"][0]["document_name"], "서울시립대학교 2027학년도 정시모집 신입생 모집요강")
        self.assertTrue(all(f["source_document_key"] == "doc_uos_2027_jeongsi" for f in seed["jeongsi_formulas"]))
        self.assertEqual(len(conf), 2 * n)
        perfect = [c for c in conf if c["formula_key"] == "UOS:uos_hum1" and c["case"] == "perfect"][0]
        self.assertAlmostEqual(perfect["expected"], 1000.0)

    def test_given_file_with_validation_error_when_built_then_build_stops(self):
        # given: 표가 빠진 계산식
        with open(UOS, encoding="utf-8") as f:
            doc = json.load(f)
        doc["formulas"][0]["tables"] = {}
        path = write_tmp(doc)
        # when / then
        with self.assertRaises(builder.BuildError):
            builder.build([path], BASE)

    def test_given_file_without_formulas_when_built_then_university_is_skipped(self):
        # given: 원문 미확보 대학
        doc = {"schema": jf.SCHEMA, "university_key": "uos", "university_name": "서울시립대학교", "academic_year": 2027,
               "formulas": [], "gaps": [{"item": "원문", "reason": "robots 차단", "url": "https://example.ac.kr"}]}
        path = write_tmp(doc)
        # when
        seed, conf = builder.build([path], BASE)
        # then
        self.assertEqual(seed["ipsi_universities"], [])
        self.assertEqual(conf, [])

    def test_given_university_missing_from_base_seed_when_built_then_build_stops(self):
        # given / when / then: 엉뚱한 대학을 새로 만들지 않도록 기존 시드에 없으면 멈춘다
        with self.assertRaisesRegex(builder.BuildError, "찾지 못함"):
            builder.build([UOS], {"ipsi_universities": [], "ipsi_documents": []})

    def test_given_needs_review_formula_when_built_then_reason_is_carried(self):
        # given
        with open(UOS, encoding="utf-8") as f:
            doc = json.load(f)
        doc["formulas"][0]["needs_review"] = {"reason": "대학 확인 필요"}
        path = write_tmp(doc)
        # when
        seed, _ = builder.build([path], BASE)
        # then
        self.assertEqual(seed["jeongsi_formulas"][0]["needs_review_reason"], "대학 확인 필요")
        self.assertEqual(seed["counts"]["needs_review"], 1)


if __name__ == "__main__":
    unittest.main()
