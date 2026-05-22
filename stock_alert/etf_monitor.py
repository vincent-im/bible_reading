from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd


def _get_recent_trading_days(n: int = 2) -> list[str]:
    days = []
    dt = datetime.now()
    while len(days) < n:
        if dt.weekday() < 5:
            days.append(dt.strftime("%Y%m%d"))
        dt -= timedelta(days=1)
    return days


def fetch_etf_top20(top_n: int = 20) -> tuple[pd.DataFrame | None, str]:
    trading_days = _get_recent_trading_days(2)
    today_str, prev_str = trading_days[0], trading_days[1]
    date_label = f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]}"

    print(f"[ETF] 조회일: {today_str} / 전일: {prev_str}")

    df_today = stock.get_etf_ohlcv_by_ticker(today_str)
    print(f"[ETF] 오늘 데이터: {len(df_today)}행, 컬럼: {df_today.columns.tolist() if not df_today.empty else '없음'}")

    df_prev = stock.get_etf_ohlcv_by_ticker(prev_str)
    print(f"[ETF] 전일 데이터: {len(df_prev)}행")

    # 오늘 데이터가 없으면(장 시작 전) 전일 기준으로 변경
    if df_today.empty:
        print("[ETF] 오늘 데이터 없음 → 전일 데이터로 대체")
        trading_days = _get_recent_trading_days(3)
        today_str, prev_str = trading_days[1], trading_days[2]
        date_label = f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]} (전일 기준)"
        df_today = stock.get_etf_ohlcv_by_ticker(today_str)
        df_prev = stock.get_etf_ohlcv_by_ticker(prev_str)
        print(f"[ETF] 대체 데이터: {len(df_today)}행")

    if df_today.empty or df_prev.empty:
        return None, date_label

    # 종가 컬럼명 확인 (pykrx 버전에 따라 다를 수 있음)
    close_col = '종가' if '종가' in df_today.columns else df_today.columns[4]
    vol_col = '거래량' if '거래량' in df_today.columns else df_today.columns[5]
    print(f"[ETF] 종가 컬럼: {close_col}, 거래량 컬럼: {vol_col}")

    common = df_today.index.intersection(df_prev.index)
    close_today = df_today.loc[common, close_col]
    close_prev = df_prev.loc[common, close_col]

    valid_prev = close_prev[close_prev > 0]
    common = valid_prev.index.intersection(close_today.index)
    returns = (close_today[common] - valid_prev[common]) / valid_prev[common] * 100

    result = pd.DataFrame({
        'close': close_today[common],
        'return': returns,
        'volume': df_today.loc[common, vol_col],
    })

    top = result.sort_values('return', ascending=False).head(top_n).copy()
    print(f"[ETF] 상위 {len(top)}개 추출 완료")

    names = {}
    for ticker in top.index:
        try:
            names[ticker] = stock.get_etf_ticker_name(ticker)
        except Exception:
            names[ticker] = ticker
    top['name'] = pd.Series(names)

    return top, date_label
