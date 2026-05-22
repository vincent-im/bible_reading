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
    daily_change_pct: float = field(default=0.0)  # 1단계 당일 변동률


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
    전일 종가 대비 ±threshold% 이상이면 변동률 반환, 미달이면 None 반환.
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
    fundamentals: Optional[dict] = None,
) -> list[SignalResult]:
    """
    2단계: 10개 매도 시그널 검사 (5개 기존 + 5개 투자 대가 기반 신규).
    1단계(UPDOWN_VARIABLES) 충족 후에만 호출됩니다.
    """
    close = df["Close"].squeeze()
    current_price = float(close.iloc[-1])
    change_pct = (current_price - buy_price) / buy_price * 100

    signals = []

    # ── 1. 손절가 도달 ─────────────────────────────────────────────────
    # O'Neil: 7~8% 손절 권장 / 기본값 -10% 유지 (watchlist에서 조정 가능)
    if change_pct <= -stop_loss_pct:
        signals.append(SignalResult(
            triggered=True,
            signal_type="STOP_LOSS",
            message=f"손절가 도달 (O'Neil: 7~8% 권장): 매수가 {buy_price:,.0f} → 현재가 {current_price:,.0f} ({change_pct:+.2f}%)",
            current_price=current_price,
            change_pct=change_pct,
        ))

    # ── 2. 목표가 도달 ─────────────────────────────────────────────────
    # O'Neil: 20~25% 부분 익절 권장 / 기본값 +100% 유지
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

    # ── 3. RSI 과매수 이탈 ────────────────────────────────────────────
    # Templeton: "대중이 열광(과매수)할 때 팔아라"
    rsi = calc_rsi(close)
    if len(rsi.dropna()) >= 2:
        rsi_prev = float(rsi.iloc[-2])
        rsi_curr = float(rsi.iloc[-1])
        if rsi_prev >= rsi_overbought and rsi_curr < rsi_overbought:
            signals.append(SignalResult(
                triggered=True,
                signal_type="RSI_OVERBOUGHT",
                message=f"[Templeton] RSI 과매수 이탈: {rsi_prev:.1f} → {rsi_curr:.1f} (기준: {rsi_overbought})",
                current_price=current_price,
                change_pct=change_pct,
            ))

    # ── 4. MACD 데드크로스 ────────────────────────────────────────────
    if len(close) >= 35:
        macd_line, signal_line = calc_macd(close)
        if len(macd_line.dropna()) >= 2:
            if (float(macd_line.iloc[-2]) >= float(signal_line.iloc[-2]) and
                    float(macd_line.iloc[-1]) < float(signal_line.iloc[-1])):
                signals.append(SignalResult(
                    triggered=True,
                    signal_type="MACD_DEATH_CROSS",
                    message=f"MACD 데드크로스: MACD({float(macd_line.iloc[-1]):.4f}) < 신호선({float(signal_line.iloc[-1]):.4f})",
                    current_price=current_price,
                    change_pct=change_pct,
                ))

    # ── 5. 20일 이동평균 하향 이탈 ───────────────────────────────────
    ma20 = close.rolling(20).mean()
    if len(ma20.dropna()) >= 2:
        if (float(close.iloc[-2]) >= float(ma20.iloc[-2]) and
                float(close.iloc[-1]) < float(ma20.iloc[-1])):
            signals.append(SignalResult(
                triggered=True,
                signal_type="BELOW_MA20",
                message=f"20일 이동평균 하향 이탈: {current_price:,.0f} < MA20 {float(ma20.iloc[-1]):,.0f}",
                current_price=current_price,
                change_pct=change_pct,
            ))

    # ── 6. 50일 이동평균 하향 이탈 [O'Neil / Peter Lynch] ────────────
    # O'Neil: "50일선 대량 거래 이탈은 핵심 매도 신호"
    # Lynch: 성장주의 핵심 지지선
    if len(close) >= 52:
        ma50 = close.rolling(50).mean()
        if len(ma50.dropna()) >= 2:
            if (float(close.iloc[-2]) >= float(ma50.iloc[-2]) and
                    float(close.iloc[-1]) < float(ma50.iloc[-1])):
                signals.append(SignalResult(
                    triggered=True,
                    signal_type="BELOW_MA50",
                    message=f"[O'Neil/Lynch] 50일 이동평균 하향 이탈: {current_price:,.0f} < MA50 {float(ma50.iloc[-1]):,.0f}",
                    current_price=current_price,
                    change_pct=change_pct,
                ))

    # ── 7. 장기 데드크로스 MA50 < MA200 ─────────────────────────────
    # 기관 투자자·퀀트 펀드가 가장 많이 참조하는 장기 약세 신호
    if len(close) >= 202:
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(200).mean()
        if (len(ma50.dropna()) >= 2 and len(ma200.dropna()) >= 2 and
                float(ma50.iloc[-2]) >= float(ma200.iloc[-2]) and
                float(ma50.iloc[-1]) < float(ma200.iloc[-1])):
            signals.append(SignalResult(
                triggered=True,
                signal_type="DEATH_CROSS_50_200",
                message=f"[기관 기준] 장기 데드크로스: MA50({float(ma50.iloc[-1]):,.0f}) < MA200({float(ma200.iloc[-1]):,.0f})",
                current_price=current_price,
                change_pct=change_pct,
            ))

    # ── 8. 거래량 급증 + 가격 하락 (Distribution Day) [O'Neil CANSLIM] ──
    # 기관의 대량 매도 징후: 거래량 50일 평균 대비 1.5배 이상 + 가격 1% 이상 하락
    vol_col = "Volume"
    if vol_col in df.columns and len(close) >= 52:
        vol = df[vol_col].squeeze()
        vol_ma50 = vol.rolling(50).mean()
        if not pd.isna(vol_ma50.iloc[-1]):
            vol_curr = float(vol.iloc[-1])
            vol_avg = float(vol_ma50.iloc[-1])
            price_chg = (float(close.iloc[-1]) - float(close.iloc[-2])) / float(close.iloc[-2]) * 100
            if vol_avg > 0 and price_chg <= -1.0 and vol_curr >= vol_avg * 1.5:
                signals.append(SignalResult(
                    triggered=True,
                    signal_type="DISTRIBUTION_DAY",
                    message=f"[O'Neil] 기관 분산 매도 신호: 거래량 평균 대비 {vol_curr/vol_avg:.1f}배, 가격 {price_chg:.1f}%",
                    current_price=current_price,
                    change_pct=change_pct,
                ))

    # ── 9. Graham P/E 과대평가 [Benjamin Graham] ─────────────────────
    # 방어적 투자자 기준: P/E > 20 = 안전 마진 초과
    # (Graham: "현명한 투자자"에서 방어적 투자자의 P/E 상한선 20배)
    if fundamentals:
        pe = fundamentals.get("trailingPE")
        if pe and isinstance(pe, (int, float)) and not np.isnan(pe) and pe > 20:
            signals.append(SignalResult(
                triggered=True,
                signal_type="GRAHAM_PE",
                message=f"[Graham] P/E 과대평가: {pe:.1f}배 > 20배 (방어적 투자자 안전 마진 초과)",
                current_price=current_price,
                change_pct=change_pct,
            ))

    # ── 10. Lynch PEG 과대평가 [Peter Lynch] ─────────────────────────
    # PEG = P/E ÷ 이익성장률. PEG > 2.0이면 성장 대비 고평가
    # Lynch: "PEG 1 = 공정가치, PEG 2 이상 = 성장이 가격에 과도하게 반영"
    if fundamentals:
        peg = fundamentals.get("pegRatio")
        if peg and isinstance(peg, (int, float)) and not np.isnan(peg) and peg > 2.0:
            signals.append(SignalResult(
                triggered=True,
                signal_type="LYNCH_PEG",
                message=f"[Lynch] PEG 과대평가: {peg:.2f} > 2.0 (성장률 대비 고평가 구간)",
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
    fundamentals: Optional[dict] = None,
) -> tuple[Optional[float], list[SignalResult]]:
    """
    2단계 매도 시그널 체크.

    1단계 (UPDOWN_VARIABLES):
      전일 종가 대비 ±updown_threshold% 이상 변동 시 2단계 진행.

    2단계 (10개 시그널):
      기술적: STOP_LOSS, TAKE_PROFIT, RSI_OVERBOUGHT, MACD_DEATH_CROSS,
               BELOW_MA20, BELOW_MA50, DEATH_CROSS_50_200, DISTRIBUTION_DAY
      기본적: GRAHAM_PE (P/E>20), LYNCH_PEG (PEG>2.0)

    반환값: (daily_change_pct | None, [SignalResult, ...])
    """
    daily_change = check_updown_variables(df, updown_threshold)
    if daily_change is None:
        return None, []

    signals = _check_stage2(df, buy_price, stop_loss_pct, take_profit_pct, rsi_overbought, fundamentals)
    for sig in signals:
        sig.daily_change_pct = daily_change
    return daily_change, signals
