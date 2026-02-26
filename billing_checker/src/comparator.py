"""
청구 금액 비교 모듈

HTML 이메일 청구 금액 ↔ Excel 전체 청구 금액을 비교하고
일치/불일치 여부를 판별합니다.
"""
import logging
from typing import List, Tuple, Optional

from .models import EmailBilling, ExcelBilling, ComparisonResult, ComparisonStatus

logger = logging.getLogger(__name__)


class BillingComparator:
    """이메일 청구와 Excel 청구를 매칭하고 금액을 비교"""

    def __init__(self, cfg: dict):
        self.tolerance_amount = cfg.get("tolerance_amount", 0)
        self.tolerance_ratio = cfg.get("tolerance_ratio", 0.0)
        self.client_matching = cfg.get("client_matching", "fuzzy")
        self.fuzzy_threshold = cfg.get("fuzzy_threshold", 80)

    # ── 메인 비교 로직 ─────────────────────────────────────────────────────

    def compare(
        self,
        email_billings: List[EmailBilling],
        excel_billings: List[ExcelBilling],
    ) -> List[ComparisonResult]:
        """
        이메일 청구 목록과 Excel 청구 목록을 비교하여 결과 반환

        매칭 기준: (고객사명, 청구월) 쌍
        """
        results: List[ComparisonResult] = []

        # Excel 청구를 {(정규화된 고객사명, 청구월): ExcelBilling} 로 인덱싱
        excel_index = {}
        for eb in excel_billings:
            key = (self._normalize_name(eb.client_name), eb.billing_month)
            excel_index[key] = eb

        matched_excel_keys = set()

        # 이메일 청구 기준으로 비교
        for email_b in email_billings:
            norm_client = self._normalize_name(email_b.client_name)
            excel_b, matched_key = self._find_excel_match(
                norm_client, email_b.billing_month, excel_index
            )

            if excel_b is None:
                results.append(ComparisonResult(
                    client_name=email_b.client_name,
                    billing_month=email_b.billing_month,
                    status=ComparisonStatus.EXCEL_NOT_FOUND,
                    email_amount=email_b.total_amount,
                    excel_amount=None,
                    difference=None,
                    email_subject=email_b.email_subject,
                    error_message=f"Excel에 '{email_b.client_name}' ({email_b.billing_month}) 데이터 없음",
                ))
                logger.warning(
                    "[Excel 없음] %s / %s → 이메일 금액: %s",
                    email_b.client_name, email_b.billing_month,
                    self._fmt(email_b.total_amount)
                )
            else:
                matched_excel_keys.add(matched_key)
                result = self._compare_amounts(email_b, excel_b)
                results.append(result)
                self._log_result(result)

        # Excel에는 있지만 이메일이 없는 경우
        for key, excel_b in excel_index.items():
            if key not in matched_excel_keys:
                results.append(ComparisonResult(
                    client_name=excel_b.client_name,
                    billing_month=excel_b.billing_month,
                    status=ComparisonStatus.EMAIL_NOT_FOUND,
                    email_amount=None,
                    excel_amount=excel_b.total_amount,
                    difference=None,
                    manager_name=excel_b.manager_name,
                    manager_email=excel_b.manager_email,
                    client_email=excel_b.client_email,
                    error_message=f"이메일에 '{excel_b.client_name}' ({excel_b.billing_month}) 청구 없음",
                ))
                logger.warning(
                    "[이메일 없음] %s / %s → Excel 금액: %s",
                    excel_b.client_name, excel_b.billing_month,
                    self._fmt(excel_b.total_amount)
                )

        match_count = sum(1 for r in results if r.status == ComparisonStatus.MATCH)
        mismatch_count = sum(1 for r in results if r.status == ComparisonStatus.MISMATCH)
        logger.info(
            "비교 완료 - 전체: %d건 | 일치: %d건 | 불일치: %d건 | 기타: %d건",
            len(results), match_count, mismatch_count,
            len(results) - match_count - mismatch_count,
        )
        return results

    # ── 매칭 ──────────────────────────────────────────────────────────────

    def _find_excel_match(
        self,
        norm_client: str,
        billing_month: str,
        excel_index: dict,
    ) -> Tuple[Optional[ExcelBilling], Optional[tuple]]:
        """고객사명과 청구월로 Excel 데이터 검색"""

        # 1차: 완전 일치
        key = (norm_client, billing_month)
        if key in excel_index:
            return excel_index[key], key

        # 2차: 청구월이 비어 있는 경우 (이메일에서 추출 실패) - 고객사명만으로 매칭
        if not billing_month:
            candidates = [(k, v) for k, v in excel_index.items() if k[0] == norm_client]
            if len(candidates) == 1:
                return candidates[0][1], candidates[0][0]

        # 3차: fuzzy 매칭
        if self.client_matching == "fuzzy":
            best_score = 0
            best_key = None
            best_val = None
            for (ec_norm, em), excel_b in excel_index.items():
                # 청구월이 둘 다 있으면 청구월도 일치해야 함
                if billing_month and em and billing_month != em:
                    continue
                score = self._fuzzy_score(norm_client, ec_norm)
                if score > best_score:
                    best_score = score
                    best_key = (ec_norm, em)
                    best_val = excel_b

            if best_score >= self.fuzzy_threshold:
                logger.debug(
                    "Fuzzy 매칭: '%s' → '%s' (유사도: %d%%)",
                    norm_client, best_key[0] if best_key else "", best_score
                )
                return best_val, best_key

        return None, None

    # ── 금액 비교 ─────────────────────────────────────────────────────────

    def _compare_amounts(self, email_b: EmailBilling, excel_b: ExcelBilling) -> ComparisonResult:
        email_amt = email_b.total_amount
        excel_amt = excel_b.total_amount
        diff = abs(email_amt - excel_amt)

        # 허용 오차 판단
        within_tolerance = diff <= self.tolerance_amount
        if not within_tolerance and self.tolerance_ratio > 0 and excel_amt > 0:
            within_tolerance = (diff / excel_amt) <= self.tolerance_ratio

        status = ComparisonStatus.MATCH if within_tolerance else ComparisonStatus.MISMATCH

        return ComparisonResult(
            client_name=excel_b.client_name,
            billing_month=excel_b.billing_month,
            status=status,
            email_amount=email_amt,
            excel_amount=excel_amt,
            difference=email_amt - excel_amt,  # 양수=이메일이 더 큼
            manager_name=excel_b.manager_name,
            manager_email=excel_b.manager_email,
            client_email=excel_b.client_email,
            email_subject=email_b.email_subject,
        )

    # ── 유틸리티 ──────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_name(name: str) -> str:
        """고객사명 정규화: 소문자, 공백/특수문자 제거"""
        import re
        return re.sub(r"[\s\(\)\[\]주식회사유한회사합자합명]", "", name).lower()

    @staticmethod
    def _fuzzy_score(a: str, b: str) -> int:
        """문자열 유사도 점수 (0~100)"""
        try:
            from thefuzz import fuzz  # type: ignore
            return fuzz.ratio(a, b)
        except ImportError:
            # thefuzz 미설치 시 간단한 공통 글자 비율
            if not a or not b:
                return 0
            common = sum(1 for c in a if c in b)
            return int(common / max(len(a), len(b)) * 100)

    @staticmethod
    def _fmt(amount: float) -> str:
        return f"{amount:,.0f}원"

    @staticmethod
    def _log_result(result: ComparisonResult):
        if result.status == ComparisonStatus.MATCH:
            logger.info(
                "[일치] %s / %s → %s",
                result.client_name, result.billing_month,
                f"{result.email_amount:,.0f}원"
            )
        else:
            logger.warning(
                "[불일치] %s / %s → 이메일: %s | Excel: %s | 차이: %s",
                result.client_name, result.billing_month,
                f"{result.email_amount:,.0f}원",
                f"{result.excel_amount:,.0f}원",
                f"{result.difference:+,.0f}원",
            )
