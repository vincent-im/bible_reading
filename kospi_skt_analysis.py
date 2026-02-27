"""
KOSPI 지수(KS11) & SK텔레콤(017670) 주가 분석
================================================
- FinanceDataReader로 실시간 데이터 수집
- MA5 / MA20 이동평균선
- 골든크로스 · 데드크로스 감지 및 시각화
- 일별 수익률 분포 히스토그램
의존 패키지 설치:
    pip install finance-datareader matplotlib pandas scipy
"""
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from datetime import datetime, timedelta
from matplotlib import font_manager
# ── 한글 폰트 자동 감지 ───────────────────────────────────────
plt.rcParams['axes.unicode_minus'] = False
for _f in font_manager.findSystemFonts():
    if any(k in _f for k in ['Nanum', 'nanum', 'Gothic', 'gothic', 'Malgun', 'malgun']):
        font_manager.fontManager.addfont(_f)
        plt.rcParams['font.family'] = font_manager.FontProperties(fname=_f).get_name()
        break
# ════════════════════════════════════════════════════════════════
# 1.  데이터 수집  (FinanceDataReader)
# ════════════════════════════════════════════════════════════════
import FinanceDataReader as fdr
end   = datetime.today()
start = end - timedelta(days=365)
print("데이터 수집 중...")
df_kospi = fdr.DataReader('KS11',   start, end)   # KOSPI 지수
df_skt   = fdr.DataReader('017670', start, end)   # SK텔레콤
print(f"  KOSPI  : {len(df_kospi)}일  ({df_kospi.index[0].date()} ~ {df_kospi.index[-1].date()})")
print(f"  SK텔레콤: {len(df_skt)}일  ({df_skt.index[0].date()} ~ {df_skt.index[-1].date()})")
# ════════════════════════════════════════════════════════════════
# 2.  이동평균 계산
# ════════════════════════════════════════════════════════════════
for df in [df_kospi, df_skt]:
    df['MA5']  = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
# ════════════════════════════════════════════════════════════════
# 3.  골든크로스 / 데드크로스 감지
#     MA5가 MA20을 상향 돌파 → 골든크로스
#     MA5가 MA20을 하향 돌파 → 데드크로스
# ════════════════════════════════════════════════════════════════
def find_crosses(df: pd.DataFrame):
    """
    Returns
    -------
    golden_dates : DatetimeIndex  (MA5가 MA20을 상향 돌파한 날)
    dead_dates   : DatetimeIndex  (MA5가 MA20을 하향 돌파한 날)
    """
    signal = (df['MA5'] > df['MA20']).astype(int)
    diff   = signal.diff()
    golden = df.index[diff ==  1]
    dead   = df.index[diff == -1]
    return golden, dead
kospi_gc, kospi_dc = find_crosses(df_kospi)
skt_gc,   skt_dc   = find_crosses(df_skt)
# ── 콘솔 출력 ──────────────────────────────────────────────────
def print_cross_summary(name, df, gc, dc, unit=''):
    ret = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100
    print(f"\n{'='*55}")
    print(f"  {name}")
    print(f"  기간 수익률 : {ret:+.2f}%")
    print(f"  골든크로스  : {len(gc)}회  |  데드크로스 : {len(dc)}회")
    for d in gc:
        print(f"    ▲ Golden Cross  {d.date()}  {df.loc[d,'Close']:,.1f}{unit}")
    for d in dc:
        print(f"    ▼ Dead   Cross  {d.date()}  {df.loc[d,'Close']:,.1f}{unit}")
print_cross_summary('KOSPI 지수 (KS11)',       df_kospi, kospi_gc, kospi_dc, 'p')
print_cross_summary('SK텔레콤 (017670)',        df_skt,   skt_gc,   skt_dc,   '원')
# ════════════════════════════════════════════════════════════════
# 4.  차트 시각화  (4-row layout)
#     Row 0 : 누적 수익률 비교
#     Row 1 : KOSPI 지수 + MA + 크로스 마커
#     Row 2 : SK텔레콤 주가 + MA + 크로스 마커
#     Row 3 : 일별 수익률 분포 히스토그램
# ════════════════════════════════════════════════════════════════
# ── 다크 테마 팔레트 ──────────────────────────────────────────
BG      = '#0D1117'
PANEL   = '#161B22'
CELL    = '#21262D'
BORDER  = '#30363D'
TXT     = '#E6EDF3'
TXT_DIM = '#8B949E'
C_KOSPI = '#7EE787'   # 연두
C_SKT   = '#D2A8FF'   # 라벤더
C_MA5   = '#58A6FF'   # 하늘
C_MA20  = '#FFA657'   # 주황
C_GC    = '#FFD700'   # 골든크로스 (금색)
C_DC    = '#FF4444'   # 데드크로스 (빨강)
C_ZERO  = '#484F58'   # 기준선
date_fmt = mdates.DateFormatter("'%y.%m")
def style_ax(ax: plt.Axes) -> None:
    """공통 다크 테마 적용"""
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=TXT_DIM, labelsize=9.5)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.grid(color=CELL, lw=0.8, alpha=0.9)
    ax.xaxis.set_major_formatter(date_fmt)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
fig = plt.figure(figsize=(18, 21), facecolor=BG)
gs  = fig.add_gridspec(4, 1,
                        height_ratios=[1.0, 1.4, 1.4, 0.6],
                        hspace=0.38)
# ─────────────────────────────────────────────────────────────
# [Row 0]  누적 수익률 비교
# ─────────────────────────────────────────────────────────────
ax0 = fig.add_subplot(gs[0])
style_ax(ax0)
k_ret = (df_kospi['Close'] / df_kospi['Close'].iloc[0] - 1) * 100
s_ret = (df_skt['Close']   / df_skt['Close'].iloc[0]   - 1) * 100
ax0.plot(df_kospi.index, k_ret, color=C_KOSPI, lw=2.2,
         label=f'KOSPI (KS11)       최종 {k_ret.iloc[-1]:+.1f}%')
ax0.plot(df_skt.index,   s_ret, color=C_SKT,   lw=2.2,
         label=f'SK텔레콤 (017670)  최종 {s_ret.iloc[-1]:+.1f}%')
ax0.axhline(0, color=C_ZERO, lw=1.2, ls='--', alpha=0.8)
ax0.fill_between(df_kospi.index, k_ret, 0, alpha=0.10, color=C_KOSPI)
ax0.fill_between(df_skt.index,   s_ret, 0, alpha=0.10, color=C_SKT)
for df_t, ret_ts, c in [(df_kospi, k_ret, C_KOSPI), (df_skt, s_ret, C_SKT)]:
    ax0.annotate(f'{ret_ts.iloc[-1]:+.1f}%',
                 xy=(df_t.index[-1], ret_ts.iloc[-1]),
                 xytext=(10, 2), textcoords='offset points',
                 fontsize=12, fontweight='bold', color=c,
                 bbox=dict(boxstyle='round,pad=0.3', fc=PANEL, ec=c, lw=1.2))
ax0.set_title('누적 수익률 비교  |  KOSPI vs SK텔레콤 (1Y)',
              color=TXT, fontsize=14, fontweight='bold', pad=12)
ax0.set_ylabel('수익률 (%)', color=TXT_DIM, fontsize=10)
ax0.legend(facecolor=CELL, edgecolor=BORDER,
           labelcolor=TXT, fontsize=10.5, loc='lower right')
# ─────────────────────────────────────────────────────────────
# 공통 보조함수 : 주가(지수) + MA + 크로스 마커
# ─────────────────────────────────────────────────────────────
def plot_price_panel(ax: plt.Axes,
                     df: pd.DataFrame,
                     gc, dc,
                     title: str,
                     c_main: str,
                     y_label: str = '주가 (원)') -> None:
    style_ax(ax)
    # 주가 / 지수
    ax.plot(df.index, df['Close'], color=c_main, lw=1.9,
            label='종가', zorder=2)
    # 이동평균선
    ax.plot(df.index, df['MA5'],   color=C_MA5,  lw=1.3, ls='--',
            alpha=0.85, label='MA5',  zorder=3)
    ax.plot(df.index, df['MA20'],  color=C_MA20, lw=1.7,
            alpha=0.95, label='MA20', zorder=3)
    # MA5/MA20 교차 구간 배경 음영
    above = df['MA5'] >= df['MA20']
    ax.fill_between(df.index, df['MA5'], df['MA20'],
                    where=above,  alpha=0.07, color=C_GC, zorder=1)
    ax.fill_between(df.index, df['MA5'], df['MA20'],
                    where=~above, alpha=0.07, color=C_DC, zorder=1)
    MAX_MARKERS = 8   # 마커 최대 개수 (겹침 방지)
    # 골든크로스 마커
    for d in gc[:MAX_MARKERS]:
        if d in df.index:
            p = df.loc[d, 'Close']
            ax.scatter(d, p, color=C_GC, s=150, zorder=6,
                       marker='^', edgecolors=BG, linewidths=0.9)
            ax.annotate(f'GC\n{d.strftime("%m/%d")}',
                        xy=(d, p), xytext=(0, 24),
                        textcoords='offset points', ha='center',
                        fontsize=8, color=C_GC, fontweight='bold',
                        arrowprops=dict(arrowstyle='->', color=C_GC, lw=0.9))
    # 데드크로스 마커
    for d in dc[:MAX_MARKERS]:
        if d in df.index:
            p = df.loc[d, 'Close']
            ax.scatter(d, p, color=C_DC, s=150, zorder=6,
                       marker='v', edgecolors=BG, linewidths=0.9)
            ax.annotate(f'DC\n{d.strftime("%m/%d")}',
                        xy=(d, p), xytext=(0, -26),
                        textcoords='offset points', ha='center',
                        fontsize=8, color=C_DC, fontweight='bold',
                        arrowprops=dict(arrowstyle='->', color=C_DC, lw=0.9))
    ax.set_title(title, color=TXT, fontsize=13, fontweight='bold', pad=10)
    ax.set_ylabel(y_label, color=TXT_DIM, fontsize=10)
    ax.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda v, _: f'{v:,.0f}'))
    h, l = ax.get_legend_handles_labels()
    gc_p = mpatches.Patch(color=C_GC, label=f'골든크로스 ▲  {len(gc)}회')
    dc_p = mpatches.Patch(color=C_DC, label=f'데드크로스 ▼  {len(dc)}회')
    ax.legend(handles=h + [gc_p, dc_p],
              facecolor=CELL, edgecolor=BORDER,
              labelcolor=TXT, fontsize=9.5, loc='upper right',
              framealpha=0.92)
# ─────────────────────────────────────────────────────────────
# [Row 1]  KOSPI
# ─────────────────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[1])
plot_price_panel(ax1, df_kospi, kospi_gc, kospi_dc,
                 'KOSPI 지수 (KS11)  |  지수 + MA5/MA20 + 크로스 시그널',
                 C_KOSPI, y_label='지수 포인트')
# ─────────────────────────────────────────────────────────────
# [Row 2]  SK텔레콤
# ─────────────────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[2])
plot_price_panel(ax2, df_skt, skt_gc, skt_dc,
                 'SK텔레콤 (017670)  |  주가 + MA5/MA20 + 크로스 시그널',
                 C_SKT, y_label='주가 (원)')
# ─────────────────────────────────────────────────────────────
# [Row 3]  일별 수익률 분포 히스토그램
# ─────────────────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[3])
ax3.set_facecolor(PANEL)
ax3.tick_params(colors=TXT_DIM, labelsize=9)
for s in ax3.spines.values():
    s.set_color(BORDER)
ax3.grid(color=CELL, lw=0.8, alpha=0.8, axis='y')
k_daily = df_kospi['Close'].pct_change().dropna() * 100
s_daily = df_skt['Close'].pct_change().dropna()   * 100
bins = np.linspace(-3.5, 3.5, 50)
ax3.hist(k_daily, bins=bins, color=C_KOSPI, alpha=0.5,
         label=f'KOSPI   σ={k_daily.std():.2f}%', edgecolor='none')
ax3.hist(s_daily, bins=bins, color=C_SKT,   alpha=0.5,
         label=f'SK텔레콤 σ={s_daily.std():.2f}%', edgecolor='none')
ax3.axvline(0, color=C_ZERO, lw=1.2, ls='--')
ax3.set_title('일별 수익률 분포  (Daily Return Distribution)',
              color=TXT, fontsize=11, fontweight='bold', pad=8)
ax3.set_xlabel('일별 수익률 (%)', color=TXT_DIM, fontsize=9.5)
ax3.set_ylabel('빈도', color=TXT_DIM, fontsize=9.5)
ax3.legend(facecolor=CELL, edgecolor=BORDER,
           labelcolor=TXT, fontsize=9.5)
# ── 하단 주석 ─────────────────────────────────────────────────
fig.text(
    0.5, 0.003,
    f"분석 기간: {start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}  |  "
    "▲ Golden Cross: MA5 ↑ MA20 상향돌파  |  "
    "▼ Dead Cross: MA5 ↓ MA20 하향돌파  |  "
    "Data: FinanceDataReader",
    ha='center', color='#484F58', fontsize=8.5)
# ════════════════════════════════════════════════════════════════
# 5.  저장
# ════════════════════════════════════════════════════════════════
import os
out_path = os.path.join(os.path.dirname(__file__), 'kospi_skt_analysis.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight',
            facecolor=fig.get_facecolor())
print(f'\n차트 저장 완료 → {out_path}')
plt.show()
