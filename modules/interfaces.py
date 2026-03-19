from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AssetSource(ABC):
    @abstractmethod
    def fetch_holdings(self) -> List[Dict[str, Any]]:
        """Must return:[{'symbol': str, 'qty': float, 'source': str, 'type': str}]"""
        pass


class NewsProvider(ABC):
    @abstractmethod
    def fetch_headlines(self, symbol: str) -> str:
        """Must return a string of headlines. Return empty string if failed."""
        pass


class PriceProvider(ABC):
    @abstractmethod
    def get_price(self, symbol: str, asset_type: str) -> Optional[float]:
        """Must return the live price as a float, or None if not found/error."""
        pass


class AIModel(ABC):
    @abstractmethod
    def analyze_briefing(self, context: str) -> Any:
        """Must return a structured analysis object"""
        pass
