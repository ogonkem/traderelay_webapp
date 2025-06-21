from .gateio_trader import GateIOTrader

class ExchangeFactory:
    """
    Factory class to create exchange traders
    """
    
    @staticmethod
    def create_trader(exchange_type, credentials):
        """
        Create trader instance based on exchange type
        
        Args:
            exchange_type (str): Exchange type ('gateio', 'binance', 'bybit')
            credentials (dict): API credentials
            
        Returns:
            Trader instance or None
        """
        if exchange_type.lower() == 'gateio':
            api_key = credentials.get('api_key')
            api_secret = credentials.get('api_secret')
            
            if not api_key or not api_secret:
                raise ValueError("Gate.io requires api_key and api_secret")
            
            return GateIOTrader(api_key, api_secret)
        
        elif exchange_type.lower() == 'binance':
            # TODO: Implement Binance trader
            raise NotImplementedError("Binance trader not implemented yet")
        
        elif exchange_type.lower() == 'bybit':
            # TODO: Implement ByBit trader
            raise NotImplementedError("ByBit trader not implemented yet")
        
        else:
            raise ValueError(f"Unsupported exchange type: {exchange_type}")