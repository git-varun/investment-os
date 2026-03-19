import logging
import os

from binance.client import Client

from modules.interfaces import AssetSource


class BinanceSync(AssetSource):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_SECRET")
        self.client = None

        if self.api_key and self.api_secret and Client:
            try:
                self.client = Client(self.api_key, self.api_secret)
            except Exception as e:
                self.logger.error(f"⚠️ Binance Init Error: {e}")
        elif not Client:
            self.logger.error("❌ Binance Source: 'python-binance' library not installed.")
        else:
            self.logger.warning("⚠️ Binance Source: Missing API_KEY or SECRET in .env")

    def fetch_holdings(self):
        """Implements the AssetSource contract with symbol cleaning."""
        if not self.client:
            return []
        try:
            account = self.client.get_account()
            balances = []
            for asset in account['balances']:
                qty = float(asset['free']) + float(asset['locked'])

                if qty > 0.0001:
                    raw_name = asset['asset']

                    # 1. Strip Earn/Staking Prefixes
                    clean_name = raw_name
                    if raw_name.startswith("LD") and len(raw_name) > 2:
                        clean_name = raw_name[2:]
                    elif raw_name.startswith("BN") and raw_name != "BNB":
                        clean_name = raw_name[2:]

                    # 2. 2026 Symbol Mapping
                    mapping = {"POL": "MATIC", "S": "SONIC"}
                    clean_name = mapping.get(clean_name, clean_name)

                    balances.append({
                        "symbol": f"{clean_name}-USD",
                        "qty": qty,
                        "source": "binance",
                        "type": "crypto"
                    })
            return balances
        except Exception as e:
            print(f"⚠️ Binance Source Error: {e}")
            return []
