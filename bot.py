import json
import os
import sys
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

URL = os.getenv(
    "SIGNALS_URL",
    "https://crypto-signal-scanner.pages.dev/data/signals.json"
)
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
STATE = Path("state/sent_signals.json")
ACTIVE = {"WAITING_TRIGGER", "TRIGGERED"}
MAX_AGE_HOURS = int(os.getenv("MAX_SIGNAL_AGE_HOURS", "24"))


def get_json(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "crypto-signal-telegram-bot/1.0"}
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def send(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    body = json.dumps({
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        result = json.loads(r.read().decode())
    if not result.get("ok"):
        raise RuntimeError(result)


def fmt(value):
    if value is None:
        return "—"
    return f"{value:.8g}" if isinstance(value, float) else str(value)


def make_message(s):
    direction = str(s.get("direction", "")).upper()
    emoji = "🟢" if direction == "LONG" else "🔴" if direction == "SHORT" else "📊"
    zone = s.get("entryZone")
    entry = (
        f"{fmt(zone[0])} – {fmt(zone[1])}"
        if isinstance(zone, list) and len(zone) >= 2
        else fmt(s.get("triggerPrice"))
    )
    ts = s.get("generatedAt")
    when = (
        datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        if isinstance(ts, (int, float)) else "—"
    )
    return "\n".join([
        f"{emoji} {s.get('symbol', 'UNKNOWN')} — {direction}",
        f"Таймфрейм: {s.get('timeframe', '—')}",
        f"Вход: {entry}",
        f"Триггер: {fmt(s.get('triggerPrice'))}",
        f"Stop Loss: {fmt(s.get('stopLoss'))}",
        f"Take Profit: {fmt(s.get('takeProfit'))}",
        f"RR: {fmt(s.get('riskReward'))}",
        f"Score: {fmt(s.get('score'))} | Качество: {s.get('quality', '—')}",
        f"Статус: {s.get('status', '—')}",
        f"Время: {when}",
        f"ID: {s.get('id', '—')}",
        "",
        "Источник: crypto-signal-scanner"
    ])


def main():
    data = get_json(URL)
    if not isinstance(data, dict) or not isinstance(data.get("signals"), list):
        raise ValueError("Ожидался JSON с массивом signals")

    STATE.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {"sent_ids": []}
    sent_ids = set(state.get("sent_ids", []))
    now = datetime.now(timezone.utc).timestamp() * 1000
    count = 0

    for signal in data["signals"]:
        if not isinstance(signal, dict):
            continue
        sid = signal.get("id")
        if not sid or sid in sent_ids or signal.get("status") not in ACTIVE:
            continue

        ts = signal.get("generatedAt")
        if isinstance(ts, (int, float)):
            age = (now - ts) / 3600000
            if age > MAX_AGE_HOURS or age < -1:
                continue

        send(make_message(signal))
        sent_ids.add(sid)
        count += 1
        print("Sent:", sid)

    STATE.write_text(json.dumps({"sent_ids": sorted(sent_ids)}, indent=2) + "\n")
    print(f"Проверено сигналов: {len(data['signals'])}. Отправлено: {count}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
