import pandas as pd
import numpy as np
import pytest
from stock_alert.signals import check_sell_signals, check_updown_variables, calc_rsi, calc_macd


def make_df(prices: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"Close": prices})


# ── 1단계: UPDOWN_VARIABLES ──────────────────────────────────────────────────

def test_updown_triggered_down():
    prices = [100.0] * 49 + [94.0]   # 전일 100 → 당일 94 (-6%)
    df = make_df(prices)
    assert check_updown_variables(df, threshold=5.0) == pytest.approx(-6.0)


def test_updown_triggered_up():
    prices = [100.0] * 49 + [106.0]  # +6%
    df = make_df(prices)
    assert check_updown_variables(df, threshold=5.0) == pytest.approx(6.0)


def test_updown_not_triggered():
    prices = [100.0] * 49 + [103.0]  # +3% → 미달
    df = make_df(prices)
    assert check_updown_variables(df, threshold=5.0) is None


# ── 2단계: 1단계 미충족 시 시그널 없음 ──────────────────────────────────────

def test_no_signal_when_stage1_not_triggered():
    prices = [100.0] * 49 + [90.0]
    prices[-2] = 92.8
    df = make_df(prices)
    daily, signals = check_sell_signals(df, buy_price=100.0, stop_loss_pct=10.0, updown_threshold=5.0)
    assert daily is None
    assert signals == []


# ── 2단계: 1단계 충족 후 시그널 검사 ────────────────────────────────────────

def test_stop_loss_after_stage1():
    prices = [100.0] * 49 + [87.0]
    df = make_df(prices)
    daily, signals = check_sell_signals(df, buy_price=100.0, stop_loss_pct=10.0, updown_threshold=5.0)
    assert daily is not None
    types = [s.signal_type for s in signals]
    assert "STOP_LOSS" in types


def test_take_profit_after_stage1():
    prices = [100.0] * 49 + [210.0]
    df = make_df(prices)
    daily, signals = check_sell_signals(df, buy_price=100.0, take_profit_pct=100.0, updown_threshold=5.0)
    assert daily is not None
    types = [s.signal_type for s in signals]
    assert "TAKE_PROFIT" in types


def test_stage1_triggered_but_no_stage2():
    prices = [100.0] * 49 + [106.0]
    df = make_df(prices)
    daily, signals = check_sell_signals(df, buy_price=80.0, stop_loss_pct=10.0, take_profit_pct=100.0, updown_threshold=5.0)
    assert daily == pytest.approx(6.0)
    assert signals == []


def test_daily_change_pct_attached():
    prices = [100.0] * 49 + [87.0]
    df = make_df(prices)
    daily, signals = check_sell_signals(df, buy_price=100.0, stop_loss_pct=10.0, updown_threshold=5.0)
    assert signals
    assert signals[0].daily_change_pct == pytest.approx(daily)


def test_rsi_calculation():
    prices = pd.Series([float(i) for i in range(1, 45)] + [44.0, 43.5, 44.2, 43.8, 44.0, 43.0])
    rsi = calc_rsi(prices)
    valid = rsi.dropna()
    assert len(valid) > 0
    assert float(valid.iloc[-1]) > 50
