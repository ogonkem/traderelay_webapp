import logging
from .exchange_factory import ExchangeFactory

logger = logging.getLogger(__name__)

def execute_trade_on_exchange(payload, exchange_model):
    """
    Execute trade on specified exchange
    
    Args:
        payload (dict): TradingView webhook payload
        exchange_model: Exchange model instance
        
    Returns:
        dict: Trade execution result
    """
    try:
        # Create trader for the exchange
        trader = ExchangeFactory.create_trader(
            exchange_model.exchange_type,
            exchange_model.credentials
        )
        
        # Execute the signal
        result = trader.execute_signal(payload)
        
        # Add exchange info to result
        result['exchange_name'] = exchange_model.name
        result['exchange_type'] = exchange_model.exchange_type
        
        logger.info(f"Trade executed on {exchange_model.name}: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Trade execution failed on {exchange_model.name}: {e}")
        return {
            'success': False,
            'exchange': exchange_model.exchange_type,
            'exchange_name': exchange_model.name,
            'error': str(e),
            'message': f"Failed to execute trade on {exchange_model.name}"
        }
