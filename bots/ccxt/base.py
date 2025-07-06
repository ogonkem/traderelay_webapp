from abc import ABC, abstractmethod

class BaseExchange(ABC):
    """
    Base class for all exchange integrations
    """
    
    def __init__(self, credentials):
        self.credentials = credentials
        self.connected = False
    
    @abstractmethod
    def connect(self):
        """Initialize connection to exchange"""
        pass
    
    @abstractmethod
    def place_order(self, symbol, side, amount, order_type="market", price=None):
        """Place an order on the exchange"""
        pass
    
    @abstractmethod
    def get_balance(self):
        """Get account balance"""
        pass
    
    @abstractmethod
    def get_ticker(self, symbol):
        """Get current ticker for symbol"""
        pass
    
    def validate_credentials(self):
        """Validate that required credentials are present"""
        required_fields = ['api_key', 'api_secret']
        for field in required_fields:
            if field not in self.credentials:
                raise ValueError(f"Missing required credential: {field}")
    
    def is_connected(self):
        """Check if exchange is connected"""
        return self.connected 