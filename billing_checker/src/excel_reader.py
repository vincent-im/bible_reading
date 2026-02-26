"""
Excel 청구 데이터 읽기 모듈

Excel 파일(전체 청구 내역)에서 고객사별 청구 정보를 읽어옵니다.
"""
import logging
import re
from pathlib import Path
from typing import List, Dict

import pandas as pd

from .models import ExcelBilling

logger = logging.getLogger(__name__)


class ExcelBillingReader:
    """Excel 파일에서 전체 청구 데이터를 읽는 클래스"""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.file_path = cfg.get("file_path", "")
        self.sheet_name = cfg.get("sheet_name") or 0  # None이면 첫 번째 시트
        self.header_row = cfg.get("header_row", 0)
        self.col_map: Dict[str, str] = cfg.get("columns", {})

    def read(self, file_path: str = None) -> List[ExcelBilling]:
        """Excel 파일을 읽어 ExcelBilling 목록 반환"""
        path = Path(file_path or self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel 파일을 찾을 수 없습니다: {path}")

        logger.info("Excel 파일 읽기 시작: %s", path)
        try:
            df = pd.read_excel(
                path,
                sheet_name=self.sheet_name,
                header=self.header_row,
                engine="openpyxl",
            )
        except Exception as e:
            raise RuntimeError(f"Excel 파일 읽기 실패: {e}") from e

        df = self._clean_dataframe(df)
        results = self._parse_rows(df)
        logger.info("Excel 파일 읽기 완료: %d건", len(results))
        return results

    # ── 전처리 ────────────────────────────────────────────────────────────

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """결측값 제거 및 컬럼명 정규화"""
        # 완전히 빈 행 제거
        df = df.dropna(how="all").reset_index(drop=True)
        # 컬럼명 공백 제거
        df.columns = [str(c).strip() for c in df.columns]
        return df

    def _parse_rows(self, df: pd.DataFrame) -> List[ExcelBilling]:
        results = []
        col = self.col_map

        required = ["client_name", "amount"]
        for field in required:
            col_name = col.get(field)
            if col_name and col_name not in df.columns:
                logger.warning(
                    "Excel 컬럼 '%s'(%s)을 찾을 수 없습니다. 사용 가능한 컬럼: %s",
                    field, col_name, list(df.columns)
                )

        for idx, row in df.iterrows():
            try:
                billing = self._parse_row(row, col, idx)
                if billing:
                    results.append(billing)
            except Exception as e:
                logger.warning("Excel %d행 파싱 오류: %s", idx + 2, e)

        return results

    def _parse_row(self, row: pd.Series, col: dict, idx: int) -> ExcelBilling | None:
        client_name = self._get_str(row, col.get("client_name", "고객사명"))
        amount_raw = self._get_val(row, col.get("amount", "금액"))

        if not client_name or amount_raw is None:
            return None

        amount = self._parse_amount(amount_raw)
        if amount is None:
            logger.debug("Excel %d행: 금액 파싱 실패 (값: %s)", idx + 2, amount_raw)
            return None

        return ExcelBilling(
            client_name=client_name,
            billing_month=self._parse_month(
                self._get_val(row, col.get("billing_month", "청구월"))
            ),
            total_amount=amount,
            manager_name=self._get_str(row, col.get("manager_name", "담당자")),
            manager_email=self._get_str(row, col.get("manager_email", "담당자이메일")),
            client_email=self._get_str(row, col.get("client_email", "고객사이메일")),
            items=[],
        )

    # ── 유틸리티 ──────────────────────────────────────────────────────────

    @staticmethod
    def _get_str(row: pd.Series, col_name: str) -> str:
        if col_name not in row.index:
            return ""
        val = row[col_name]
        if pd.isna(val):
            return ""
        return str(val).strip()

    @staticmethod
    def _get_val(row: pd.Series, col_name: str):
        if col_name not in row.index:
            return None
        val = row[col_name]
        if pd.isna(val):
            return None
        return val

    @staticmethod
    def _parse_amount(value) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        # 문자열에서 숫자만 추출
        cleaned = re.sub(r"[^\d.]", "", str(value).replace(",", ""))
        if cleaned:
            try:
                return float(cleaned)
            except ValueError:
                pass
        return None

    @staticmethod
    def _parse_month(value) -> str:
        if value is None:
            return ""
        if hasattr(value, "strftime"):  # datetime / Timestamp
            return value.strftime("%Y-%m")
        raw = str(value).strip()
        # 다양한 형식 통일: 2024년 1월, 2024-01, 2024/01, 202401
        match = re.search(r"(\d{4})\D*(\d{1,2})", raw)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}"
        return raw
