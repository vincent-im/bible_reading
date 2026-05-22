#!/usr/bin/env python3
"""
국내 ETF 당일 수익률 상위 20개를 텔레그램으로 전송합니다.
GitHub Actions에서 매 1시간마다 자동 실행됩니다.
"""

import os
import sys
from dotenv import load_dotenv
from stock_alert.etf_monitor import fetch_etf_top20
from stock_alert.telegram_notifier import TelegramNotifier

load_dotenv()


def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        print("[오류] TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        sys.exit(1)

    notifier = TelegramNotifier(bot_token, chat_id)

    print("국내 ETF 수익률 상위 20개 조회 중...")
    try:
        top20, date_label = fetch_etf_top20()
    except Exception as e:
        print(f"[오류] ETF 데이터 조회 실패: {e}")
        sys.exit(1)

    if top20 is None or top20.empty:
        print("데이터 없음 — 휴장일이거나 아직 장이 시작되지 않았습니다.")
        sys.exit(0)

    print(f"상위 {len(top20)}개 종목 조회 완료. 텔레그램 전송 중...")
    sent = notifier.send_etf_report(top20, date_label)
    if sent:
        print("전송 완료.")
    else:
        print("[오류] 텔레그램 전송 실패.")
        sys.exit(1)


if __name__ == "__main__":
    main()
