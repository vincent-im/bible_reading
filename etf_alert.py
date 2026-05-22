#!/usr/bin/env python3
"""
국내 ETF 수익률 TOP 20을 텔레그램으로 전송합니다.
ETF_MODE 환경변수로 실행 모드를 지정합니다: daily (기본), weekly, monthly
"""

import os
import sys
import traceback
from dotenv import load_dotenv
from stock_alert.etf_monitor import fetch_etf_top20, fetch_etf_weekly_top20, fetch_etf_monthly_top20
from stock_alert.telegram_notifier import TelegramNotifier

load_dotenv()


def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    mode = os.getenv("ETF_MODE", "daily")

    if not bot_token or not chat_id:
        print("[오류] TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        sys.exit(1)

    notifier = TelegramNotifier(bot_token, chat_id)
    report_type = mode

    try:
        if mode == "weekly":
            print("국내 ETF 주간 수익률 상위 20개 조회 중...")
            top20, date_label = fetch_etf_weekly_top20()
            report_fn = notifier.send_etf_weekly_report
            report_type = "주간"
        elif mode == "monthly":
            print("국내 ETF 월간 수익률 상위 20개 조회 중...")
            top20, date_label = fetch_etf_monthly_top20()
            report_fn = notifier.send_etf_monthly_report
            report_type = "월간"
        else:
            print("국내 ETF 당일 수익률 상위 20개 조회 중...")
            top20, date_label = fetch_etf_top20()
            report_fn = notifier.send_etf_report
            report_type = "당일"
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[오류] ETF {report_type} 데이터 조회 실패: {e}\n{tb}")
        notifier.send_message(f"❌ ETF {report_type} 조회 오류\n{e}\n\n{tb[:500]}")
        sys.exit(1)

    if top20 is None or top20.empty:
        msg = f"⚠️ ETF {report_type} 데이터 없음 — 휴장일이거나 데이터가 없습니다."
        print(msg)
        notifier.send_message(msg)
        sys.exit(0)

    print(f"상위 {len(top20)}개 종목 조회 완료. 텔레그램 전송 중...")
    sent = report_fn(top20, date_label)
    if sent:
        print("전송 완료.")
    else:
        print("[오류] 텔레그램 전송 실패.")
        sys.exit(1)


if __name__ == "__main__":
    main()
