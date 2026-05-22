import time
import json
from datetime import datetime
from .fetcher import fetch_ohlcv, resolve_korean_ticker
from .signals import check_sell_signals
from .telegram_notifier import TelegramNotifier


class StockMonitor:
    def __init__(self, notifier: TelegramNotifier, check_interval_minutes: int = 5):
        self.notifier = notifier
        self.check_interval = check_interval_minutes * 60
        # {ticker: set of signal_types already fired today}
        self._fired_today: dict[str, set] = {}
        self._last_reset_date: str = ""

    def _reset_if_new_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self._last_reset_date:
            self._fired_today.clear()
            self._last_reset_date = today

    def _already_fired(self, ticker: str, signal_type: str) -> bool:
        return signal_type in self._fired_today.get(ticker, set())

    def _mark_fired(self, ticker: str, signal_type: str):
        self._fired_today.setdefault(ticker, set()).add(signal_type)

    def check_once(self, watchlist: list[dict]):
        self._reset_if_new_day()
        now = datetime.now().strftime("%H:%M:%S")

        for item in watchlist:
            raw_ticker = item["ticker"]
            ticker = resolve_korean_ticker(raw_ticker)
            name = item.get("name", "")
            buy_price = item["buy_price"]
            stop_loss_pct = item.get("stop_loss_pct", 10.0)
            take_profit_pct = item.get("take_profit_pct", 100.0)
            rsi_overbought = item.get("rsi_overbought", 70.0)
            updown_threshold = item.get("updown_threshold", 5.0)
            label = f"{name}({ticker})" if name else ticker

            try:
                df = fetch_ohlcv(ticker)
                daily_change, signals = check_sell_signals(
                    df, buy_price,
                    stop_loss_pct=stop_loss_pct,
                    take_profit_pct=take_profit_pct,
                    rsi_overbought=rsi_overbought,
                    updown_threshold=updown_threshold,
                )

                price = float(df["Close"].iloc[-1])
                chg = (price - buy_price) / buy_price * 100
                sign = "+" if chg >= 0 else ""

                if daily_change is None:
                    # 1단계 미충족 — 당일 변동 ±5% 미만
                    print(f"[{now}] {label}: {price:,.2f} ({sign}{chg:.2f}%) — 1단계 미충족")
                    continue

                d_sign = "+" if daily_change >= 0 else ""
                if not signals:
                    # 1단계 충족, 2단계 시그널 없음
                    print(f"[{now}] {label}: {price:,.2f} ({sign}{chg:.2f}%) — 1단계 충족(당일{d_sign}{daily_change:.2f}%) / 2단계 시그널 없음")
                    continue

                for sig in signals:
                    if self._already_fired(ticker, sig.signal_type):
                        continue
                    print(f"[{now}] {label}: {sig.signal_type} 시그널 발생 (당일{d_sign}{daily_change:.2f}%) → 텔레그램 전송")
                    sent = self.notifier.send_sell_alert(
                        ticker=ticker,
                        signal_type=sig.signal_type,
                        message=sig.message,
                        current_price=sig.current_price,
                        buy_price=buy_price,
                        change_pct=sig.change_pct,
                        daily_change_pct=sig.daily_change_pct,
                        name=name,
                    )
                    if sent:
                        self._mark_fired(ticker, sig.signal_type)

            except Exception as e:
                print(f"[{now}] {ticker}: 오류 — {e}")

    def run(self, watchlist: list[dict]):
        print(f"모니터링 시작 (간격: {self.check_interval // 60}분)")
        self.notifier.send_startup_message(watchlist)

        while True:
            self.check_once(watchlist)
            time.sleep(self.check_interval)
