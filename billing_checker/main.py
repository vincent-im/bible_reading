#!/usr/bin/env python3
"""
청구 금액 비교 자동화 시스템
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Outlook 이메일(HTML 개별 청구) ↔ Excel(전체 청구) 금액을 비교하여
  - 일치 → 고객사에 청구서 발행 요청 이메일
  - 불일치 → 담당자에 수정 요청 이메일

사용법:
  python main.py                      # config.yaml 사용
  python main.py --config my.yaml     # 커스텀 설정 파일
  python main.py --excel billing.xlsx # Excel 파일 직접 지정
  python main.py --html-dir emails/   # HTML 파일 폴더 직접 지정
  python main.py --dry-run            # 이메일 발송 없이 시뮬레이션
"""
import argparse
import logging
import sys
from pathlib import Path

import yaml

from src.email_reader import create_email_reader, FileReader, HtmlBillingParser
from src.excel_reader import ExcelBillingReader
from src.comparator import BillingComparator
from src.email_sender import BillingEmailSender
from src.reporter import BillingReporter


# ─────────────────────────────────────────────────────────────────────────────
# 설정 로드
# ─────────────────────────────────────────────────────────────────────────────

def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(cfg: dict):
    level_str = cfg.get("logging", {}).get("level", "INFO")
    level = getattr(logging, level_str.upper(), logging.INFO)
    log_file = cfg.get("logging", {}).get("file", "")

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 메인 로직
# ─────────────────────────────────────────────────────────────────────────────

def run(config: dict, args: argparse.Namespace):
    logger = logging.getLogger(__name__)

    # ── 1. 이메일 청구 읽기 ───────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("1단계: 이메일 청구 데이터 읽기")
    logger.info("=" * 60)

    if args.html_dir:
        # CLI에서 HTML 폴더를 직접 지정한 경우
        html_parser = HtmlBillingParser(config.get("html_parsing", {}))
        reader = FileReader(config.get("email", {}), html_parser)
        email_billings = reader.read_billing_emails(args.html_dir)
    else:
        reader = create_email_reader(config)
        if hasattr(reader, "read_billing_emails"):
            # FileReader는 directory 인자 필요 없음 (config에서 읽음)
            email_billings = (
                reader.read_billing_emails("sample_data")
                if isinstance(reader, FileReader)
                else reader.read_billing_emails()
            )
        else:
            email_billings = []

    if not email_billings:
        logger.warning("읽어온 이메일 청구 데이터가 없습니다. sample_data 폴더의 HTML 파일을 확인하세요.")

    # ── 2. Excel 청구 읽기 ────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("2단계: Excel 전체 청구 데이터 읽기")
    logger.info("=" * 60)

    excel_cfg = config.get("excel", {})
    excel_path = args.excel or excel_cfg.get("file_path", "sample_data/total_billing.xlsx")
    excel_reader = ExcelBillingReader(excel_cfg)
    excel_billings = excel_reader.read(excel_path)

    if not excel_billings:
        logger.warning("Excel에서 읽어온 청구 데이터가 없습니다.")

    # ── 3. 금액 비교 ──────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("3단계: 금액 비교")
    logger.info("=" * 60)

    comparator = BillingComparator(config.get("comparison", {}))
    results = comparator.compare(email_billings, excel_billings)

    # ── 4. 이메일 발송 ────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("4단계: 이메일 발송")
    logger.info("=" * 60)

    sender_cfg = config.get("sender", {})
    if args.dry_run:
        sender_cfg = {**sender_cfg, "method": "dry_run"}

    sender = BillingEmailSender(sender_cfg)
    stats = sender.process_results(results)

    # ── 5. 리포트 생성 ────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("5단계: 리포트 생성")
    logger.info("=" * 60)

    reporter = BillingReporter(config.get("report", {}))
    saved_files = reporter.generate(results)

    # ── 최종 요약 출력 ────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("처리 완료 요약")
    logger.info("=" * 60)
    logger.info("  이메일 청구 건수  : %d건", len(email_billings))
    logger.info("  Excel 청구 건수   : %d건", len(excel_billings))
    logger.info("  비교 결과 건수    : %d건", len(results))
    logger.info("  청구서 발행 요청  : %d건", stats.get("billing_sent", 0))
    logger.info("  수정 요청         : %d건", stats.get("correction_sent", 0))
    logger.info("  건너뜀            : %d건", stats.get("skipped", 0))
    logger.info("  실패              : %d건", stats.get("failed", 0))
    for fmt, file_path in saved_files.items():
        logger.info("  %s 리포트       : %s", fmt.upper(), file_path)
    logger.info("=" * 60)

    return results, stats, saved_files


# ─────────────────────────────────────────────────────────────────────────────
# CLI 진입점
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="청구 금액 비교 자동화 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--config", default="config.yaml",
        help="설정 파일 경로 (기본값: config.yaml)"
    )
    parser.add_argument(
        "--excel",
        help="Excel 청구 파일 경로 (config.yaml의 excel.file_path 덮어씀)"
    )
    parser.add_argument(
        "--html-dir",
        help="HTML 이메일 파일 폴더 경로 (Outlook 대신 로컬 파일 사용)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="이메일 발송 없이 시뮬레이션만 실행"
    )
    parser.add_argument(
        "--report-format", choices=["excel", "html", "both"],
        help="리포트 형식 지정 (config.yaml의 report.format 덮어씀)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 작업 디렉터리를 스크립트 위치로 변경
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)

    config = load_config(args.config)
    setup_logging(config)

    logger = logging.getLogger(__name__)
    logger.info("청구 금액 비교 자동화 시스템 시작")

    # CLI 인자로 config 덮어쓰기
    if args.report_format:
        config.setdefault("report", {})["format"] = args.report_format

    try:
        run(config, args)
    except FileNotFoundError as e:
        logger.error("파일 없음: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.exception("예기치 않은 오류 발생: %s", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
