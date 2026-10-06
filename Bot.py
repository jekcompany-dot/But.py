import os
import time
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "TRXUSDT", "LTCUSDT", "BCHUSDT", "ATOMUSDT", "NEARUSDT",
    "UNIUSDT", "ETCUSDT", "FILUSDT", "APTUSDT", "ARBUSDT",
    "OPUSDT", "SUIUSDT", "INJUSDT", "AAVEUSDT", "SEIUSDT",
    "PEPEUSDT", "SHIBUSDT", "WIFUSDT", "FETUSDT", "RENDERUSDT",
    "TIAUSDT", "IMXUSDT", "STXUSDT", "MATICUSDT", "ALGOUSDT"
]

BINANCE_URL = "https://api.binance.com/api/v3/klines"


def get_klines(symbol, interval="1h", limit=100):
    try:
        r = requests.get(
            BINANCE_URL,
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            },
            timeout=15
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": text
            },
            timeout=15
        )
    except Exception:
        pass


def get_chat_ids():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    try:
        r = requests.get(url, timeout=15)
        data = r.json()

        chat_ids = set()

        for update in data.get("result", []):
            message = update.get("message")

            if message:
                chat = message.get("chat")
                if chat:
                    chat_ids.add(str(chat["id"]))

        return list(chat_ids)

    except Exception:
        return []


def analyze_symbol(symbol):
    candles = get_klines(symbol)

    if not candles:
        return None

    closes = [float(x[4]) for x in candles]
    volumes = [float(x[5]) for x in candles]

    price = closes[-1]
    rsi = calculate_rsi(closes)

    if rsi is None:
        return None

    avg_volume = sum(volumes[-21:-1]) / 20
    current_volume = volumes[-1]

    volume_ratio = current_volume / avg_volume if avg_volume else 0

    signal = None

    # Oversold + volume increase
    if rsi <= 30 and volume_ratio >= 1.5:
        signal = "🟢 احتمال برگشت صعودی"

    # Overbought + volume increase
    elif rsi >= 70 and volume_ratio >= 1.5:
        signal = "🔴 احتمال برگشت نزولی"

    if signal:
        return (
            f"{signal}\n\n"
            f"💰 {symbol}\n"
            f"Price: {price:.6f}\n"
            f"RSI: {rsi:.1f}\n"
            f"Volume: {volume_ratio:.1f}x میانگین\n"
            f"⏱ تایم‌فریم: 1H"
        )

    return None


def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN پیدا نشد.")
        return

    chat_ids = get_chat_ids()

    if not chat_ids:
        print("هیچ چتی پیدا نشد. ابتدا در تلگرام /start بفرست.")
        return

    alerts = []

    for symbol in SYMBOLS:
        result = analyze_symbol(symbol)

        if result:
            alerts.append(result)

        time.sleep(0.2)

    if not alerts:
        message = "🔎 بررسی انجام شد.\n\nفعلاً هیچ سیگنال قوی پیدا نشد."
    else:
        message = "🚨 هشدارهای واچ‌لیست\n\n"
        message += "\n\n━━━━━━━━━━━━\n\n".join(alerts)

    for chat_id in chat_ids:
        send_message(chat_id, message)

    print("Scan completed.")


if __name__ == "__main__":
    main()
