#!/usr/bin/env python3
import os
import sys
import traceback
from dotenv import load_dotenv
from stock_alert.etf_monitor import fetch_etf_top20
from stock_alert.telegram_notifier import TelegramNotifier

load_dotenv()


def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        print("[오류] Telegram 환경변수 미설정")
        sys.exit(1)

    notifier = TelegramNotifier(bot_token, chat_id)

    print("국내 ETF 수익률 상위 20개 조회 중...")
    try:
        top20, date_label = fetch_etf_top20()
    except Exception as e:
        err = traceback.format_exc()
        print(f"[오류]\n{err}")
        notifier.send_message(f"❌ ETF 조회 오류\n<code>{str(e)[:300]}</code>")
        sys.exit(1)

    if top20 is None or top20.empty:
        msg = "⚠️ ETF 데이터 없음\n휴장일이거나 아직 장이 시작되지 않았습니다."
        print(msg)
        notifier.send_message(msg)
        sys.exit(0)

    print(f"상위 {len(top20)}개 종목 조회 완료. 텔레그램 전송 중...")
    sent = notifier.send_etf_report(top20, date_label)
    if sent:
        print("전송 완료.")
    else:
        print("[오류] 텔레그램 전송 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
