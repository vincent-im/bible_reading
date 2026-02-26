"""핵심 기능 단위 테스트"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src.email_reader import HtmlBillingParser
from src.comparator import BillingComparator
from src.models import EmailBilling, ExcelBilling, ComparisonStatus


# ── HTML 파서 테스트 ────────────────────────────────────────────────────────

class TestHtmlBillingParser:
    def _parser(self):
        return HtmlBillingParser({
            "method": "auto",
            "total_row_keywords": ["합계", "총액", "total", "Total"],
            "amount_patterns": [
                r"합계[\s:：]*([\d,]+)\s*원",
                r"청구금액[\s:：]*([\d,]+)\s*원",
                r"총액[\s:：]*([\d,]+)\s*원",
            ],
            "client_patterns": [r"고객사[\s:：]*([^\n<]+)", r"청구처[\s:：]*([^\n<]+)"],
            "billing_month_patterns": [
                r"(\d{4}[-./]\d{1,2})\s*(?:월|청구)",
                r"(\d{4})년\s*(\d{1,2})월",
            ],
        })

    def test_table_total_row(self):
        html = """<table>
          <tr><th>항목</th><th>금액</th></tr>
          <tr><td>서비스A</td><td>1,000,000원</td></tr>
          <tr><td>합계</td><td>1,000,000원</td></tr>
        </table>"""
        result = self._parser().parse(html)
        assert result["total_amount"] == 1_000_000.0

    def test_pattern_match(self):
        html = "<p>합계: 2,500,000원</p>"
        result = self._parser().parse(html)
        assert result["total_amount"] == 2_500_000.0

    def test_client_extraction(self):
        html = "<p>고객사: ABC상사</p><p>합계: 1,000,000원</p>"
        result = self._parser().parse(html)
        assert "ABC상사" in result["client_name"]

    def test_month_extraction(self):
        html = "<p>청구월: 2024년 01월 청구</p><p>합계: 500,000원</p>"
        result = self._parser().parse(html)
        assert result["billing_month"] == "2024-01"

    def test_amount_with_table_no_total_row(self):
        """합계 행 없이 항목만 있는 경우 - 합산"""
        html = """<table>
          <tr><td>항목1</td><td>300,000원</td></tr>
          <tr><td>항목2</td><td>200,000원</td></tr>
        </table>"""
        result = self._parser().parse(html)
        assert result["total_amount"] == 500_000.0


# ── 비교기 테스트 ───────────────────────────────────────────────────────────

class TestBillingComparator:
    def _comparator(self, tolerance=0):
        return BillingComparator({
            "tolerance_amount": tolerance,
            "tolerance_ratio": 0.0,
            "client_matching": "fuzzy",
            "fuzzy_threshold": 80,
        })

    def _email(self, client, amount, month="2024-01"):
        return EmailBilling(
            email_subject=f"청구_{client}",
            sender_email="sender@test.com",
            sender_name="발신자",
            received_at=datetime.now(),
            client_name=client,
            billing_month=month,
            total_amount=amount,
        )

    def _excel(self, client, amount, month="2024-01"):
        return ExcelBilling(
            client_name=client,
            billing_month=month,
            total_amount=amount,
            manager_name="담당자",
            manager_email="manager@test.com",
            client_email="client@test.com",
        )

    def test_exact_match(self):
        results = self._comparator().compare(
            [self._email("ABC상사", 1_000_000)],
            [self._excel("ABC상사", 1_000_000)],
        )
        assert len(results) == 1
        assert results[0].status == ComparisonStatus.MATCH

    def test_mismatch(self):
        results = self._comparator().compare(
            [self._email("ABC상사", 1_000_000)],
            [self._excel("ABC상사", 1_200_000)],
        )
        assert results[0].status == ComparisonStatus.MISMATCH
        assert results[0].difference == -200_000  # 이메일 - Excel

    def test_within_tolerance(self):
        results = self._comparator(tolerance=5000).compare(
            [self._email("ABC상사", 1_000_000)],
            [self._excel("ABC상사", 1_003_000)],
        )
        assert results[0].status == ComparisonStatus.MATCH

    def test_excel_not_found(self):
        results = self._comparator().compare(
            [self._email("없는회사", 1_000_000)],
            [self._excel("ABC상사", 1_000_000)],
        )
        # 없는회사 → Excel 없음, ABC상사 → 이메일 없음
        statuses = {r.status for r in results}
        assert ComparisonStatus.EXCEL_NOT_FOUND in statuses
        assert ComparisonStatus.EMAIL_NOT_FOUND in statuses

    def test_fuzzy_client_name(self):
        """'ABC상사(주)' ↔ 'ABC상사' 유사 이름 매칭"""
        results = self._comparator().compare(
            [self._email("ABC상사(주)", 2_000_000)],
            [self._excel("ABC상사", 2_000_000)],
        )
        # fuzzy 매칭으로 일치해야 함
        match_results = [r for r in results if r.status == ComparisonStatus.MATCH]
        assert len(match_results) >= 1

    def test_multiple_clients(self):
        emails = [
            self._email("A사", 1_000_000),
            self._email("B사", 2_000_000),
        ]
        excels = [
            self._excel("A사", 1_000_000),
            self._excel("B사", 2_500_000),  # B사 불일치
        ]
        results = self._comparator().compare(emails, excels)
        assert len(results) == 2
        a_result = next(r for r in results if "A사" in r.client_name)
        b_result = next(r for r in results if "B사" in r.client_name)
        assert a_result.status == ComparisonStatus.MATCH
        assert b_result.status == ComparisonStatus.MISMATCH


if __name__ == "__main__":
    # pytest 없이 직접 실행
    import traceback
    test_classes = [TestHtmlBillingParser, TestBillingComparator]
    passed = failed = 0
    for cls in test_classes:
        obj = cls()
        for name in dir(obj):
            if name.startswith("test_"):
                try:
                    getattr(obj, name)()
                    print(f"  PASS: {cls.__name__}.{name}")
                    passed += 1
                except Exception:
                    print(f"  FAIL: {cls.__name__}.{name}")
                    traceback.print_exc()
                    failed += 1
    print(f"\n결과: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
