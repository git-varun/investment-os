from typing import List

import yfinance as yf

from modules.interfaces import PriceProvider


class PortfolioValuator:
    def __init__(self, pricers: List[PriceProvider]):
        self.usd_inr_ticker = "USDINR=X"
        self._price_cache = {}
        self.pricers = pricers

    def get_live_fx(self):
        try:
            return yf.Ticker(self.usd_inr_ticker).fast_info['last_price']
        except:
            return 83.50  # 2026 Fallback

    def get_price(self, asset: dict) -> float:
        symbol = asset['symbol']
        asset_type = asset.get('type', 'stock')

        if symbol in self._price_cache:
            return self._price_cache[symbol]

        price = 0.0

        # 1. 1:1 Static Assets
        if asset_type in ['fixed_income', 'cash']:
            price = 1.0

            # 2. Commodities (Gold)
        elif symbol == "GOLD":
            try:
                gold_usd_oz = yf.Ticker("GC=F").fast_info['last_price']
                price = (gold_usd_oz * self.get_live_fx()) / 31.1034768
            except:
                price = 6500.0  # Safe fallback

        # 3. Dynamic Assets (Stocks & Crypto) -> Route through our Fallback Chain
        else:
            for pricer in self.pricers:
                fetched_price = pricer.get_price(symbol, asset_type)
                if fetched_price is not None and fetched_price > 0:
                    price = fetched_price
                    break  # Success! Stop querying other providers.

        self._price_cache[symbol] = price
        return price

    def calculate_total(self, assets):
        fx_rate = self.get_live_fx()
        total_inr = 0.0
        self._price_cache.clear()

        for asset in assets:
            price = self.get_price(asset)
            subtotal = price * asset['qty']

            if "-USD" in asset['symbol'] or asset.get('type') == 'crypto':
                total_inr += (subtotal * fx_rate)
            else:
                total_inr += subtotal

        return total_inr
