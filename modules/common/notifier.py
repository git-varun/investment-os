import os

import requests


class Notifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send_telegram(self, message: str):
        if not self.token or not self.chat_id:
            print("⚠️ Telegram Notifier: Missing API Key or Chat ID.")
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                print(f"✅ Telegram Sent: {message[:50]}...")
            else:
                print(f"⚠️ Telegram API Error: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"⚠️ Telegram Failed: {e}")
