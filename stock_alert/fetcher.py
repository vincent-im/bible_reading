import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def fetch_fundamentals(ticker: str) -> dict:
    """yfinance에서 기본적 분석 지표(P/E, PEG 등)를 가져옵니다. 실패 시 빈 dict 반환."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "trailingPE":  info.get("trailingPE"),
            "pegRatio":    info.get("pegRatio"),
            "priceToBook": info.get("priceToBook"),
        }
    except Exception:
        return {}


def fetch_ohlcv(ticker: str, period_days: int = 300) -> pd.DataFrame:
    """
    yfinance로 OHLCV 데이터를 가져옵니다.
    한국 주식은 ticker 뒤에 .KS (코스피) 또는 .KQ (코스닥)를 붙입니다.
    """
    end = datetime.today()
    start = end - timedelta(days=period_days)
    df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                     end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"데이터 없음: {ticker} — 티커 코드를 확인하세요.")
    return df


def get_current_price(ticker: str) -> float:
    info = yf.Ticker(ticker).fast_info
    price = getattr(info, "last_price", None)
    if price is None:
        df = fetch_ohlcv(ticker, period_days=5)
        price = float(df["Close"].iloc[-1])
    return float(price)


def resolve_korean_ticker(code: str) -> str:
    code = code.strip().upper()
    if code.isdigit() and len(code) == 6:
        return code + ".KS"
    return code
