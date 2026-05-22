import requests
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd

_NAVER_ETF_URL = "https://finance.naver.com/api/sise/etfItemList.naver"
_NAVER_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ETFBot/1.0)"}


def _get_recent_trading_days(n: int = 2) -> list[str]:
    days = []
    dt = datetime.now()
    while len(days) < n:
        if dt.weekday() < 5:
            days.append(dt.strftime("%Y%m%d"))
        dt -= timedelta(days=1)
    return days


def _last_weekday(dt: datetime) -> datetime:
    while dt.weekday() >= 5:
        dt -= timedelta(days=1)
    return dt


def _calc_etf_returns(df_end: pd.DataFrame, df_start: pd.DataFrame, top_n: int) -> "pd.DataFrame | None":
    common = df_end.index.intersection(df_start.index)
    close_end = df_end.loc[common, '종가']
    close_start = df_start.loc[common, '종가']

    valid_start = close_start[close_start > 0]
    common = valid_start.index.intersection(close_end.index)
    if common.empty:
        return None

    returns = (close_end[common] - valid_start[common]) / valid_start[common] * 100
    result = pd.DataFrame({
        'close': close_end[common],
        'return': returns,
        'volume': df_end.loc[common, '거래량'],
    })

    top = result.sort_values('return', ascending=False).head(top_n).copy()
    names = {}
    for ticker in top.index:
        try:
            names[ticker] = stock.get_etf_ticker_name(ticker)
        except Exception:
            names[ticker] = ticker
    top['name'] = pd.Series(names)
    return top


def _fetch_etf_top20_naver(top_n: int = 20) -> tuple["pd.DataFrame | None", str]:
    """네이버금융 API로 장중 실시간 ETF 수익률 상위 top_n 반환 (명칭은 pykrx 조회)"""
    try:
        resp = requests.get(_NAVER_ETF_URL, headers=_NAVER_HEADERS, timeout=10)
        resp.raise_for_status()
        items = resp.json().get("result", {}).get("etfItemList", [])
    except Exception as e:
        print(f"[Naver ETF] 요청 실패: {e}")
        return None, ""

    if not items:
        print("[Naver ETF] 데이터 없음")
        return None, ""

    records = []
    for item in items:
        try:
            change_rate = float(item.get("changeRate", 0) or 0)
            now_val = float(item.get("nowVal", 0) or 0)
            if now_val <= 0:
                continue
            records.append({
                'ticker': str(item['itemcode']),
                'close': now_val,
                'return': change_rate,
                'volume': int(item.get('quant', 0) or 0),
            })
        except (KeyError, ValueError, TypeError):
            continue

    if not records:
        return None, ""

    df = pd.DataFrame(records).set_index('ticker')
    top = df.sort_values('return', ascending=False).head(top_n).copy()

    # pykrx로 공식 KRX ETF 명칭 조회 (상위 top_n개만)
    names = {}
    for ticker in top.index:
        try:
            names[ticker] = stock.get_etf_ticker_name(ticker)
        except Exception:
            names[ticker] = ticker
    top['name'] = pd.Series(names)

    date_label = datetime.now().strftime("%Y-%m-%d")
    print(f"[Naver ETF] {len(records)}개 ETF 수신, 상위 {len(top)}개 추출")
    return top, date_label


def _fetch_etf_top20_pykrx(top_n: int = 20) -> tuple["pd.DataFrame | None", str]:
    trading_days = _get_recent_trading_days(2)
    today_str, prev_str = trading_days[0], trading_days[1]
    date_label = f"{today_str[:4]}-{today_str[4:6]}-{today_str[6:]}"

    df_today = stock.get_etf_ohlcv_by_ticker(today_str)
    df_prev = stock.get_etf_ohlcv_by_ticker(prev_str)

    if df_today.empty or df_prev.empty:
        print(f"[pykrx] {today_str} 데이터 없음 (장중이거나 휴장)")
        return None, date_label

    top = _calc_etf_returns(df_today, df_prev, top_n)
    return top, date_label


def fetch_etf_top20(top_n: int = 20) -> tuple["pd.DataFrame | None", str]:
    """
    국내 ETF 당일 수익률 상위 top_n 반환.
    네이버금융(실시간) -> pykrx(EOD) 순으로 시도.
    """
    top, date_label = _fetch_etf_top20_naver(top_n)
    if top is not None and not top.empty:
        return top, date_label

    print("[Naver ETF] 실패, pykrx 폴백 시도")
    return _fetch_etf_top20_pykrx(top_n)


def fetch_etf_weekly_top20(top_n: int = 20) -> tuple["pd.DataFrame | None", str]:
    now = datetime.now()
    days_since_fri = (now.weekday() - 4) % 7
    this_friday = _last_weekday(now - timedelta(days=days_since_fri))
    last_friday = _last_weekday(this_friday - timedelta(days=7))

    this_str = this_friday.strftime("%Y%m%d")
    last_str = last_friday.strftime("%Y%m%d")
    date_label = f"{this_friday.strftime('%Y-%m-%d')} 주간"

    df_this = stock.get_etf_ohlcv_by_ticker(this_str)
    df_last = stock.get_etf_ohlcv_by_ticker(last_str)

    if df_this.empty or df_last.empty:
        return None, date_label

    top = _calc_etf_returns(df_this, df_last, top_n)
    return top, date_label


def fetch_etf_monthly_top20(top_n: int = 20) -> tuple["pd.DataFrame | None", str]:
    now = datetime.now()
    first_of_this_month = now.replace(day=1)
    last_of_prev_month = first_of_this_month - timedelta(days=1)
    first_of_prev_month = last_of_prev_month.replace(day=1)
    last_of_prev_prev_month = first_of_prev_month - timedelta(days=1)

    end_dt = _last_weekday(last_of_prev_month)
    start_dt = _last_weekday(last_of_prev_prev_month)

    end_str = end_dt.strftime("%Y%m%d")
    start_str = start_dt.strftime("%Y%m%d")
    date_label = f"{last_of_prev_month.strftime('%Y-%m')} 월간"

    df_end = stock.get_etf_ohlcv_by_ticker(end_str)
    df_start = stock.get_etf_ohlcv_by_ticker(start_str)

    if df_end.empty or df_start.empty:
        return None, date_label

    top = _calc_etf_returns(df_end, df_start, top_n)
    return top, date_label
