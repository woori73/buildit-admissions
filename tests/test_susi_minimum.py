"""수시 수능최저학력기준(susi_minimum/v1) 단위 테스트 (given/when/then). 실행: python3 -m unittest discover -s tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import susi_minimum as sm  # noqa: E402

THREE_SUM_6 = "low_sum(3, KOR_GRD, MATH_GRD, ENG_GRD, min(INQ1_GRD, INQ2_GRD)) <= 6"
TYPES = {"학생부교과(추천형)", "논술우수자", "학생부종합(서류형)"}


def doc_with(rule: dict, **extra) -> dict:
    base = {"rule_id": "r1", "label": "전체", "document_key": "d1", "applies_to": {"type_names": ["학생부교과(추천형)"]},
            "condition": THREE_SUM_6, "evidence_pages": [12], "raw_text": "3개 영역 등급 합 6 이내"}
    base.update(rule)
    doc = {"schema": sm.SCHEMA, "university_key": "test", "university_name": "테스트대학교", "academic_year": 2027,
           "documents": [{"document_key": "d1", "file_url": "https://example.ac.kr/susi.pdf"}], "rules": [base],
           "no_minimum": {"학생부종합(서류형)": "수능최저학력기준 미적용(10쪽)"}, "not_covered": {"논술우수자": "원문 확인 중"}}
    doc.update(extra)
    return doc


class ValidateTest(unittest.TestCase):
    def test_given_valid_rule_when_validated_then_no_errors_or_warnings(self):
        # given / when
        r = sm.validate_doc(doc_with({}), known_type_names=TYPES, known_department_names=set())
        # then
        self.assertEqual(r["errors"], [])
        self.assertEqual(r["warnings"], [])

    def test_given_condition_using_scores_when_validated_then_error(self):
        # given: 수능최저는 등급만 쓴다
        r = sm.validate_doc(doc_with({"condition": "KOR_STD >= 120"}), known_type_names=TYPES, known_department_names=set())
        # then
        self.assertTrue(any("쓰지 않는 변수" in e for e in r["errors"]))

    def test_given_inverted_condition_when_validated_then_sanity_error(self):
        # given: 부등호를 거꾸로 적은 실수
        r = sm.validate_doc(doc_with({"condition": "low_sum(3, KOR_GRD, MATH_GRD, ENG_GRD) >= 6"}),
                            known_type_names=TYPES, known_department_names=set())
        # then
        self.assertTrue(any("등급 1인 학생이 미충족" in e for e in r["errors"]))

    def test_given_type_missing_from_all_lists_when_validated_then_warning(self):
        # given
        doc = doc_with({}, not_covered={})
        # when
        r = sm.validate_doc(doc, known_type_names=TYPES, known_department_names=set())
        # then
        self.assertTrue(any("논술우수자" in w for w in r["warnings"]))

    def test_given_unknown_type_name_when_validated_then_error(self):
        # given / when
        r = sm.validate_doc(doc_with({"applies_to": {"type_names": ["없는 전형"]}}), known_type_names=TYPES,
                            known_department_names=set())
        # then
        self.assertTrue(any("없는 전형" in e for e in r["errors"]))

    def test_given_official_example_when_validated_then_it_is_checked(self):
        # given: 원문 예시 — 국2 수1 영3 탐4·2 → 1+2+2=5 충족
        ex_ok = {"inputs": {"KOR_GRD": 2, "MATH_GRD": 1, "ENG_GRD": 3, "INQ1_GRD": 4, "INQ2_GRD": 2}, "expected_met": True}
        ex_bad = {"inputs": {"KOR_GRD": 2, "MATH_GRD": 1, "ENG_GRD": 3, "INQ1_GRD": 4, "INQ2_GRD": 2}, "expected_met": False}
        # when
        ok = sm.validate_doc(doc_with({"examples": [ex_ok]}), known_type_names=TYPES, known_department_names=set())
        bad = sm.validate_doc(doc_with({"examples": [ex_bad]}), known_type_names=TYPES, known_department_names=set())
        # then
        self.assertEqual(ok["errors"], [])
        self.assertTrue(any("예시 0" in e for e in bad["errors"]))


class CheckTest(unittest.TestCase):
    def test_given_grades_when_checked_then_met_or_not_met(self):
        # given
        rule = {"condition": THREE_SUM_6 + " and HIST_GRD <= 4"}
        # when
        met = sm.check(rule, {"KOR_GRD": 2, "MATH_GRD": 2, "ENG_GRD": 2, "INQ1_GRD": 3, "INQ2_GRD": 5, "HIST_GRD": 3})
        hist_fail = sm.check(rule, {"KOR_GRD": 2, "MATH_GRD": 2, "ENG_GRD": 2, "INQ1_GRD": 3, "INQ2_GRD": 5, "HIST_GRD": 5})
        # then
        self.assertEqual(met["outcome"], "MET")
        self.assertEqual(hist_fail["outcome"], "NOT_MET")

    def test_given_missing_grade_when_checked_then_needs_input_lists_it(self):
        # given / when
        r = sm.check({"condition": THREE_SUM_6}, {"KOR_GRD": 2, "MATH_GRD": 2, "ENG_GRD": 2})
        # then
        self.assertEqual(r, {"outcome": "NEEDS_INPUT", "missing": ["INQ1_GRD", "INQ2_GRD"]})

    def test_given_science_required_rule_when_social_student_checks_then_not_met(self):
        # given: 과탐 2과목 응시 필수 — 선택 표시가 없으면 0으로 본다
        rule = {"condition": "INQ1_SCI == 1 and INQ2_SCI == 1 and " + THREE_SUM_6}
        grades = {"KOR_GRD": 1, "MATH_GRD": 1, "ENG_GRD": 1, "INQ1_GRD": 1, "INQ2_GRD": 1}
        # when
        social = sm.check(rule, grades)
        science = sm.check(rule, {**grades, "INQ1_SCI": 1, "INQ2_SCI": 1})
        # then
        self.assertEqual(social["outcome"], "NOT_MET")
        self.assertEqual(science["outcome"], "MET")


if __name__ == "__main__":
    unittest.main()
