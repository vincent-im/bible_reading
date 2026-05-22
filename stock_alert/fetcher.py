import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

_NAVER_STOCK_URL = "https://m.stock.naver.com/api/stock/{code}/basic"
_NAVER_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockBot/1.0)"}


def _get_naver_realtime_price(code: str) -> "float | None":
    """네이버금융 모바일 API로 한국 주식 실시간 현재가 조회"""
    try:
        url = _NAVER_STOCK_URL.format(code=code)
        resp = requests.get(url, headers=_NAVER_HEADERS, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        # currentPrice 필드 (장중) 또는 closePrice (장후) 사용
        for field in ("currentPrice", "closePrice"):
            val = data.get(field)
            if val:
                price = float(str(val).replace(",", ""))
                if price > 0:
                    return price
    except Exception as e:
        print(f"[Naver 실시간] {code} 조회 실패: {e}")
    return None


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
    """
    실시간 현재가 조회.
    한국 주식(.KS/.KQ 또는 6자리 코드): 네이버금융 모바일 API → yfinance fast_info 순 시도.
    해외 주식: yfinance fast_info → OHLCV 최종가 순 시도.
    """
    code = None
    upper = ticker.upper()
    if upper.endswith(".KS") or upper.endswith(".KQ"):
        code = upper[:6]
    elif ticker.isdigit() and len(ticker) == 6:
        code = ticker

    if code:
        price = _get_naver_realtime_price(code)
        if price:
            print(f"[실시간가] {ticker}: {price:,.0f}원 (네이버금융)")
            return price

    # yfinance fast_info fallback (해외 및 Naver 실패 시)
    try:
        info = yf.Ticker(ticker).fast_info
        price = getattr(info, "last_price", None)
        if price and float(price) > 0:
            print(f"[실시간가] {ticker}: {float(price):,.4f} (yfinance fast_info)")
            return float(price)
    except Exception:
        pass

    # 최종 fallback: OHLCV 마지막 종가
    df = fetch_ohlcv(ticker, period_days=5)
    price = float(df["Close"].iloc[-1])
    print(f"[실시간가] {ticker}: {price:,.4f} (OHLCV 최종가 fallback)")
    return price


def resolve_korean_ticker(code: str) -> str:
    code = code.strip().upper()
    if code.isdigit() and len(code) == 6:
        return code + ".KS"
    return code
