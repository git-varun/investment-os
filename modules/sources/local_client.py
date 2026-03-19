import json
import logging
import os

from modules.interfaces import AssetSource


class LocalAssetSync(AssetSource):
    """
    Tracks offline or manually entered assets via a local JSON file.
    Follows the AssetSource interface contract perfectly.
    """

    def __init__(self, filepath="data/manual_assets.json"):
        self.logger = logging.getLogger(__name__)
        self.filepath = filepath

    def fetch_holdings(self):
        # Auto-create directory and dummy template if it doesn't exist
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            template = [
                {"symbol": "RELIANCE.NS", "qty": 50, "source": "manual", "type": "stock"},
                {"symbol": "BTC-USD", "qty": 0.5, "source": "manual", "type": "crypto"},
                {"symbol": "GOLD", "qty": 100, "source": "manual", "type": "commodity"},
                {"symbol": "FD-SBI", "qty": 500000, "source": "manual", "type": "fixed_income"}
            ]
            with open(self.filepath, 'w') as f:
                json.dump(template, f, indent=4)
            self.logger.info(f"📁 Created default manual assets file at {self.filepath}")
            return template

        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            self.logger.error(f"⚠️ Local Source Error: {e}")
            return []
