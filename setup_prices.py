#!/usr/bin/env python3
"""
watchlist.json에서 buy_price가 0이고 fetch_current가 true인 종목의
현재가를 yfinance로 자동으로 채워줍니다.

사용법: python setup_prices.py
"""

import json
import yfinance as yf
from pathlib import Path

WATCHLIST_PATH = "watchlist.json"


def fetch_price(ticker: str) -> float | None:
    try:
        df = yf.download(ticker, period="2d", progress=False, auto_adjust=True)
        if not df.empty:
            return float(df["Close"].iloc[-1])
    except Exception as e:
        print(f"  [{ticker}] 가격 조회 실패: {e}")
    return None


def main():
    with open(WATCHLIST_PATH, encoding="utf-8") as f:
        watchlist = json.load(f)

    updated = False
    for item in watchlist:
        if not item.get("fetch_current") or item.get("buy_price", 0) != 0:
            continue

        ticker = item["ticker"]
        name = item.get("name", ticker)
        print(f"{name} ({ticker}) 현재가 조회 중...", end=" ", flush=True)

        price = fetch_price(ticker)
        if price:
            item["buy_price"] = round(price, 2)
            item.pop("fetch_current", None)
            print(f"{price:,.2f}")
            updated = True
        else:
            print("실패 — 직접 입력 필요")

    if updated:
        with open(WATCHLIST_PATH, "w", encoding="utf-8") as f:
            json.dump(watchlist, f, ensure_ascii=False, indent=2)
        print(f"\nwatchlist.json 저장 완료")
    else:
        print("\n업데이트할 항목 없음")


if __name__ == "__main__":
    main()
