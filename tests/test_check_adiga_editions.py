"""모집요강 판 대조(check_adiga_editions) 단위 테스트 (given/when/then). 실행: python3 -m unittest discover -s tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import check_adiga_editions as ce  # noqa: E402


def parsed(types=None, departments=None, schedules=None):
    return {"admission_types": types or [], "departments": departments or [], "schedules": schedules or []}


PAGE_TABLE = "전형별 모집인원\n학생부교과(지역균형전형)\n전자공학과 16\n경영학부 20\n합계 36\n"
PAGE_SCHEDULE = "원서접수 2026. 9. 8.(화) 10:00 ~ 9. 11.(금) 17:00\n"


class NormalizeTest(unittest.TestCase):
    def test_given_name_split_across_lines_when_normalized_then_matches(self):
        # given
        text = ce.norm("정치행정학부\n(정치외교학전공)")
        # when
        found = ce.name_found("정치행정학부(정치외교학전공)", text)
        # then
        self.assertTrue(found)

    def test_given_group_suffix_when_name_found_then_group_is_ignored(self):
        # given
        text = ce.norm("정시 일반전형 수능위주 모집인원")
        # when / then
        self.assertTrue(ce.name_found("정시 일반전형 수능위주(가군)", text))

    def test_given_korean_date_formats_when_tokenized_then_month_day_pairs(self):
        # given / when
        toks = ce.date_tokens("2026. 9. 8.(화) ~ 9월 11일")
        # then
        self.assertEqual(toks, {(9, 8), (9, 11)})


class CheckTest(unittest.TestCase):
    def test_given_same_values_when_checked_then_no_candidates(self):
        # given
        p = parsed(types=[{"name": "학생부교과(지역균형전형)", "recruitment_count": 36}],
                   departments=[{"department": "전자공학과", "counts_by_type": {"학생부교과(지역균형전형)": 16}},
                                {"department": "경영학부", "counts_by_type": {"학생부교과(지역균형전형)": 20}}],
                   schedules=[{"item": "원서접수", "type_name": "전 전형", "date": "2026. 9. 8.(화) 10:00 ~ 9. 11.(금) 17:00"}])
        # when
        stats, cands = ce.check_parsed_against_pages(p, [PAGE_TABLE, PAGE_SCHEDULE])
        # then
        self.assertEqual(cands, {})
        self.assertEqual(stats["학과별 인원"], 2)

    def test_given_changed_department_count_when_checked_then_candidate(self):
        # given: 원문은 16명인데 구조화 값은 18명
        p = parsed(departments=[{"department": "전자공학과", "counts_by_type": {"학생부교과(지역균형전형)": 18}}])
        # when
        _, cands = ce.check_parsed_against_pages(p, [PAGE_TABLE])
        # then
        self.assertEqual(cands["학과별 인원"][0]["값"], 18)

    def test_given_changed_schedule_date_when_checked_then_candidate(self):
        # given: 원문 9.8인데 구조화 값 9.9
        p = parsed(schedules=[{"item": "원서접수", "type_name": "전 전형", "date": "2026. 9. 9.(수) 10:00"}])
        # when
        _, cands = ce.check_parsed_against_pages(p, [PAGE_SCHEDULE])
        # then
        self.assertEqual(cands["일정"][0]["없는 날짜"], [(9, 9)])

    def test_given_counts_split_by_group_when_sum_printed_then_accepted(self):
        # given: 원문은 합계 117만, 구조화는 가/나/다군 11·99·7
        page = "기회균형전형 농·어촌학생 117\n"
        types = [{"name": f"정시 기회균형전형-농·어촌학생({g}군)", "recruitment_count": c} for g, c in (("가", 11), ("나", 99), ("다", 7))]
        # when
        _, cands = ce.check_parsed_against_pages(parsed(types=types), [page])
        # then
        self.assertEqual(cands, {})

    def test_given_type_total_not_printed_when_departments_match_then_accepted(self):
        # given: 원문에 전형 합계 행이 없고 학과별 인원만 있음
        page = "논술우수자전형\n전자공학과 16\n경영학부 20\n"
        p = parsed(types=[{"name": "논술우수자전형", "recruitment_count": 36}],
                   departments=[{"department": "전자공학과", "counts_by_type": {"논술우수자전형": 16}},
                                {"department": "경영학부", "counts_by_type": {"논술우수자전형": 20}}])
        # when
        _, cands = ce.check_parsed_against_pages(p, [page])
        # then
        self.assertEqual(cands, {})

    def test_given_department_split_humanities_science_when_sum_matches_then_accepted(self):
        # given: 원문은 인문 7 + 자연 73, 구조화는 학부 합계 80
        page = "컴퓨터·AI학부(인문) 7\n컴퓨터·AI학부(자연) 73\n"
        p = parsed(departments=[{"department": "컴퓨터·AI학부", "counts_by_type": {"정시 일반전형(나군)": 80}}])
        # when
        _, cands = ce.check_parsed_against_pages(p, [page])
        # then
        self.assertEqual(cands, {})


if __name__ == "__main__":
    unittest.main()
