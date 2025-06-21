# bots/exchanges/gateio_trader.py
import gate_api
from gate_api.exceptions import ApiException
import logging
from decimal import Decimal, ROUND_DOWN
from datetime import datetime

logger = logging.getLogger(__name__)

class GateIOTrader:
    """
    Simple Gate.io spot trading implementation
    """
    
    def __init__(self, api_key, api_secret):
        """
        Initialize Gate.io trader
        
        Args:
            api_key (str): Gate.io API key
            api_secret (str): Gate.io API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        
        # Configure API client
        configuration = gate_api.Configuration(
            host="https://api.gateio.ws/api/v4",
            key=api_key,
            secret=api_secret
        )
        
        self.api_client = gate_api.ApiClient(configuration)
        self.spot_api = gate_api.SpotApi(self.api_client)
    
    def convert_symbol(self, tradingview_symbol):
        """
        Convert TradingView symbol to Gate.io format
        
        Args:
            tradingview_symbol (str): Symbol from TradingView (e.g., BTCUSD, BTCUSDT)
            
        Returns:
            str: Gate.io format symbol (e.g., BTC_USDT)
        """
        symbol = tradingview_symbol.upper()
        
        # Direct conversions
        conversions = {
            'BTCUSD': 'BTC_USDT',
            'ETHUSD': 'ETH_USDT',
            'ADAUSD': 'ADA_USDT',
            'SOLUSD': 'SOL_USDT',
            'BNBUSD': 'BNB_USDT',
        }
        
        if symbol in conversions:
            return conversions[symbol]
        
        # Generic conversion
        if symbol.endswith('USD') and not symbol.endswith('USDT'):
            base = symbol[:-3]
            return f"{base}_USDT"
        elif symbol.endswith('USDT'):
            base = symbol[:-4]
            return f"{base}_USDT"
        elif '_' not in symbol:
            return f"{symbol}_USDT"
        
        return symbol
    
    def get_account_balance(self, currency):
        """
        Get balance for specific currency
        
        Args:
            currency (str): Currency code (e.g., 'USDT', 'BTC')
            
        Returns:
            float: Available balance
        """
        try:
            accounts = self.spot_api.list_spot_accounts()
            
            for account in accounts:
                if account.currency.upper() == currency.upper():
                    return float(account.available)
            
            return 0.0
            
        except ApiException as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0
    
    def get_ticker_price(self, symbol):
        """
        Get current price for symbol
        
        Args:
            symbol (str): Trading pair (e.g., 'BTC_USDT')
            
        Returns:
            float: Current price
        """
        try:
            ticker = self.spot_api.get_ticker(currency_pair=symbol)
            return float(ticker.last)
            
        except ApiException as e:
            logger.error(f"Error getting ticker price: {e}")
            return 0.0
    
    def place_spot_order(self, symbol, side, amount, order_type='market'):
        """
        Place spot trading order
        
        Args:
            symbol (str): Trading pair (e.g., 'BTC_USDT')
            side (str): 'buy' or 'sell'
            amount (float): Amount to trade
            order_type (str): 'market' only for simplicity
            
        Returns:
            dict: Order result
        """
        try:
            # Create market order
            order = gate_api.Order(
                currency_pair=symbol,
                side=side.lower(),
                type='market',
                amount=str(amount)
            )
            
            # Place the order
            result = self.spot_api.create_order(order)
            
            return {
                'success': True,
                'order_id': result.id,
                'symbol': result.currency_pair,
                'side': result.side,
                'amount': float(result.amount),
                'status': result.status,
                'timestamp': result.create_time,
                'exchange': 'gateio'
            }
            
        except ApiException as e:
            logger.error(f"Error placing order: {e}")
            return {
                'success': False,
                'error': str(e),
                'exchange': 'gateio'
            }
    
    def execute_signal(self, payload):
        """
        Execute trading signal from TradingView
        
        Args:
            payload (dict): TradingView webhook payload
            
        Returns:
            dict: Trade execution result
        """
        try:
            # Extract signal data
            side = payload.get('side', '').lower()
            symbol = self.convert_symbol(payload.get('symbol', ''))
            amount = float(payload.get('amount', 0))
            
            logger.info(f"Executing Gate.io signal: {side.upper()} {amount} {symbol}")
            
            # Validate inputs
            if not side or side not in ['buy', 'sell']:
                raise ValueError("Invalid side. Must be 'buy' or 'sell'")
            
            if amount <= 0:
                raise ValueError("Amount must be greater than 0")
            
            # Get current price for calculation
            current_price = self.get_ticker_price(symbol)
            if current_price <= 0:
                raise ValueError(f"Could not get price for {symbol}")
            
            # Calculate trade amount
            if side == 'buy':
                # For buy orders, amount is in quote currency (USDT)
                quote_balance = self.get_account_balance('USDT')
                if quote_balance < amount:
                    raise ValueError(f"Insufficient USDT balance. Have: {quote_balance}, Need: {amount}")
                
                # Calculate base amount to buy
                base_amount = amount / current_price
                trade_amount = str(round(base_amount, 6))
            else:
                # For sell orders, amount is in base currency
                base_currency = symbol.split('_')[0]
                base_balance = self.get_account_balance(base_currency)
                if base_balance < amount:
                    raise ValueError(f"Insufficient {base_currency} balance. Have: {base_balance}, Need: {amount}")
                
                trade_amount = str(amount)
            
            # Execute the trade
            order_result = self.place_spot_order(symbol, side, trade_amount)
            
            if order_result['success']:
                return {
                    'success': True,
                    'exchange': 'gateio',
                    'order_id': order_result['order_id'],
                    'symbol': symbol,
                    'side': side,
                    'amount': trade_amount,
                    'price': current_price,
                    'total_value': amount if side == 'buy' else float(trade_amount) * current_price,
                    'status': order_result['status'],
                    'timestamp': datetime.now().isoformat(),
                    'message': f"Gate.io {side} order executed successfully"
                }
            else:
                return {
                    'success': False,
                    'exchange': 'gateio',
                    'error': order_result['error'],
                    'message': f"Gate.io {side} order failed"
                }
                
        except Exception as e:
            logger.error(f"Gate.io signal execution error: {e}")
            return {
                'success': False,
                'exchange': 'gateio',
                'error': str(e),
                'message': "Gate.io signal execution failed"
            }