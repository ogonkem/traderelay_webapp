# trading.py
import json
import logging
from django.utils import timezone
from celery import shared_task
from .models import Bot, BotLog, ExchangeLog
from .ccxt.factory import ExchangeFactory
from decimal import Decimal

logger = logging.getLogger(__name__)

def process_trading_signal(payload, webhook):
    """
    Process trading signal and find all bots related to the webhook.
    Queues trade execution tasks for scalability.
    """
    try:
        # Basic validation
        required_fields = ['type', 'side', 'amount', 'symbol']
        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Missing required field: {field}")
        
        # Find all active bots that use this webhook
        bots = Bot.objects.filter(
            webhook=webhook,
            is_active=True
        ).select_related('exchange', 'user')
        
        if not bots:
            logger.warning(f"No active bots found for webhook: {webhook.name}")
            return
        
        logger.info(f"Found {bots.count()} active bots for webhook: {webhook.name}")
        
        # Queue trade execution for each bot
        for bot in bots:
            # Validate symbol matches bot's configured symbol
            if bot.symbol.lower() != payload.get('symbol', '').lower():
                logger.info(f"Skipping bot {bot.name} - symbol mismatch: {bot.symbol} vs {payload.get('symbol')}")
                continue
            
            # Queue the trade execution task
            execute_trade_task.delay(
                bot_id=bot.id,
                payload=payload,
                webhook_id=webhook.id
            )
            
            logger.info(f"Queued trade execution for bot: {bot.name} on {bot.exchange.name}")
        
        # Log the signal processing
        logger.info(f"Processed signal for {webhook.user.username}:")
        logger.info(f"  Type: {payload.get('type')}")
        logger.info(f"  Side: {payload.get('side')}")
        logger.info(f"  Amount: {payload.get('amount')}")
        logger.info(f"  Symbol: {payload.get('symbol')}")
        logger.info(f"  Take Profit: {payload.get('takeProfit', 'N/A')}")
        logger.info(f"  Stop Loss: {payload.get('stopLoss', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Error processing trading signal: {e}")
        raise

@shared_task(bind=True, max_retries=3)
def execute_trade_task(self, bot_id, payload, webhook_id):
    """
    Celery task to execute a trade on a specific exchange.
    Includes retry logic and comprehensive logging.
    """
    try:
        # Get bot and related data
        bot = Bot.objects.select_related('exchange', 'user').get(id=bot_id)
        
        # Execute the trade
        result = execute_trade_on_exchange(bot, payload)
        
        # Log successful execution
        BotLog.objects.create(
            bot=bot,
            payload={
                'signal': payload,
                'execution_result': result,
                'webhook_id': webhook_id
            },
            success=True
        )
        
        logger.info(f"Successfully executed trade for bot: {bot.name}")
        return result
        
    except Exception as exc:
        logger.error(f"Error executing trade for bot {bot_id}: {exc}")
        
        # Log failed execution
        try:
            bot = Bot.objects.get(id=bot_id)
            BotLog.objects.create(
                bot=bot,
                payload={
                    'signal': payload,
                    'error': str(exc),
                    'webhook_id': webhook_id
                },
                success=False,
                error_message=str(exc)
            )
        except Exception as log_error:
            logger.error(f"Error logging failed trade: {log_error}")
        
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

def execute_trade_on_exchange(bot, payload):
    """
    Execute a trade on the specified exchange using the bot's configuration.
    """
    try:
        exchange = bot.exchange
        credentials = exchange.credentials
        
        # Initialize exchange connection using factory
        exchange_instance = ExchangeFactory.create_exchange(exchange.exchange_type, credentials)
        
        # Connect to exchange
        exchange_instance.connect()
        
        # Prepare order parameters
        order_params = prepare_order_params(bot, payload)
        
        # Execute the order
        result = place_order(exchange_instance, order_params)
        
        # Log exchange interaction
        ExchangeLog.objects.create(
            exchange=exchange,
            payload={
                'order_params': order_params,
                'result': result,
                'bot_name': bot.name
            },
            success=True
        )
        
        return result
        
    except Exception as e:
        # Log exchange error
        try:
            ExchangeLog.objects.create(
                exchange=exchange,
                payload={
                    'order_params': order_params if 'order_params' in locals() else {},
                    'error': str(e),
                    'bot_name': bot.name
                },
                success=False,
                error_message=str(e)
            )
        except Exception as log_error:
            logger.error(f"Error logging exchange error: {log_error}")
        
        raise

def prepare_order_params(bot, payload):
    """
    Prepare order parameters based on bot configuration and signal payload.
    """
    try:
        # Basic order parameters
        order_params = {
            'symbol': payload['symbol'],
            'type': payload['type'],  # 'market' or 'limit'
            'side': payload['side'],  # 'buy' or 'sell'
            'amount': float(bot.position_size),  # Use bot's configured position size
        }
        
        # Add price for limit orders
        if payload['type'] == 'limit' and 'price' in payload:
            order_params['price'] = float(payload['price'])
        
        # Add take profit and stop loss if provided
        if 'takeProfit' in payload:
            order_params['takeProfit'] = float(payload['takeProfit'])
        
        if 'stopLoss' in payload:
            order_params['stopLoss'] = float(payload['stopLoss'])
        
        # Add additional parameters
        if 'timeInForce' in payload:
            order_params['timeInForce'] = payload['timeInForce']
        
        if 'reduceOnly' in payload:
            order_params['reduceOnly'] = payload['reduceOnly']
        
        return order_params
        
    except Exception as e:
        logger.error(f"Error preparing order parameters: {e}")
        raise

def place_order(exchange_instance, order_params):
    """
    Place an order on the exchange using the custom exchange classes.
    """
    try:
        # Place the main order
        order = exchange_instance.place_order(
            symbol=order_params['symbol'],
            side=order_params['side'],
            amount=order_params['amount'],
            order_type=order_params['type'],
            price=order_params.get('price')
        )
        
        result = {
            'main_order': order,
            'take_profit_order': None,
            'stop_loss_order': None,
        }
        
        # Place take profit order if specified
        if 'takeProfit' in order_params:
            try:
                tp_order = exchange_instance.place_order(
                    symbol=order_params['symbol'],
                    side='sell' if order_params['side'] == 'buy' else 'buy',
                    amount=order_params['amount'],
                    order_type='limit',
                    price=order_params['takeProfit']
                )
                result['take_profit_order'] = tp_order
            except Exception as tp_error:
                logger.warning(f"Failed to place take profit order: {tp_error}")
        
        # Place stop loss order if specified
        if 'stopLoss' in order_params:
            try:
                sl_order = exchange_instance.place_order(
                    symbol=order_params['symbol'],
                    side='sell' if order_params['side'] == 'buy' else 'buy',
                    amount=order_params['amount'],
                    order_type='stop',
                    price=order_params['stopLoss']
                )
                result['stop_loss_order'] = sl_order
            except Exception as sl_error:
                logger.warning(f"Failed to place stop loss order: {sl_error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise 