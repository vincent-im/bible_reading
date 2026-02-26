"""
이메일 발송 모듈

비교 결과에 따라:
  - 금액 일치 → 고객사 대상 청구서 발행 요청 이메일
  - 금액 불일치 → 담당자 대상 수정 요청 이메일
  - 데이터 누락 → 담당자 대상 확인 요청 이메일

지원 발송 방식:
  dry_run      - 실제 발송 없이 로그/콘솔 출력 (기본값, 테스트용)
  outlook_com  - Windows Outlook COM API
  graph_api    - Microsoft Graph API
  smtp         - 범용 SMTP
"""
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from .models import ComparisonResult, ComparisonStatus

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 이메일 템플릿
# ─────────────────────────────────────────────────────────────────────────────

def _billing_request_html(result: ComparisonResult) -> str:
    """청구서 발행 요청 이메일 HTML"""
    now = datetime.now().strftime("%Y년 %m월 %d일")
    amount_str = f"{result.excel_amount:,.0f}원"
    month_str = result.billing_month.replace("-", "년 ") + "월"
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<style>
  body {{ font-family: '맑은 고딕', Arial, sans-serif; color: #333; }}
  .container {{ max-width: 620px; margin: 0 auto; padding: 20px; }}
  .header {{ background: #1a73e8; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
  .body {{ background: #f8f9fa; padding: 24px; border: 1px solid #dee2e6; }}
  .footer {{ padding: 16px; font-size: 12px; color: #666; border-top: 1px solid #dee2e6; }}
  .amount-box {{ background: white; border: 2px solid #1a73e8; border-radius: 6px;
                 padding: 16px; text-align: center; margin: 16px 0; }}
  .amount {{ font-size: 24px; font-weight: bold; color: #1a73e8; }}
  .badge {{ display: inline-block; background: #28a745; color: white;
            padding: 4px 12px; border-radius: 12px; font-size: 13px; }}
</style></head>
<body><div class="container">
  <div class="header">
    <h2 style="margin:0">청구서 발행 요청</h2>
    <p style="margin:4px 0 0">{now}</p>
  </div>
  <div class="body">
    <p>안녕하세요,</p>
    <p>아래 내용으로 청구서 발행을 요청드립니다.</p>
    <table style="width:100%; border-collapse:collapse; margin:16px 0;">
      <tr><td style="padding:8px; font-weight:bold; width:40%;">고객사명</td>
          <td style="padding:8px;">{result.client_name}</td></tr>
      <tr style="background:#f0f4ff;"><td style="padding:8px; font-weight:bold;">청구월</td>
          <td style="padding:8px;">{month_str}</td></tr>
      <tr><td style="padding:8px; font-weight:bold;">검증 상태</td>
          <td style="padding:8px;"><span class="badge">금액 검증 완료</span></td></tr>
    </table>
    <div class="amount-box">
      <p style="margin:0; color:#666;">청구 금액</p>
      <p class="amount">{amount_str}</p>
    </div>
    <p>개별 청구 이메일과 전체 청구 Excel 금액이 일치함을 확인하였습니다.<br>
       위 금액으로 청구서를 발행해 주시기 바랍니다.</p>
    <p>감사합니다.</p>
  </div>
  <div class="footer">
    본 이메일은 청구 금액 비교 자동화 시스템에서 발송되었습니다.
  </div>
</div></body></html>"""


def _correction_request_html(result: ComparisonResult) -> str:
    """수정 요청 이메일 HTML"""
    now = datetime.now().strftime("%Y년 %m월 %d일")
    email_amt = f"{result.email_amount:,.0f}원" if result.email_amount is not None else "정보 없음"
    excel_amt = f"{result.excel_amount:,.0f}원" if result.excel_amount is not None else "정보 없음"
    diff_str = ""
    if result.difference is not None:
        sign = "+" if result.difference > 0 else ""
        diff_str = f"{sign}{result.difference:,.0f}원 (이메일 기준)"
    month_str = result.billing_month.replace("-", "년 ") + "월" if result.billing_month else "미확인"

    status_map = {
        ComparisonStatus.MISMATCH: ("금액 불일치", "#dc3545"),
        ComparisonStatus.EMAIL_NOT_FOUND: ("이메일 청구 누락", "#fd7e14"),
        ComparisonStatus.EXCEL_NOT_FOUND: ("Excel 청구 누락", "#fd7e14"),
        ComparisonStatus.PARSE_ERROR: ("파싱 오류", "#6c757d"),
    }
    status_label, status_color = status_map.get(result.status, ("오류", "#dc3545"))

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<style>
  body {{ font-family: '맑은 고딕', Arial, sans-serif; color: #333; }}
  .container {{ max-width: 620px; margin: 0 auto; padding: 20px; }}
  .header {{ background: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
  .body {{ background: #f8f9fa; padding: 24px; border: 1px solid #dee2e6; }}
  .footer {{ padding: 16px; font-size: 12px; color: #666; border-top: 1px solid #dee2e6; }}
  .diff-box {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px;
               padding: 16px; margin: 16px 0; }}
  .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px;
            font-size: 13px; color: white; background: {status_color}; }}
  td {{ padding: 8px; vertical-align: top; }}
</style></head>
<body><div class="container">
  <div class="header">
    <h2 style="margin:0">청구 금액 수정 요청</h2>
    <p style="margin:4px 0 0">{now}</p>
  </div>
  <div class="body">
    <p>안녕하세요, <strong>{result.manager_name}</strong> 담당자님,</p>
    <p>청구 금액 검증 결과 불일치가 발견되어 확인 및 수정을 요청드립니다.</p>
    <table style="width:100%; border-collapse:collapse; margin:16px 0;">
      <tr><td style="font-weight:bold; width:40%;">고객사명</td>
          <td>{result.client_name}</td></tr>
      <tr style="background:#f0f4ff;"><td style="font-weight:bold;">청구월</td>
          <td>{month_str}</td></tr>
      <tr><td style="font-weight:bold;">이상 유형</td>
          <td><span class="badge">{status_label}</span></td></tr>
      <tr style="background:#f0f4ff;"><td style="font-weight:bold;">원본 이메일 제목</td>
          <td>{result.email_subject or "해당 없음"}</td></tr>
    </table>
    <div class="diff-box">
      <table style="width:100%; border-collapse:collapse;">
        <tr><td style="font-weight:bold; color:#856404;">이메일 청구 금액</td>
            <td style="text-align:right; font-size:18px;">{email_amt}</td></tr>
        <tr><td style="font-weight:bold; color:#856404;">Excel 청구 금액</td>
            <td style="text-align:right; font-size:18px;">{excel_amt}</td></tr>
        {f'<tr><td style="font-weight:bold; color:#dc3545;">차이</td><td style="text-align:right; font-size:18px; color:#dc3545;">{diff_str}</td></tr>' if diff_str else ""}
      </table>
    </div>
    {f'<p style="color:#666; font-size:13px;">오류 내용: {result.error_message}</p>' if result.error_message else ""}
    <p>위 내용을 확인하시고 수정 또는 재전송 부탁드립니다.<br>
       문의 사항이 있으시면 회신 부탁드립니다.</p>
    <p>감사합니다.</p>
  </div>
  <div class="footer">
    본 이메일은 청구 금액 비교 자동화 시스템에서 발송되었습니다.
  </div>
</div></body></html>"""


# ─────────────────────────────────────────────────────────────────────────────
# 발송 방식별 클래스
# ─────────────────────────────────────────────────────────────────────────────

class DryRunSender:
    """실제 발송 없이 콘솔에 출력 (테스트용)"""

    def send(self, to: str, subject: str, html_body: str) -> bool:
        border = "─" * 60
        logger.info("\n%s\n[DRY RUN] 이메일 발송 시뮬레이션\n수신: %s\n제목: %s\n%s",
                    border, to, subject, border)
        print(f"\n{'─'*60}")
        print(f"[DRY RUN] 발송될 이메일")
        print(f"  수신: {to}")
        print(f"  제목: {subject}")
        print(f"{'─'*60}")
        return True


class OutlookComSender:
    """Windows Outlook COM을 통한 이메일 발송"""

    def send(self, to: str, subject: str, html_body: str) -> bool:
        try:
            import win32com.client  # type: ignore
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)  # olMailItem
            mail.To = to
            mail.Subject = subject
            mail.HTMLBody = html_body
            mail.Send()
            logger.info("Outlook COM 발송 완료 → %s", to)
            return True
        except ImportError:
            raise RuntimeError("pywin32가 필요합니다: pip install pywin32")
        except Exception as e:
            logger.error("Outlook COM 발송 실패 (%s): %s", to, e)
            return False


class GraphApiSender:
    """Microsoft Graph API를 통한 이메일 발송"""

    def __init__(self, cfg: dict):
        self.api_cfg = cfg.get("graph_api", {})
        self.sender_email = cfg.get("sender_email", "")

    def _get_token(self) -> str:
        try:
            import msal  # type: ignore
        except ImportError:
            raise RuntimeError("msal이 필요합니다: pip install msal")

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

    def send(self, to: str, subject: str, html_body: str) -> bool:
        import requests  # type: ignore
        token = self._get_token()
        url = f"https://graph.microsoft.com/v1.0/users/{self.sender_email}/sendMail"
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": html_body},
                "toRecipients": [{"emailAddress": {"address": to}}],
            }
        }
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if resp.status_code == 202:
            logger.info("Graph API 발송 완료 → %s", to)
            return True
        logger.error("Graph API 발송 실패 (%s): %s %s", to, resp.status_code, resp.text)
        return False


class SmtpSender:
    """범용 SMTP를 통한 이메일 발송"""

    def __init__(self, cfg: dict):
        smtp_cfg = cfg.get("smtp", {})
        self.host = smtp_cfg.get("host", "smtp.office365.com")
        self.port = smtp_cfg.get("port", 587)
        self.username = smtp_cfg.get("username", "")
        self.password = smtp_cfg.get("password", "")
        self.use_tls = smtp_cfg.get("use_tls", True)
        self.sender_name = cfg.get("sender_name", "")
        self.sender_email = cfg.get("sender_email", self.username)

    def send(self, to: str, subject: str, html_body: str) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            from_addr = (
                f"{self.sender_name} <{self.sender_email}>"
                if self.sender_name
                else self.sender_email
            )
            msg["From"] = from_addr
            msg["To"] = to
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.sender_email, [to], msg.as_string())

            logger.info("SMTP 발송 완료 → %s", to)
            return True
        except Exception as e:
            logger.error("SMTP 발송 실패 (%s): %s", to, e)
            return False


# ─────────────────────────────────────────────────────────────────────────────
# 오케스트레이터
# ─────────────────────────────────────────────────────────────────────────────

class BillingEmailSender:
    """비교 결과를 받아 적절한 이메일을 발송"""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        method = cfg.get("method", "dry_run")
        if method == "outlook_com":
            self._sender = OutlookComSender()
        elif method == "graph_api":
            self._sender = GraphApiSender(cfg)
        elif method == "smtp":
            self._sender = SmtpSender(cfg)
        else:
            if method != "dry_run":
                logger.warning("알 수 없는 발송 방식 '%s', dry_run으로 실행합니다.", method)
            self._sender = DryRunSender()

    def process_results(self, results: List[ComparisonResult]) -> dict:
        """비교 결과 목록을 처리하여 이메일 발송"""
        stats = {"billing_sent": 0, "correction_sent": 0, "failed": 0, "skipped": 0}

        for result in results:
            try:
                if result.status == ComparisonStatus.MATCH:
                    self._send_billing_request(result, stats)
                else:
                    self._send_correction_request(result, stats)
            except Exception as e:
                logger.error("이메일 처리 실패 (%s): %s", result.client_name, e)
                result.action_taken = f"오류: {e}"
                stats["failed"] += 1

        logger.info(
            "이메일 발송 완료 - 청구 요청: %d건 | 수정 요청: %d건 | 실패: %d건 | 건너뜀: %d건",
            stats["billing_sent"], stats["correction_sent"], stats["failed"], stats["skipped"]
        )
        return stats

    def _send_billing_request(self, result: ComparisonResult, stats: dict):
        """청구서 발행 요청 이메일 발송"""
        to_email = result.client_email
        if not to_email:
            logger.warning("[청구 요청 건너뜀] %s - 고객사 이메일 없음", result.client_name)
            result.action_taken = "건너뜀: 고객사 이메일 없음"
            stats["skipped"] += 1
            return

        month_str = result.billing_month.replace("-", "년 ") + "월" if result.billing_month else ""
        subject = f"[청구서 발행 요청] {result.client_name} {month_str} 청구서"
        html = _billing_request_html(result)

        ok = self._sender.send(to_email, subject, html)
        if ok:
            result.action_taken = "청구서 발행 요청 발송 완료"
            stats["billing_sent"] += 1
        else:
            result.action_taken = "청구서 발행 요청 발송 실패"
            stats["failed"] += 1

    def _send_correction_request(self, result: ComparisonResult, stats: dict):
        """수정 요청 이메일 발송"""
        to_email = result.manager_email
        if not to_email:
            logger.warning("[수정 요청 건너뜀] %s - 담당자 이메일 없음", result.client_name)
            result.action_taken = "건너뜀: 담당자 이메일 없음"
            stats["skipped"] += 1
            return

        month_str = result.billing_month.replace("-", "년 ") + "월" if result.billing_month else ""
        subject = f"[청구 금액 수정 요청] {result.client_name} {month_str} - {result.status.value}"
        html = _correction_request_html(result)

        ok = self._sender.send(to_email, subject, html)
        if ok:
            result.action_taken = f"수정 요청 발송 완료 ({result.status.value})"
            stats["correction_sent"] += 1
        else:
            result.action_taken = f"수정 요청 발송 실패 ({result.status.value})"
            stats["failed"] += 1
