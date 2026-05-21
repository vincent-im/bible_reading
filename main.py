#!/usr/bin/env python3
"""
주식 매도 시그널 텔레그램 알림 프로그램

사용법:
  1. .env 파일에 TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 설정
  2. watchlist.json에 모니터링할 종목 추가
  3. python main.py 실행

또는 대화형 모드:
  python main.py --interactive
"""

import os
import json
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

from stock_alert.monitor import StockMonitor
from stock_alert.telegram_notifier import TelegramNotifier
from stock_alert.fetcher import resolve_korean_ticker

load_dotenv()


def load_watchlist(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_watchlist(path: str, watchlist: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, ensure_ascii=False, indent=2)
    print(f"watchlist 저장됨: {path}")


def interactive_setup(watchlist_path: str) -> list[dict]:
    """대화형으로 종목을 입력받아 watchlist를 구성합니다."""
    watchlist = []
    if Path(watchlist_path).exists():
        keep = input(f"\n기존 {watchlist_path} 파일이 있습니다. 유지하시겠습니까? (y/n): ").strip().lower()
        if keep == "y":
            watchlist = load_watchlist(watchlist_path)
            print(f"기존 종목 {len(watchlist)}개 로드됨")

    print("\n모니터링할 종목을 입력하세요. 입력 완료 시 빈 줄에서 Enter.")
    print("한국 주식: 6자리 숫자 (예: 005930) 또는 005930.KS")
    print("해외 주식: AAPL, TSLA 등\n")

    while True:
        ticker = input("종목코드 (완료 시 Enter): ").strip()
        if not ticker:
            break

        resolved = resolve_korean_ticker(ticker)
        buy_price_str = input(f"  {resolved} 매수가: ").strip().replace(",", "")
        try:
            buy_price = float(buy_price_str)
        except ValueError:
            print("  올바른 숫자를 입력하세요.")
            continue

        stop_loss = input("  손절 기준 (%, 기본 5): ").strip()
        stop_loss_pct = float(stop_loss) if stop_loss else 5.0

        take_profit = input("  목표 수익 (%, 기본 20): ").strip()
        take_profit_pct = float(take_profit) if take_profit else 20.0

        watchlist.append({
            "ticker": resolved,
            "buy_price": buy_price,
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct,
        })
        print(f"  → 추가됨: {resolved} (매수가: {buy_price:,.0f}, 손절: -{stop_loss_pct}%, 목표: +{take_profit_pct}%)\n")

    return watchlist


def get_notifier() -> TelegramNotifier:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not bot_token or bot_token == "your_bot_token_here":
        print("[오류] TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        print("  .env 파일에 TELEGRAM_BOT_TOKEN을 입력하세요.")
        sys.exit(1)
    if not chat_id or chat_id == "your_chat_id_here":
        print("[오류] TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        print("  .env 파일에 TELEGRAM_CHAT_ID를 입력하세요.")
        sys.exit(1)

    return TelegramNotifier(bot_token, chat_id)


def main():
    parser = argparse.ArgumentParser(description="주식 매도 시그널 텔레그램 알림")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="대화형으로 종목 입력")
    parser.add_argument("--watchlist", "-w", default="watchlist.json",
                        help="종목 목록 JSON 파일 (기본: watchlist.json)")
    parser.add_argument("--interval", "-n", type=int, default=None,
                        help="모니터링 간격 (분, 기본: 환경변수 CHECK_INTERVAL_MINUTES 또는 5)")
    parser.add_argument("--once", action="store_true",
                        help="한 번만 체크하고 종료")
    args = parser.parse_args()

    interval = args.interval or int(os.getenv("CHECK_INTERVAL_MINUTES", "5"))

    notifier = get_notifier()
    if not notifier.validate():
        print("[오류] Telegram 봇에 연결할 수 없습니다. 토큰을 확인하세요.")
        sys.exit(1)

    if args.interactive:
        watchlist = interactive_setup(args.watchlist)
        if not watchlist:
            print("종목이 없습니다. 종료합니다.")
            sys.exit(0)
        save_watchlist(args.watchlist, watchlist)
    elif Path(args.watchlist).exists():
        watchlist = load_watchlist(args.watchlist)
        print(f"watchlist 로드: {len(watchlist)}개 종목")
    else:
        print(f"[오류] {args.watchlist} 파일이 없습니다.")
        print("  --interactive 옵션으로 종목을 추가하거나 watchlist.json을 직접 작성하세요.")
        print("  예시: python main.py --interactive")
        sys.exit(1)

    monitor = StockMonitor(notifier, check_interval_minutes=interval)

    if args.once:
        monitor.check_once(watchlist)
    else:
        monitor.run(watchlist)


if __name__ == "__main__":
    main()
