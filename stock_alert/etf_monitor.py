from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd


def _get_recent_trading_days(n: int = 2) -> list[str]:
    """주말을 제외한 최근 n개 거래일을 YYYYMMDD 형식으로 반환"""
    days = []
    dt = datetime.now()
    while len(days) < n:
        if dt.weekday() < 5:
            days.append(dt.strftime("%Y%m%d"))
        dt -= timedelta(days=1)
    return days


def fetch_etf_top20(top_n: int = 20) -> tuple[pd.DataFrame | None, str]:
    """
    국내 ETF 전종목 당일 수익률을 계산하여 상위 top_n개를 반환합니다.

    반환: (DataFrame | None, 기준일자 YYYY-MM-DD)
      DataFrame 컬럼: name, close, return, volume
    """
    trading_days = _get_recent_trading_days(2)
    today_str, prev_str = trading_days[0], trading_days[1]
    date_label = f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]}"

    df_today = stock.get_etf_ohlcv_by_ticker(today_str)
    df_prev = stock.get_etf_ohlcv_by_ticker(prev_str)

    if df_today.empty or df_prev.empty:
        return None, date_label

    common = df_today.index.intersection(df_prev.index)
    close_today = df_today.loc[common, '종가']
    close_prev = df_prev.loc[common, '종가']

    valid_prev = close_prev[close_prev > 0]
    common = valid_prev.index.intersection(close_today.index)

    returns = (close_today[common] - valid_prev[common]) / valid_prev[common] * 100

    result = pd.DataFrame({
        'close': close_today[common],
        'return': returns,
        'volume': df_today.loc[common, '거래량'],
    })

    top = result.sort_values('return', ascending=False).head(top_n).copy()

    names = {}
    for ticker in top.index:
        try:
            names[ticker] = stock.get_etf_ticker_name(ticker)
        except Exception:
            names[ticker] = ticker
    top['name'] = pd.Series(names)

    return top, date_label
