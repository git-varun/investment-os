import urllib.parse

import feedparser

from modules.interfaces import NewsProvider


class GoogleNews(NewsProvider):
    def fetch_headlines(self, symbol: str) -> str:
        try:
            search_term = symbol.split('.')[0] if '.' in symbol else symbol
            query = urllib.parse.quote(f"{search_term} stock market news")
            feed = feedparser.parse(f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en")
            return " | ".join([entry.title for entry in feed.entries[:3]]) if feed.entries else ""
        except:
            return ""


class YahooFinanceNews(NewsProvider):
    def fetch_headlines(self, symbol: str) -> str:
        try:
            feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={symbol}")
            return " | ".join([entry.title for entry in feed.entries[:2]]) if feed.entries else ""
        except:
            return ""
