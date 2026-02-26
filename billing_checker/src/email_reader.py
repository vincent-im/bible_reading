"""
Outlook 이메일 읽기 모듈

지원 방식:
  1. outlook_com  - Windows 로컬 Outlook COM API (pywin32)
  2. graph_api    - Microsoft Graph API (Microsoft 365 / Exchange Online)
  3. file         - 로컬 HTML 파일 직접 읽기 (테스트/오프라인용)
"""
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup

from .models import EmailBilling

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# HTML 파서
# ─────────────────────────────────────────────────────────────────────────────

class HtmlBillingParser:
    """HTML 이메일 본문에서 청구 정보를 추출"""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.total_keywords = cfg.get("total_row_keywords", ["합계", "총액", "total", "Total"])
        self.amount_patterns = cfg.get("amount_patterns", [
            r"합계[\s:：]*([\d,]+)\s*원",
            r"청구금액[\s:：]*([\d,]+)\s*원",
            r"총액[\s:：]*([\d,]+)\s*원",
            r"Total[\s:：]*([\d,]+)",
        ])
        self.client_patterns = cfg.get("client_patterns", [
            r"고객사[\s:：]*([^\n<]+)",
            r"청구처[\s:：]*([^\n<]+)",
        ])
        self.month_patterns = cfg.get("billing_month_patterns", [
            r"(\d{4}[-./]\d{1,2})\s*(?:월|청구)",
            r"청구월[\s:：]*(\d{4}[-./]\d{1,2})",
            r"(\d{4})년\s*(\d{1,2})월",   # 한국어 형식: 2024년 01월
        ])
        self.method = cfg.get("method", "auto")

    def parse(self, html: str, subject: str = "", sender_name: str = "") -> dict:
        """
        HTML 문자열을 파싱해서 {client_name, billing_month, total_amount, items} 반환
        """
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator="\n")

        total_amount = None
        items = []

        if self.method in ("table", "auto"):
            total_amount, items = self._parse_table(soup)

        if total_amount is None and self.method in ("pattern", "auto"):
            total_amount = self._parse_pattern(text)

        client_name = self._extract_client(text) or sender_name
        billing_month = self._extract_month(text) or self._guess_month_from_subject(subject)

        return {
            "client_name": client_name.strip() if client_name else "",
            "billing_month": billing_month or "",
            "total_amount": total_amount or 0.0,
            "items": items,
        }

    # ── 테이블 방식 ────────────────────────────────────────────────────────

    def _parse_table(self, soup: BeautifulSoup):
        """HTML 테이블에서 합계 행을 찾아 금액 추출"""
        items = []
        total_amount = None

        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if not cells:
                    continue

                # 합계 행 탐지
                row_text = " ".join(cells).lower()
                is_total_row = any(kw.lower() in row_text for kw in self.total_keywords)

                if is_total_row:
                    # 셀 중 숫자가 있는 마지막 셀을 금액으로 사용
                    for cell in reversed(cells):
                        amount = self._parse_amount_str(cell)
                        if amount is not None:
                            total_amount = amount
                            break
                elif len(cells) >= 2:
                    # 일반 항목 행: 마지막 숫자 셀을 금액으로 추정
                    for cell in reversed(cells):
                        amount = self._parse_amount_str(cell)
                        if amount is not None and amount > 0:
                            items.append({"name": cells[0], "amount": amount})
                            break

            if total_amount is not None:
                break

        # 합계 행이 없을 경우 항목 합산
        if total_amount is None and items:
            total_amount = sum(i["amount"] for i in items)

        return total_amount, items

    # ── 패턴 방식 ──────────────────────────────────────────────────────────

    def _parse_pattern(self, text: str) -> Optional[float]:
        """정규식 패턴으로 금액 추출"""
        for pattern in self.amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = self._parse_amount_str(match.group(1))
                if amount is not None:
                    logger.debug("패턴 '%s'로 금액 추출: %s", pattern, amount)
                    return amount
        return None

    # ── 고객사명 / 청구월 추출 ─────────────────────────────────────────────

    def _extract_client(self, text: str) -> Optional[str]:
        for pattern in self.client_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_month(self, text: str) -> Optional[str]:
        for pattern in self.month_patterns:
            match = re.search(pattern, text)
            if match:
                if match.lastindex and match.lastindex >= 2:
                    # 그룹이 2개 이상 → (year, month) 형식
                    return f"{match.group(1)}-{int(match.group(2)):02d}"
                raw = match.group(1)
                # 구분자 통일 (. / → -)
                return re.sub(r"[./]", "-", raw)
        return None

    def _guess_month_from_subject(self, subject: str) -> Optional[str]:
        match = re.search(r"(\d{4})[-./년\s]*(\d{1,2})[-./월]?", subject)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}"
        return None

    # ── 유틸리티 ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_amount_str(text: str) -> Optional[float]:
        """'1,234,567원' → 1234567.0"""
        cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
        if cleaned:
            try:
                return float(cleaned)
            except ValueError:
                pass
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Outlook COM (Windows)
# ─────────────────────────────────────────────────────────────────────────────

class OutlookComReader:
    """Windows 로컬 Outlook COM API를 통한 이메일 읽기"""

    def __init__(self, cfg: dict, parser: HtmlBillingParser):
        self.cfg = cfg
        self.parser = parser
        self._outlook = None

    def _connect(self):
        try:
            import win32com.client  # type: ignore
            self._outlook = win32com.client.Dispatch("Outlook.Application")
            logger.info("Outlook COM 연결 성공")
        except ImportError:
            raise RuntimeError(
                "pywin32가 설치되어 있지 않습니다.\n"
                "  pip install pywin32\n"
                "Windows 환경에서만 사용 가능합니다."
            )

    def read_billing_emails(self) -> List[EmailBilling]:
        self._connect()
        namespace = self._outlook.GetNamespace("MAPI")

        folder_name = self.cfg.get("inbox_folder", "받은 편지함")
        inbox = self._find_folder(namespace, folder_name)
        if inbox is None:
            logger.warning("폴더 '%s'를 찾을 수 없어 기본 받은 편지함을 사용합니다.", folder_name)
            inbox = namespace.GetDefaultFolder(6)  # olFolderInbox = 6

        return self._filter_and_parse(inbox)

    def _find_folder(self, namespace, folder_name: str):
        try:
            for store in namespace.Stores:
                try:
                    root = store.GetRootFolder()
                    for folder in root.Folders:
                        if folder_name in folder.Name:
                            return folder
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _filter_and_parse(self, folder) -> List[EmailBilling]:
        keywords = self.cfg.get("subject_keywords", ["청구"])
        max_emails = self.cfg.get("max_emails", 50)
        days_back = self.cfg.get("days_back", 30)
        cutoff = datetime.now() - timedelta(days=days_back) if days_back else None

        results = []
        messages = folder.Items
        messages.Sort("[ReceivedTime]", True)  # 최신순

        count = 0
        for msg in messages:
            if max_emails and count >= max_emails:
                break
            try:
                received = msg.ReceivedTime.replace(tzinfo=None)
                if cutoff and received < cutoff:
                    break

                subject = msg.Subject or ""
                if not any(kw.lower() in subject.lower() for kw in keywords):
                    continue

                html_body = msg.HTMLBody or ""
                if not html_body:
                    continue

                parsed = self.parser.parse(html_body, subject, msg.SenderName or "")
                results.append(EmailBilling(
                    email_subject=subject,
                    sender_email=msg.SenderEmailAddress or "",
                    sender_name=msg.SenderName or "",
                    received_at=received,
                    client_name=parsed["client_name"],
                    billing_month=parsed["billing_month"],
                    total_amount=parsed["total_amount"],
                    raw_html=html_body,
                    items=parsed["items"],
                ))
                count += 1
            except Exception as e:
                logger.warning("이메일 처리 중 오류: %s", e)

        logger.info("Outlook COM: %d건 청구 이메일 읽기 완료", len(results))
        return results


# ─────────────────────────────────────────────────────────────────────────────
# Microsoft Graph API
# ─────────────────────────────────────────────────────────────────────────────

class GraphApiReader:
    """Microsoft Graph API를 통한 이메일 읽기 (Microsoft 365)"""

    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"

    def __init__(self, cfg: dict, parser: HtmlBillingParser):
        self.cfg = cfg
        self.parser = parser
        self.api_cfg = cfg.get("graph_api", {})

    def _get_token(self) -> str:
        try:
            import msal  # type: ignore
        except ImportError:
            raise RuntimeError("msal이 설치되어 있지 않습니다: pip install msal")

        import requests  # type: ignore

        app = msal.ConfidentialClientApplication(
            client_id=self.api_cfg["client_id"],
            client_credential=self.api_cfg["client_secret"],
            authority=f"https://login.microsoftonline.com/{self.api_cfg['tenant_id']}",
        )
        result = app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" not in result:
            raise RuntimeError(f"Graph API 토큰 획득 실패: {result.get('error_description')}")
        return result["access_token"]

    def read_billing_emails(self) -> List[EmailBilling]:
        import requests  # type: ignore

        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        keywords = self.cfg.get("subject_keywords", ["청구"])
        days_back = self.cfg.get("days_back", 30)
        max_emails = self.cfg.get("max_emails", 50)

        filter_parts = [f"contains(subject, '{kw}')" for kw in keywords]
        filter_str = " or ".join(filter_parts)
        if days_back:
            cutoff = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
            filter_str = f"({filter_str}) and receivedDateTime ge {cutoff}"

        url = (
            f"{self.GRAPH_ENDPOINT}/me/messages"
            f"?$filter={filter_str}"
            f"&$top={max_emails}"
            f"&$select=subject,sender,receivedDateTime,body"
            f"&$orderby=receivedDateTime desc"
        )

        results = []
        while url:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for msg in data.get("value", []):
                body_content = msg.get("body", {}).get("content", "")
                body_type = msg.get("body", {}).get("contentType", "text")
                if body_type.lower() != "html":
                    continue

                subject = msg.get("subject", "")
                sender = msg.get("sender", {}).get("emailAddress", {})
                received_str = msg.get("receivedDateTime", "")
                received = datetime.fromisoformat(received_str.replace("Z", "+00:00")).replace(tzinfo=None)

                parsed = self.parser.parse(body_content, subject, sender.get("name", ""))
                results.append(EmailBilling(
                    email_subject=subject,
                    sender_email=sender.get("address", ""),
                    sender_name=sender.get("name", ""),
                    received_at=received,
                    client_name=parsed["client_name"],
                    billing_month=parsed["billing_month"],
                    total_amount=parsed["total_amount"],
                    raw_html=body_content,
                    items=parsed["items"],
                ))

            url = data.get("@odata.nextLink")

        logger.info("Graph API: %d건 청구 이메일 읽기 완료", len(results))
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 로컬 HTML 파일 읽기 (테스트/오프라인)
# ─────────────────────────────────────────────────────────────────────────────

class FileReader:
    """로컬 HTML 파일을 이메일로 간주하고 읽기 (테스트용)"""

    def __init__(self, cfg: dict, parser: HtmlBillingParser):
        self.cfg = cfg
        self.parser = parser

    def read_billing_emails(self, directory: str = "sample_data") -> List[EmailBilling]:
        results = []
        html_files = list(Path(directory).glob("*.html"))

        if not html_files:
            logger.warning("'%s' 폴더에 HTML 파일이 없습니다.", directory)
            return results

        for html_file in html_files:
            try:
                html_content = html_file.read_text(encoding="utf-8")
                subject = html_file.stem  # 파일명을 제목으로 사용
                parsed = self.parser.parse(html_content, subject)
                results.append(EmailBilling(
                    email_subject=subject,
                    sender_email="",
                    sender_name="",
                    received_at=datetime.fromtimestamp(html_file.stat().st_mtime),
                    client_name=parsed["client_name"],
                    billing_month=parsed["billing_month"],
                    total_amount=parsed["total_amount"],
                    raw_html=html_content,
                    items=parsed["items"],
                ))
                logger.debug("파일 '%s' 읽기 완료 → 금액: %s", html_file.name, parsed["total_amount"])
            except Exception as e:
                logger.warning("파일 '%s' 처리 오류: %s", html_file, e)

        logger.info("파일 읽기: %d건 처리 완료", len(results))
        return results


# ─────────────────────────────────────────────────────────────────────────────
# 팩토리 함수
# ─────────────────────────────────────────────────────────────────────────────

def create_email_reader(config: dict):
    """설정에 따라 적절한 이메일 리더 반환"""
    sender_method = config.get("sender", {}).get("method", "dry_run")
    html_cfg = config.get("html_parsing", {})
    parser = HtmlBillingParser(html_cfg)
    email_cfg = config.get("email", {})

    # 이메일 읽기 방식 결정: sender method와 무관하게 환경에 따라 자동 선택
    if os.name == "nt":  # Windows
        try:
            import win32com.client  # noqa: F401
            logger.info("Outlook COM 방식으로 이메일 읽기")
            return OutlookComReader(email_cfg, parser)
        except ImportError:
            pass

    graph_cfg = config.get("sender", {}).get("graph_api", {})
    if graph_cfg.get("client_id"):
        logger.info("Microsoft Graph API 방식으로 이메일 읽기")
        merged = {**email_cfg, "graph_api": graph_cfg}
        return GraphApiReader(merged, parser)

    logger.info("로컬 HTML 파일 방식으로 이메일 읽기 (테스트 모드)")
    return FileReader(email_cfg, parser)
