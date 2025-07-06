# factory.py
from .binance import BinanceExchange
from .bybit import BybitExchange
from .gateio import GateioExchange


class ExchangeFactory:
    """
    Factory class to create exchange instances
    """
    
    _exchanges = {
        'binance': BinanceExchange,
        'bybit': BybitExchange,
        'gateio': GateioExchange,
    }
    
    @classmethod
    def create_exchange(cls, exchange_type, credentials):
        """
        Create an exchange instance based on exchange type
        
        Args:
            exchange_type (str): Type of exchange (e.g., 'binance', 'bybit')
            credentials (dict): Exchange API credentials
            
        Returns:
            Exchange instance
            
        Raises:
            ValueError: If exchange type is not supported
        """
        if exchange_type not in cls._exchanges:
            supported = ', '.join(cls._exchanges.keys())
            raise ValueError(f"Unsupported exchange type: {exchange_type}. Supported: {supported}")
        
        exchange_class = cls._exchanges[exchange_type]
        return exchange_class(credentials)
    
    @classmethod
    def get_supported_exchanges(cls):
        """
        Get list of supported exchange types
        
        Returns:
            list: List of supported exchange types
        """
        return list(cls._exchanges.keys()) 