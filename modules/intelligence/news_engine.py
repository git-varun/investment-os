from typing import List

from modules.interfaces import NewsProvider


class NewsEngine(NewsProvider):
    """Acts as a centralized hub that loops through registered News Providers."""

    def __init__(self, providers: List[NewsProvider]):
        self.providers = providers

    def fetch_headlines(self, symbol: str) -> str:
        # Tries each provider until one successfully returns news
        for provider in self.providers:
            headlines = provider.fetch_headlines(symbol)
            if headlines and len(headlines.strip()) > 5:
                return headlines
        return ""
