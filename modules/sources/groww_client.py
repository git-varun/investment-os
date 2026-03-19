import logging
import os

from modules.interfaces import AssetSource


class GrowwSync(AssetSource):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = os.getenv("GROWW_API_KEY")
        self.api_secret = os.getenv("GROWW_API_SECRET")
        self.api = None

        if self.api_key and self.api_secret:
            self._authenticate()
        else:
            self.logger.warning("⚠️ Groww Source: Missing API_KEY or SECRET in .env")

    def _authenticate(self):
        """Exchanges Key/Secret for an active session token."""
        try:
            from growwapi import GrowwAPI
            access_token = GrowwAPI.get_access_token(
                api_key=self.api_key,
                secret=self.api_secret
            )
            self.api = GrowwAPI(access_token)
            self.logger.info("✅ Groww Source: Authenticated")
        except ImportError:
            self.logger.error("❌ Groww Source: 'growwapi' library not installed.")
        except Exception as e:
            self.logger.error(f"❌ Groww Source: Auth Failed -> {e}")

    def fetch_holdings(self):
        """Implements the AssetSource contract."""
        if not self.api:
            self._authenticate()
            if not self.api: return []

        try:
            response = self.api.get_holdings_for_user(timeout=10)
            raw = response.get("holdings", [])
            return [{
                "symbol": f"{item.get('trading_symbol')}.NS",
                "qty": float(item.get("quantity", 0)),
                "source": "groww",
                "type": "stock"
            } for item in raw]
        except Exception as e:
            self.logger.error(f"⚠️ Groww Fetch Error: {e}")
            return []
