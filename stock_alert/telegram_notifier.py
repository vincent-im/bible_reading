import requests
from datetime import datetime


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str) -> bool:
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"[Telegram 전송 실패] {e}")
            return False

    def send_sell_alert(self, ticker: str, signal_type: str, message: str,
                        current_price: float, buy_price: float, change_pct: float,
                        daily_change_pct: float = 0.0, name: str = ""):
        icon_map = {
            "STOP_LOSS":        "🔴",
            "TAKE_PROFIT":      "🟢",
            "RSI_OVERBOUGHT":   "🟡",
            "MACD_DEATH_CROSS": "🟠",
            "BELOW_MA20":       "🟠",
        }
        icon = icon_map.get(signal_type, "⚠️")
        sign = "+" if change_pct >= 0 else ""
        d_sign = "+" if daily_change_pct >= 0 else ""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        display = f"{name} ({ticker})" if name else ticker

        text = (
            f"{icon} <b>[매도 시그널] {display}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 1단계: 당일 변동 {d_sign}{daily_change_pct:.2f}%\n"
            f"📌 2단계: {signal_type}\n"
            f"📋 내용: {message}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 매수가: {buy_price:,.2f}\n"
            f"💹 현재가: {current_price:,.2f} ({sign}{change_pct:.2f}%)\n"
            f"🕐 시각: {now}"
        )
        return self.send_message(text)

    def send_startup_message(self, watchlist: list[dict]):
        lines = [f"<b>📡 주식 매도 알림 시작</b>", "━━━━━━━━━━━━━━━━━━", "모니터링 종목:"]
        for item in watchlist:
            name = item.get("name", "")
            display = f"{name} ({item['ticker']})" if name else item['ticker']
            lines.append(
                f"  • {display} | 매수가: {item['buy_price']:,.2f}"
                + (f" | 손절: -{item['stop_loss_pct']}%" if 'stop_loss_pct' in item else "")
                + (f" | 목표: +{item['take_profit_pct']}%" if 'take_profit_pct' in item else "")
            )
        lines.append("━━━━━━━━━━━━━━━━━━")
        self.send_message("\n".join(lines))

    def send_etf_report(self, df: "pd.DataFrame", date_label: str) -> bool:
        now = datetime.now().strftime("%H:%M")
        lines = [
            f"<b>📊 국내 ETF 수익률 TOP 20</b>",
            "━━━━━━━━━━━━━━━━━━",
            f"📅 {date_label} {now} 기준\n",
        ]
        for i, (ticker, row) in enumerate(df.iterrows(), 1):
            name = str(row.get('name', ticker))
            # 이름이 너무 길면 자르기
            if len(name) > 16:
                name = name[:15] + "…"
            ret = row['return']
            close = int(row['close'])
            sign = "+" if ret >= 0 else ""
            lines.append(
                f"{i:2d}위  {name:<16}  {sign}{ret:.2f}%  {close:,}원"
            )
        lines.append("\n━━━━━━━━━━━━━━━━━━")
        return self.send_message("\n".join(lines))

    def validate(self) -> bool:
        """봇 토큰과 채팅 ID가 유효한지 확인합니다."""
        try:
            resp = requests.get(f"{self.base_url}/getMe", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("ok"):
                bot_name = data["result"]["username"]
                print(f"[Telegram] 봇 연결 성공: @{bot_name}")
                return True
        except requests.RequestException as e:
            print(f"[Telegram] 연결 실패: {e}")
        return False
