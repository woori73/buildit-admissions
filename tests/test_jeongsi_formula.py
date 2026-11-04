"""정시 수능 환산 계산식(jeongsi_formula/v1) 단위 테스트 (given/when/then). 실행: python3 -m unittest discover -s tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import jeongsi_formula as jf  # noqa: E402

ENG = {str(g): v for g, v in zip(range(1, 10), [100, 97, 90, 80, 65, 50, 30, 10, 0])}


def doc_with(formula: dict) -> dict:
    base = {"formula_id": "f1", "label": "자연계열", "document_key": "d1", "applies_to": {"type_names": ["정시 일반(가군)"]},
            "evidence_pages": [6], "raw_text": "원문", "tables": {}}
    base.update(formula)
    return {"schema": jf.SCHEMA, "university_key": "test", "university_name": "테스트대학교", "academic_year": 2027,
            "documents": [{"document_key": "d1", "file_url": "https://example.ac.kr/a.pdf"}], "formulas": [base]}


class EvaluateTest(unittest.TestCase):
    def test_given_max_ratio_formula_when_inputs_are_national_max_then_full_points(self):
        # given: 국어 300 × 취득/최고 + 영어 등급표
        expr = "KOR_STD / KOR_STD_MAX * 300 + table('ENG', ENG_GRD)"
        # when
        got = jf.evaluate(expr, {"KOR_STD": 139, "KOR_STD_MAX": 139, "ENG_GRD": 1}, {"ENG": ENG})
        # then
        self.assertAlmostEqual(got, 400.0)

    def test_given_two_type_formula_when_evaluated_then_higher_type_is_used(self):
        # given: A형·B형 중 높은 점수 반영
        expr = "max(KOR_STD * 1.1 + MATH_STD * 1.3, KOR_STD * 1.3 + MATH_STD * 1.1)"
        # when
        got = jf.evaluate(expr, {"KOR_STD": 130, "MATH_STD": 120})
        # then: A=143+156=299, B=169+132=301
        self.assertAlmostEqual(got, 301.0)

    def test_given_condition_bonus_when_science_taken_then_bonus_is_added(self):
        # given: 과학탐구 응시 과목 변환점수 3% 가산
        expr = "INQ1_CONV * cond(INQ1_SCI == 1, 1.03, 1)"
        # when
        sci = jf.evaluate(expr, {"INQ1_CONV": 70, "INQ1_SCI": 1})
        soc = jf.evaluate(expr, {"INQ1_CONV": 70, "INQ1_SCI": 0})
        # then
        self.assertAlmostEqual(sci, 72.1)
        self.assertAlmostEqual(soc, 70.0)

    def test_given_half_up_rounding_when_rounded_then_not_bankers_rounding(self):
        # given / when
        up = jf.evaluate("round(2.345, 2)", {})
        cut = jf.evaluate("trunc(2.349, 2)", {})
        # then
        self.assertAlmostEqual(up, 2.35)
        self.assertAlmostEqual(cut, 2.34)

    def test_given_top_sum_when_three_areas_then_best_two_summed(self):
        # given / when
        got = jf.evaluate("top_sum(2, KOR_PCT, MATH_PCT, INQ1_PCT)", {"KOR_PCT": 80, "MATH_PCT": 95, "INQ1_PCT": 90})
        # then
        self.assertAlmostEqual(got, 185.0)

    def test_given_low_sum_when_four_grades_then_best_three_summed(self):
        # given: 수능최저 "4개 영역 중 3개 합" — 등급은 작을수록 좋다
        expr = "low_sum(3, KOR_GRD, MATH_GRD, ENG_GRD, min(INQ1_GRD, INQ2_GRD)) <= 6"
        # when
        met = jf.evaluate(expr, {"KOR_GRD": 2, "MATH_GRD": 1, "ENG_GRD": 3, "INQ1_GRD": 4, "INQ2_GRD": 2})
        not_met = jf.evaluate(expr, {"KOR_GRD": 3, "MATH_GRD": 3, "ENG_GRD": 3, "INQ1_GRD": 4, "INQ2_GRD": 4})
        # then: 1+2+2=5 ≤ 6 충족, 3+3+3=9 미충족
        self.assertEqual(met, 1.0)
        self.assertEqual(not_met, 0.0)

    def test_given_missing_input_when_evaluated_then_error_names_variable(self):
        # given / when / then
        with self.assertRaisesRegex(jf.FormulaError, "KOR_STD"):
            jf.evaluate("KOR_STD * 2", {})

    def test_given_python_code_when_parsed_then_rejected(self):
        # given / when / then: 속성 접근·임의 함수는 허용하지 않는다
        for bad in ["__import__('os').system('x')", "KOR_STD.real", "open('a')", "[1,2]"]:
            with self.assertRaises(jf.FormulaError):
                jf.parse(bad)


class ValidateTest(unittest.TestCase):
    def test_given_valid_formula_with_matching_max_when_validated_then_no_errors(self):
        # given
        doc = doc_with({"expression": "KOR_STD / KOR_STD_MAX * 300 + table('ENG', ENG_GRD)", "tables": {"ENG": ENG},
                        "perfect_score_expected": 400})
        # when
        r = jf.validate_doc(doc, known_type_names={"정시 일반(가군)"})
        # then
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["formulas"][0]["pending_inputs"], ["KOR_STD_MAX"])

    def test_given_perfect_score_mismatch_when_validated_then_error(self):
        # given: 원문 만점 1000인데 식은 400까지만 나옴
        doc = doc_with({"expression": "KOR_STD / KOR_STD_MAX * 300 + table('ENG', ENG_GRD)", "tables": {"ENG": ENG},
                        "perfect_score_expected": 1000})
        # when
        r = jf.validate_doc(doc, known_type_names={"정시 일반(가군)"})
        # then
        self.assertTrue(any("만점" in e for e in r["errors"]))

    def test_given_unknown_variable_or_type_or_missing_grade_when_validated_then_errors(self):
        # given
        doc = doc_with({"expression": "KOREAN * 2 + table('ENG', ENG_GRD)", "tables": {"ENG": {"1": 100}},
                        "applies_to": {"type_names": ["없는 전형"]}})
        # when
        r = jf.validate_doc(doc, known_type_names={"정시 일반(가군)"})
        # then
        text = " ".join(r["errors"])
        self.assertIn("모르는 변수", text)
        self.assertIn("없는 전형명", text)
        self.assertIn("등급표 ENG", text)

    def test_given_department_not_in_2027_data_when_validated_then_error(self):
        # given
        doc = doc_with({"expression": "KOR_PCT", "applies_to": {"type_names": ["정시 일반(가군)"],
                                                                  "department_names": ["경영학부", "없는학과"]}})
        # when
        r = jf.validate_doc(doc, known_type_names={"정시 일반(가군)"}, known_department_names={"경영학부"})
        # then
        self.assertEqual([e for e in r["errors"] if "모집단위명" in e], ["f1: 2027 정시 자료에 없는 모집단위명 '없는학과'"])

    def test_given_official_example_when_validated_then_example_is_checked(self):
        # given: 원문 계산 예시(국어 표점 130, 최고 140 → 300×130/140 = 278.57)
        doc = doc_with({"expression": "round(KOR_STD / KOR_STD_MAX * 300, 2)",
                        "examples": [{"inputs": {"KOR_STD": 130, "KOR_STD_MAX": 140}, "expected": 278.57, "page": 7},
                                     {"inputs": {"KOR_STD": 130, "KOR_STD_MAX": 140}, "expected": 280, "page": 7}]})
        # when
        r = jf.validate_doc(doc, known_type_names={"정시 일반(가군)"})
        # then
        self.assertEqual([e["match"] for e in r["formulas"][0]["examples"]], [True, False])
        self.assertEqual(len(r["errors"]), 1)

    def test_given_uncovered_type_when_validated_then_warning_unless_reason_given(self):
        # given
        doc = doc_with({"expression": "KOR_PCT"})
        known = {"정시 일반(가군)", "정시 실기(나군)"}
        # when
        warned = jf.validate_doc(doc, known_type_names=known)
        doc["not_covered"] = {"정시 실기(나군)": "수능 미반영(실기 100%)"}
        silent = jf.validate_doc(doc, known_type_names=known)
        # then
        self.assertTrue(any("정시 실기(나군)" in w for w in warned["warnings"]))
        self.assertFalse(any("정시 실기(나군)" in w for w in silent["warnings"]))


if __name__ == "__main__":
    unittest.main()
