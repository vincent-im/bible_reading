"""데이터 모델 정의"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class ComparisonStatus(Enum):
    MATCH = "일치"
    MISMATCH = "불일치"
    EMAIL_NOT_FOUND = "이메일 없음"
    EXCEL_NOT_FOUND = "엑셀 없음"
    PARSE_ERROR = "파싱 오류"


@dataclass
class EmailBilling:
    """HTML 이메일에서 추출한 청구 정보"""
    email_subject: str
    sender_email: str
    sender_name: str
    received_at: datetime
    client_name: str
    billing_month: str          # "2024-01" 형식
    total_amount: float
    raw_html: str = ""
    items: list = field(default_factory=list)  # 개별 항목 목록


@dataclass
class ExcelBilling:
    """Excel 파일에서 읽은 청구 정보"""
    client_name: str
    billing_month: str          # "2024-01" 형식
    total_amount: float
    manager_name: str
    manager_email: str
    client_email: str
    items: list = field(default_factory=list)


@dataclass
class ComparisonResult:
    """비교 결과"""
    client_name: str
    billing_month: str
    status: ComparisonStatus
    email_amount: Optional[float]
    excel_amount: Optional[float]
    difference: Optional[float]
    manager_name: str = ""
    manager_email: str = ""
    client_email: str = ""
    email_subject: str = ""
    error_message: str = ""
    action_taken: str = ""      # "청구서 발행 요청" | "수정 요청" | ""
    processed_at: datetime = field(default_factory=datetime.now)
