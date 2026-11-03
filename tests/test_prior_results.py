"""지난해 입시결과 수집·시드 빌드 단위 테스트 (given/when/then). 실행: python3 -m unittest discover -s tests"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import build_prior_results_seed as builder  # noqa: E402
import ipsi_fetch  # noqa: E402


class FakeResp:
    def __init__(self, status, text="", ctype="text/plain"):
        self.status_code = status
        self.text = text
        self.headers = {"Content-Type": ctype}


class RedirectGateTest(unittest.TestCase):
    def test_given_allowed_url_redirecting_to_disallowed_path_when_fetched_then_redirect_is_not_followed(self):
        # given: /admission/html/ 은 허용, /error_new/ 는 robots 비허용
        robots = FakeResp(200, "User-agent: *\nDisallow: /error_new/\n")
        redirect = FakeResp(302, "", "text/html")
        redirect.headers["Location"] = "/error_new/error.html"
        redirect.url = "https://ibhak.example.ac.kr/admission/html/"
        redirect.content = b""
        session = mock.Mock()
        session.get.side_effect = [robots, redirect]
        with tempfile.TemporaryDirectory() as d:
            fetcher = ipsi_fetch.IpsiFetcher(store_raw=False, delay=0, raw_dir=d, meta_dir=d)
            fetcher._session = session
            fetcher.gate = ipsi_fetch.RobotsGate(session)
            # when
            res = fetcher.fetch("https://ibhak.example.ac.kr/admission/html/", save_meta=False)
        # then: 비허용 경로는 요청하지 않는다(robots 1회 + 첫 요청 1회만)
        self.assertFalse(res.ok)
        self.assertFalse(res.robots_allowed)
        self.assertIn("redirect to robots-disallowed", res.error)
        self.assertEqual(session.get.call_count, 2)


class RobotsGateTest(unittest.TestCase):
    def gate(self, resp_or_exc):
        session = mock.Mock()
        if isinstance(resp_or_exc, Exception):
            session.get.side_effect = resp_or_exc
        else:
            session.get.return_value = resp_or_exc
        return ipsi_fetch.RobotsGate(session)

    def test_given_robots_fetch_error_when_checked_then_request_is_denied(self):
        # given
        gate = self.gate(ConnectionError("reset"))
        # when
        allowed = gate.allowed("https://ipsi.example.ac.kr/board")
        # then
        self.assertFalse(allowed)

    def test_given_robots_5xx_when_checked_then_request_is_denied(self):
        # given
        gate = self.gate(FakeResp(502, "bad gateway", "text/html"))
        # when / then
        self.assertFalse(gate.allowed("https://ipsi.example.ac.kr/board"))

    def test_given_no_robots_404_when_checked_then_request_is_allowed(self):
        # given
        gate = self.gate(FakeResp(404, "not found", "text/html"))
        # when / then
        self.assertTrue(gate.allowed("https://admission.example.ac.kr/data"))

    def test_given_firewall_block_page_as_robots_when_checked_then_request_is_denied(self):
        # given: robots.txt 자리에 HTTP 200 HTML 차단 안내
        gate = self.gate(FakeResp(200, "<html><body>웹 보안 정책에 위배되어 차단되었습니다.</body></html>", "text/html"))
        # when / then
        self.assertFalse(gate.allowed("https://ipsi.example.ac.kr/board"))

    def test_given_soft_404_html_as_robots_when_checked_then_request_is_allowed(self):
        # given: robots.txt 자리에 일반 HTML(없는 페이지 안내)
        gate = self.gate(FakeResp(200, "<!doctype html><html><body>페이지를 찾을 수 없습니다</body></html>", "text/html"))
        # when / then
        self.assertTrue(gate.allowed("https://admission.example.ac.kr/data"))

    def test_given_http_allowed_but_https_blocked_when_checked_then_each_scheme_is_judged_separately(self):
        # given: http robots는 400(규칙 없음 취급), https robots는 전면 차단
        session = mock.Mock()
        session.get.side_effect = [FakeResp(400, "bad request", "text/html"), FakeResp(200, "User-agent: *\nDisallow: /\n")]
        gate = ipsi_fetch.RobotsGate(session)
        # when
        http_ok = gate.allowed("http://ipsi.example.ac.kr/board")
        https_ok = gate.allowed("https://ipsi.example.ac.kr/board")
        # then: 같은 호스트라도 스킴마다 robots를 따로 확인한다
        self.assertTrue(http_ok)
        self.assertFalse(https_ok)
        self.assertEqual(session.get.call_count, 2)

    def test_given_disallow_all_when_checked_then_request_is_denied(self):
        # given
        gate = self.gate(FakeResp(200, "User-agent: *\nDisallow: /\n"))
        # when / then
        self.assertFalse(gate.allowed("https://admission.example.ac.kr/data"))


class RangeAndKeyTest(unittest.TestCase):
    def row(self, **kw):
        base = {"result_year": 2026, "round_type": "SUSI", "group": None, "type_name": "교과", "department_name": "국어국문학과",
                "metric_label": None, "metric_unit": None, "metric_value": None, "recruit_count": 10, "applicant_count": 100,
                "competition_rate": 10.0, "extra_admitted_count": None}
        base.update(kw)
        return base

    def test_given_values_in_range_when_checked_then_no_problem(self):
        # given / when / then
        self.assertIsNone(builder.range_problem(self.row()))
        self.assertIsNone(builder.range_problem(self.row(metric_label="교과등급 70%컷", metric_unit="GRADE", metric_value=2.31)))

    def test_given_out_of_range_values_when_checked_then_problem_is_reported(self):
        # given / when / then
        self.assertIsNotNone(builder.range_problem(self.row(metric_unit="GRADE", metric_value=9.5, metric_label="x")))
        self.assertIsNotNone(builder.range_problem(self.row(metric_unit="PERCENTILE", metric_value=101, metric_label="x")))
        self.assertIsNotNone(builder.range_problem(self.row(competition_rate=-1)))
        self.assertIsNotNone(builder.range_problem(self.row(recruit_count=3.5)))

    def test_given_different_metric_labels_when_keyed_then_keys_differ_and_same_row_keys_equal(self):
        # given
        a = self.row(metric_label="교과등급 50%컷")
        b = self.row(metric_label="교과등급 70%컷")
        # when / then
        self.assertNotEqual(builder.natural_key(a), builder.natural_key(b))
        self.assertEqual(builder.natural_key(a), builder.natural_key(dict(a)))


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        os.makedirs(os.path.join(d, "prior"))
        main = {"ipsi_universities": [{"code": "u14", "university_code": "U14", "name": "부산대학교"}],
                "ipsi_admission_types": [{"university_code": "U14", "academic_year": 2027, "type_name": "학생부교과(학생부교과전형)"}],
                "ipsi_departments": [{"university_code": "U14", "academic_year": "2027", "department_name": "국어국문학과"}]}
        with open(os.path.join(d, "main.json"), "w", encoding="utf-8") as f:
            json.dump(main, f, ensure_ascii=False)
        doc = {"document_key": "u14_2026_susi_result", "document_name": "2026 대입전형결과", "round_type": "SUSI",
               "institution_name": "부산대학교 입학처", "source_url": "https://go.pusan.ac.kr/x.pdf", "published_at": "2026-04-17"}
        rows = [
            {"round_type": "SUSI", "type_name": "학생부교과(학생부교과전형)", "department_name": "국어국문학과", "group": None,
             "metric_label": None, "metric_unit": None, "metric_value": None, "raw_value_text": None, "recruit_count": 8,
             "applicant_count": 156, "competition_rate": 19.5, "extra_admitted_count": 4,
             "source_document_key": "u14_2026_susi_result", "evidence_pages": [4]},
            {"round_type": "SUSI", "type_name": "학생부교과(학생부교과전형)", "department_name": "국어국문학과", "group": None,
             "metric_label": "교과종합등급 70%", "metric_unit": "GRADE", "metric_value": 3.24, "raw_value_text": "3.24",
             "recruit_count": None, "applicant_count": None, "competition_rate": None, "extra_admitted_count": None,
             "source_document_key": "u14_2026_susi_result", "evidence_pages": [4]}]
        src = {"university_key": "u14", "university_name": "부산대학교", "university_code": "U14", "result_year": 2026,
               "documents": [doc, {**doc, "document_key": "u14_unused", "document_name": "검증용"}], "rows": rows,
               "verification": {"spot_checks": [], "range_failures": 0}, "gaps": [{"item": "연제캠퍼스", "reason": "범위 밖"}]}
        with open(os.path.join(d, "prior", "u14_2026_prior.json"), "w", encoding="utf-8") as f:
            json.dump(src, f, ensure_ascii=False)
        self.patches = [mock.patch.object(builder, "PRIOR_DIR", os.path.join(d, "prior")),
                        mock.patch.object(builder, "MAIN_SEED", os.path.join(d, "main.json"))]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_given_reserve_rank_university_when_built_then_rank_moves_to_metric_row_and_count_is_null(self):
        # given: 부산대는 '최종 추합 번호'가 충원 인원 칸에 들어온다
        # when
        seed, per = builder.build(None)
        # then
        base = [r for r in seed["prior_results"] if r["metric_label"] is None][0]
        rank = [r for r in seed["prior_results"] if r["metric_label"] == "최종 추합 번호"][0]
        self.assertIsNone(base["extra_admitted_count"])
        self.assertEqual(rank["metric_value"], 4)
        self.assertEqual(per[0]["reserve_rank_moved_to_metric"], 1)

    def test_given_rows_when_built_then_documents_keys_links_and_sources_are_set(self):
        # when
        seed, per = builder.build(None)
        # then
        self.assertEqual([d["document_key"] for d in seed["ipsi_documents"]], ["doc_u14_2026_susi_result"])  # 행 없는 문서 제외
        self.assertIn("2026학년도 수시 입시결과", seed["ipsi_documents"][0]["document_name"])
        self.assertEqual(seed["ipsi_documents"][0]["applicable_academic_year"], 2027)
        for r in seed["prior_results"]:
            self.assertEqual(r["source_document_key"], "doc_u14_2026_susi_result")
            self.assertTrue(r["source_url"])
            self.assertEqual((r["academic_year"], r["result_year"]), (2027, 2026))
            self.assertEqual(r["linked_2027_type_name"], "학생부교과(학생부교과전형)")
            self.assertEqual(r["linked_2027_department_name"], "국어국문학과")
        self.assertNotIn("authoritative_universities", seed)
        self.assertEqual(per[0]["build_failures"], [])

    def test_given_seed_when_split_then_null_fields_are_dropped_and_rows_are_preserved(self):
        # given
        seed, _ = builder.build(None)
        # when
        parts = builder.split_seed(seed)
        # then
        rows = [r for p in parts for r in p["prior_results"]]
        self.assertEqual(len(rows), len(seed["prior_results"]))
        self.assertTrue(all(v is not None for r in rows for v in r.values()))
        self.assertTrue(all(p["ipsi_documents"] for p in parts))

    def test_given_same_unit_in_two_documents_when_built_then_empty_cells_are_filled_and_conflict_is_a_warning(self):
        # given: 같은 기본 행이 두 번째 문서에도 있고, 한쪽에만 지원자 수가 있으며 경쟁률은 서로 다르다
        path = os.path.join(builder.PRIOR_DIR, "u14_2026_prior.json")
        with open(path, encoding="utf-8") as f:
            src = json.load(f)
        dup = dict(src["rows"][0], applicant_count=None, competition_rate=19.4, extra_admitted_count=None)
        src["rows"][0]["applicant_count"] = None
        dup["applicant_count"] = 156
        src["rows"].append(dup)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(src, f, ensure_ascii=False)
        # when
        seed, per = builder.build(None)
        # then
        base = [r for r in seed["prior_results"] if r["metric_label"] is None]
        self.assertEqual(len(base), 1)
        self.assertEqual(base[0]["applicant_count"], 156)
        self.assertEqual(base[0]["competition_rate"], 19.5)
        self.assertEqual(per[0]["build_failures"], [])
        self.assertEqual(len(per[0]["build_warnings"]), 1)

    def test_given_row_without_department_when_built_then_department_is_whole_type(self):
        # given: 원문에 모집단위 열이 없는 전형 단위 결과
        path = os.path.join(builder.PRIOR_DIR, "u14_2026_prior.json")
        with open(path, encoding="utf-8") as f:
            src = json.load(f)
        src["rows"][0]["department_name"] = None
        with open(path, "w", encoding="utf-8") as f:
            json.dump(src, f, ensure_ascii=False)
        # when
        seed, _ = builder.build(None)
        # then
        self.assertIn("전형 전체", {r["department_name"] for r in seed["prior_results"]})


if __name__ == "__main__":
    unittest.main()
