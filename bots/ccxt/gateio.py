# gateio.py
import gate_api
from gate_api.api import SpotApi, FuturesApi, WalletApi
from gate_api.exceptions import ApiException, GateApiException
import time
import logging

logger = logging.getLogger(__name__)

class GateioExchange:
    """
    Gate.io Exchange Integration
    """
    def __init__(self, credentials):
        self.credentials = credentials
        self.name = "Gate.io"
        self.client = None
        self.spot_api = None
        self.futures_api = None
        self.wallet_api = None
        self.is_connected = False
        
    def connect(self):
        """Initialize connection to Gate.io"""
        try:
            # Create configuration
            configuration = gate_api.Configuration(
                host="https://api.gateio.ws/api/v4",
                key=self.credentials.get('api_key'),
                secret=self.credentials.get('api_secret')
            )
            
            # Initialize API client
            api_client = gate_api.ApiClient(configuration)
            
            # Initialize specific APIs
            self.spot_api = SpotApi(api_client)
            self.futures_api = FuturesApi(api_client)
            self.wallet_api = WalletApi(api_client)
            
            # Test connection by getting account info
            balance = self.wallet_api.list_spot_accounts()
            self.is_connected = True
            
            logger.info(f"Successfully connected to {self.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {str(e)}")
            self.is_connected = False
            return False
    
    def place_order(self, symbol, side, amount, order_type="market", price=None, 
                   take_profit=None, stop_loss=None, time_in_force=None, reduce_only=None):
        """Place an order on Gate.io"""
        if not self.is_connected:
            raise Exception("Not connected to Gate.io. Call connect() first.")
        
        try:
            # Normalize symbol format (e.g., BTC/USDT -> BTC_USDT)
            normalized_symbol = symbol.replace('/', '_')
            
            # Prepare order parameters
            order_params = {
                'currency_pair': normalized_symbol,
                'side': side.lower(),  # 'buy' or 'sell'
                'type': order_type.lower(),  # 'market', 'limit', etc.
                'amount': str(amount)
            }
            
            # Add price for limit orders
            if order_type.lower() == 'limit' and price:
                order_params['price'] = str(price)
            
            # Add time in force if specified
            if time_in_force:
                order_params['time_in_force'] = time_in_force.upper()
            
            # Handle stop loss and take profit (using separate API calls if needed)
            if stop_loss or take_profit:
                logger.warning("Stop loss and take profit orders may require separate API calls")
            
            # Place the order
            if order_type.lower() in ['market', 'limit']:
                order = gate_api.Order(**order_params)
                result = self.spot_api.create_order(order)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            logger.info(f"Order placed successfully: {result.id}")
            return {
                'id': result.id,
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'type': order_type,
                'status': result.status,
                'price': getattr(result, 'price', None),
                'filled_amount': getattr(result, 'filled_total', '0')
            }
            
        except ApiException as e:
            logger.error(f"API error placing order: {e}")
            raise Exception(f"Failed to place order: {e}")
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            raise Exception(f"Failed to place order: {str(e)}")
    
    def get_balance(self):
        """Get account balance"""
        if not self.is_connected:
            raise Exception("Not connected to Gate.io. Call connect() first.")
        
        try:
            # Get spot account balances
            spot_accounts = self.wallet_api.list_spot_accounts()
            
            balances = {}
            for account in spot_accounts:
                if float(account.available) > 0 or float(account.locked) > 0:
                    balances[account.currency] = {
                        'available': float(account.available),
                        'locked': float(account.locked),
                        'total': float(account.available) + float(account.locked)
                    }
            
            return balances
            
        except ApiException as e:
            logger.error(f"API error getting balance: {e}")
            raise Exception(f"Failed to get balance: {e}")
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            raise Exception(f"Failed to get balance: {str(e)}")
    
    def get_ticker(self, symbol):
        """Get current ticker for symbol"""
        if not self.is_connected:
            raise Exception("Not connected to Gate.io. Call connect() first.")
        
        try:
            # Normalize symbol format
            normalized_symbol = symbol.replace('/', '_')
            
            # Get ticker information
            ticker = self.spot_api.list_tickers(currency_pair=normalized_symbol)
            
            if ticker:
                ticker_data = ticker[0]
                return {
                    'symbol': symbol,
                    'last_price': float(ticker_data.last),
                    'bid': float(ticker_data.highest_bid),
                    'ask': float(ticker_data.lowest_ask),
                    'volume': float(ticker_data.base_volume),
                    'high_24h': float(ticker_data.high_24h),
                    'low_24h': float(ticker_data.low_24h),
                    'change_24h': float(ticker_data.change_percentage)
                }
            else:
                raise Exception(f"No ticker data found for {symbol}")
            
        except ApiException as e:
            logger.error(f"API error getting ticker: {e}")
            raise Exception(f"Failed to get ticker: {e}")
        except Exception as e:
            logger.error(f"Error getting ticker: {str(e)}")
            raise Exception(f"Failed to get ticker: {str(e)}")

    def get_order_status(self, order_id, symbol):
        """Get order status"""
        if not self.is_connected:
            raise Exception("Not connected to Gate.io. Call connect() first.")
        
        try:
            normalized_symbol = symbol.replace('/', '_')
            order = self.spot_api.get_order(order_id, normalized_symbol)
            
            return {
                'id': order.id,
                'symbol': symbol,
                'side': order.side,
                'amount': float(order.amount),
                'price': float(order.price) if order.price else None,
                'filled_amount': float(order.filled_total),
                'status': order.status,
                'created_at': order.create_time
            }
            
        except ApiException as e:
            logger.error(f"API error getting order status: {e}")
            raise Exception(f"Failed to get order status: {e}")
        except Exception as e:
            logger.error(f"Error getting order status: {str(e)}")
            raise Exception(f"Failed to get order status: {str(e)}")

    def cancel_order(self, order_id, symbol):
        """Cancel an order"""
        if not self.is_connected:
            raise Exception("Not connected to Gate.io. Call connect() first.")
        
        try:
            normalized_symbol = symbol.replace('/', '_')
            result = self.spot_api.cancel_order(order_id, normalized_symbol)
            
            logger.info(f"Order {order_id} cancelled successfully")
            return True
            
        except ApiException as e:
            logger.error(f"API error cancelling order: {e}")
            raise Exception(f"Failed to cancel order: {e}")
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            raise Exception(f"Failed to cancel order: {str(e)}")


def get_gateio_symbols():
    """
    Retrieve all available trading symbols from Gate.io exchange
    
    Returns:
        list: List of available trading symbols in format ['BTC/USDT', 'ETH/USDT', ...]
    """
    try:
        # Create a temporary connection to get symbols
        configuration = gate_api.Configuration(host="https://api.gateio.ws/api/v4")
        api_client = gate_api.ApiClient(configuration)
        spot_api = SpotApi(api_client)
        
        # Get all currency pairs (this is a public endpoint, no auth needed)
        currency_pairs = spot_api.list_currency_pairs()
        
        symbols = []
        for pair in currency_pairs:
            # Convert from Gate.io format (BTC_USDT) to standard format (BTC/USDT)
            if pair.trade_status == 'tradable':  # Only include tradable pairs
                symbol = pair.id.replace('_', '/')
                symbols.append(symbol)
        
        logger.info(f"Retrieved {len(symbols)} symbols from Gate.io")
        return sorted(symbols)
        
    except ApiException as e:
        logger.error(f"API error getting symbols: {e}")
        raise Exception(f"Failed to get symbols: {e}")
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        raise Exception(f"Failed to get symbols: {str(e)}")


def get_gateio_symbol_info(symbol=None):
    """
    Get detailed information about trading symbols
    
    Args:
        symbol (str, optional): Specific symbol to get info for. If None, returns all symbols.
    
    Returns:
        dict or list: Symbol information including trading rules, precision, etc.
    """
    try:
        configuration = gate_api.Configuration(host="https://api.gateio.ws/api/v4")
        api_client = gate_api.ApiClient(configuration)
        spot_api = SpotApi(api_client)
        
        if symbol:
            # Get info for specific symbol
            normalized_symbol = symbol.replace('/', '_')
            currency_pairs = spot_api.list_currency_pairs()
            
            for pair in currency_pairs:
                if pair.id == normalized_symbol:
                    return {
                        'symbol': symbol,
                        'base_currency': pair.base,
                        'quote_currency': pair.quote,
                        'min_base_amount': float(pair.min_base_amount),
                        'min_quote_amount': float(pair.min_quote_amount),
                        'max_base_amount': float(pair.max_base_amount) if pair.max_base_amount else None,
                        'max_quote_amount': float(pair.max_quote_amount) if pair.max_quote_amount else None,
                        'amount_precision': pair.amount_precision,
                        'price_precision': pair.precision,
                        'trade_status': pair.trade_status,
                        'fee_rate': float(pair.fee)
                    }
            
            raise Exception(f"Symbol {symbol} not found")
            
        else:
            # Get info for all symbols
            currency_pairs = spot_api.list_currency_pairs()
            symbol_info = []
            
            for pair in currency_pairs:
                if pair.trade_status == 'tradable':
                    symbol_formatted = pair.id.replace('_', '/')
                    symbol_info.append({
                        'symbol': symbol_formatted,
                        'base_currency': pair.base,
                        'quote_currency': pair.quote,
                        'min_base_amount': float(pair.min_base_amount),
                        'min_quote_amount': float(pair.min_quote_amount),
                        'max_base_amount': float(pair.max_base_amount) if pair.max_base_amount else None,
                        'max_quote_amount': float(pair.max_quote_amount) if pair.max_quote_amount else None,
                        'amount_precision': pair.amount_precision,
                        'price_precision': pair.precision,
                        'trade_status': pair.trade_status,
                        'fee_rate': float(pair.fee)
                    })
            
            return symbol_info
            
    except ApiException as e:
        logger.error(f"API error getting symbol info: {e}")
        raise Exception(f"Failed to get symbol info: {e}")
    except Exception as e:
        logger.error(f"Error getting symbol info: {str(e)}")
        raise Exception(f"Failed to get symbol info: {str(e)}")