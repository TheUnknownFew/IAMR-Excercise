from .market import MarketMap
from .bin import Bin, PriceCode, price_codes
from .vendor import Vendor

cache_stalls_from_database = MarketMap.cache_stalls_from_database
_market_map: MarketMap


def init_market():
    global _market_map
    _market_map = MarketMap()


def get_market_map() -> MarketMap:
    return _market_map
