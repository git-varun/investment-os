import os

import requests
import yfinance as yf
from bs4 import BeautifulSoup

from modules.interfaces import PriceProvider


class BinancePricer(PriceProvider):
    """Fetches purely free real-time crypto prices directly from Binance public API."""

    def get_price(self, symbol: str, asset_type: str):
        if asset_type != "crypto": return None
        try:
            # Convert BTC-USD to BTCUSDT for Binance
            clean_symbol = symbol.replace("-USD", "USDT")
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={clean_symbol}"
            res = requests.get(url, timeout=5).json()
            return float(res['price'])
        except Exception:
            return None


class CoinGeckoPricer(PriceProvider):
    """Free tier CoinGecko API fallback."""

    def get_price(self, symbol: str, asset_type: str):
        if asset_type != "crypto": return None
        try:
            # Map common symbols to CoinGecko IDs
            coin_map = {"MATIC": "polygon", "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}
            clean_sym = symbol.replace("-USD", "")
            cg_id = coin_map.get(clean_sym, clean_sym.lower())

            url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
            res = requests.get(url, timeout=5).json()
            return float(res[cg_id]['usd'])
        except Exception:
            return None


class CoinMarketCapPricer(PriceProvider):
    """Requires CMC_API_KEY in .env. Fails gracefully if missing."""

    def __init__(self):
        self.api_key = os.getenv("CMC_API_KEY")

    def get_price(self, symbol: str, asset_type: str):
        if asset_type != "crypto" or not self.api_key: return None
        try:
            clean_sym = symbol.replace("-USD", "")
            url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
            headers = {'X-CMC_PRO_API_KEY': self.api_key}
            params = {'symbol': clean_sym, 'convert': 'USD'}
            res = requests.get(url, headers=headers, params=params, timeout=5).json()
            return float(res['data'][clean_sym][0]['quote']['USD']['price'])
        except Exception:
            return None


class YFinancePricer(PriceProvider):
    """Standard robust fetcher for Indian Stocks (.NS) and US Equities."""

    def get_price(self, symbol: str, asset_type: str):
        try:
            return float(yf.Ticker(symbol).fast_info['last_price'])
        except Exception:
            return None


class GoogleFinanceScraperPricer(PriceProvider):
    """Emergency fallback for Indian Stocks if YFinance goes down."""

    def get_price(self, symbol: str, asset_type: str):
        if asset_type != "stock": return None
        try:
            clean_sym = symbol.replace(".NS", "")
            url = f"https://www.google.com/finance/quote/{clean_sym}:NSE"
            html = requests.get(url, timeout=5).text
            soup = BeautifulSoup(html, 'html.parser')
            # Google Finance price class is typically "YMlKec fxKbKc"
            price_div = soup.find('div', class_='YMlKec fxKbKc')
            if price_div:
                price_str = price_div.text.replace('₹', '').replace(',', '')
                return float(price_str)
            return None
        except Exception:
            return None
