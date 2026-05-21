import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def fetch_ohlcv(ticker: str, period_days: int = 60) -> pd.DataFrame:
    """
    yfinance로 OHLCV 데이터를 가져옵니다.
    한국 주식은 ticker 뒤에 .KS (코스피) 또는 .KQ (코스닥)를 붙입니다.
    예: 삼성전자 → 005930.KS, 카카오 → 035720.KS
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
    """
    6자리 숫자 코드이면 자동으로 .KS 접미사를 붙입니다.
    이미 접미사가 있거나 해외 종목이면 그대로 반환합니다.
    """
    code = code.strip().upper()
    if code.isdigit() and len(code) == 6:
        return code + ".KS"
    return code
