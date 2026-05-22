import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SignalResult:
    triggered: bool
    signal_type: str
    message: str
    current_price: float
    change_pct: float
    daily_change_pct: float = field(default=0.0)  # 당일 변동률 (1단계 값)


def calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(prices: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


def check_updown_variables(df: pd.DataFrame, threshold: float = 5.0) -> Optional[float]:
    """
    1단계: 당일 변동률 확인.
    전일 종가 대비 ±threshold% 이상이면 변동률을 반환, 미달이면 None 반환.
    """
    close = df["Close"].squeeze()
    if len(close) < 2:
        return None
    prev_close = float(close.iloc[-2])
    current_price = float(close.iloc[-1])
    if prev_close == 0:
        return None
    daily_change = (current_price - prev_close) / prev_close * 100
    if abs(daily_change) >= threshold:
        return daily_change
    return None


def _check_stage2(
    df: pd.DataFrame,
    buy_price: float,
    stop_loss_pct: float,
    take_profit_pct: float,
    rsi_overbought: float,
) -> list[SignalResult]:
    """
    2단계: 기존 5개 매도 시그널 검사.
    1단계(UPDOWN_VARIABLES)가 충족된 후에만 호출됩니다.
    """
    close = df["Close"].squeeze()
    current_price = float(close.iloc[-1])
    change_pct = (current_price - buy_price) / buy_price * 100

    signals = []

    # 1. 손절가 도달
    if change_pct <= -stop_loss_pct:
        signals.append(SignalResult(
            triggered=True,
            signal_type="STOP_LOSS",
            message=f"손절가 도달: 매수가 {buy_price:,.0f} → 현재가 {current_price:,.0f} ({change_pct:+.2f}%)",
            current_price=current_price,
            change_pct=change_pct,
        ))

    # 2. 목표가 도달
    if change_pct >= take_profit_pct:
        signals.append(SignalResult(
            triggered=True,
            signal_type="TAKE_PROFIT",
            message=f"목표가 도달: 매수가 {buy_price:,.0f} → 현재가 {current_price:,.0f} ({change_pct:+.2f}%)",
            current_price=current_price,
            change_pct=change_pct,
        ))

    if len(close) < 30:
        return signals

    # 3. RSI 과매수 후 하락 전환
    rsi = calc_rsi(close)
    if len(rsi.dropna()) >= 2:
        rsi_prev = float(rsi.iloc[-2])
        rsi_curr = float(rsi.iloc[-1])
        if rsi_prev >= rsi_overbought and rsi_curr < rsi_overbought:
            signals.append(SignalResult(
                triggered=True,
                signal_type="RSI_OVERBOUGHT",
                message=f"RSI 과매수 이탈: RSI {rsi_prev:.1f} → {rsi_curr:.1f} (기준: {rsi_overbought})",
                current_price=current_price,
                change_pct=change_pct,
            ))

    # 4. MACD 데드크로스
    if len(close) >= 35:
        macd_line, signal_line = calc_macd(close)
        if len(macd_line.dropna()) >= 2:
            macd_prev = float(macd_line.iloc[-2])
            sig_prev = float(signal_line.iloc[-2])
            macd_curr = float(macd_line.iloc[-1])
            sig_curr = float(signal_line.iloc[-1])
            if macd_prev >= sig_prev and macd_curr < sig_curr:
                signals.append(SignalResult(
                    triggered=True,
                    signal_type="MACD_DEATH_CROSS",
                    message=f"MACD 데드크로스: MACD({macd_curr:.4f}) < 신호선({sig_curr:.4f})",
                    current_price=current_price,
                    change_pct=change_pct,
                ))

    # 5. 20일 이동평균선 하향 이탈
    ma20 = close.rolling(20).mean()
    if len(ma20.dropna()) >= 2:
        ma_prev = float(ma20.iloc[-2])
        ma_curr = float(ma20.iloc[-1])
        close_prev = float(close.iloc[-2])
        close_curr = float(close.iloc[-1])
        if close_prev >= ma_prev and close_curr < ma_curr:
            signals.append(SignalResult(
                triggered=True,
                signal_type="BELOW_MA20",
                message=f"20일 이동평균 하향 이탈: 현재가 {close_curr:,.0f} < MA20 {ma_curr:,.0f}",
                current_price=current_price,
                change_pct=change_pct,
            ))

    return signals


def check_sell_signals(
    df: pd.DataFrame,
    buy_price: float,
    stop_loss_pct: float = 10.0,
    take_profit_pct: float = 100.0,
    rsi_overbought: float = 70.0,
    updown_threshold: float = 5.0,
) -> tuple[Optional[float], list[SignalResult]]:
    """
    2단계 매도 시그널 체크.

    1단계 (UPDOWN_VARIABLES):
      전일 종가 대비 ±updown_threshold% 이상 변동 시 2단계로 진행.
      미달이면 빈 리스트 반환.

    2단계:
      STOP_LOSS, TAKE_PROFIT, RSI_OVERBOUGHT, MACD_DEATH_CROSS, BELOW_MA20 검사.

    반환값: (daily_change_pct | None, [SignalResult, ...])
      - daily_change_pct: 1단계 당일 변동률 (None이면 1단계 미충족)
      - signals: 2단계에서 발생한 시그널 목록
    """
    daily_change = check_updown_variables(df, updown_threshold)
    if daily_change is None:
        return None, []

    signals = _check_stage2(df, buy_price, stop_loss_pct, take_profit_pct, rsi_overbought)
    for sig in signals:
        sig.daily_change_pct = daily_change
    return daily_change, signals
