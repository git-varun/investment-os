# modules/__init__.py

import os
import sys

# Adds the parent directory to the path so 'modules' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Interfaces
from .interfaces import AssetSource, NewsProvider, AIModel
# Sources
from .sources.groww_client import GrowwSync
from .sources.binance_client import BinanceSync

# Intelligence
from .intelligence.news_engine import NewsEngine
from .intelligence.gemini_agent import GeminiFlash

# Common Tools
from .common.valuator import PortfolioValuator
from .common.notifier import Notifier

# UI
from .ui.rich_tui import PortfolioTUI
