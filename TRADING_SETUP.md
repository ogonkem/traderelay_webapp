# Trading System Setup Guide

This guide explains how to set up and use the scalable trading system with queue-based trade execution using RabbitMQ.

## Overview

The trading system has been enhanced with the following features:

1. **Queue-based Trade Execution**: Uses Celery with RabbitMQ for scalable, asynchronous trade processing
2. **Multi-Bot Support**: Automatically finds and executes trades for all bots using a webhook
3. **Exchange Integration**: Supports multiple exchanges via CCXT library
4. **Comprehensive Logging**: Detailed logging of all trading activities
5. **Error Handling**: Robust error handling with retry mechanisms

## Architecture

```
Webhook → process_trading_signal() → Find Bots → Queue Tasks → Execute Trades
```

1. **Webhook Handler**: Receives trading signals from TradingView
2. **Signal Processor**: Validates signals and finds related bots
3. **Task Queue**: Queues trade execution tasks for scalability using RabbitMQ
4. **Trade Executor**: Executes trades on exchanges with retry logic

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install and Start RabbitMQ

RabbitMQ is required as the message broker for Celery.

**Ubuntu/Debian:**
```bash
# Install RabbitMQ
sudo apt-get update
sudo apt-get install rabbitmq-server

# Start RabbitMQ service
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# Enable management plugin (optional, for web UI)
sudo rabbitmq-plugins enable rabbitmq_management
```

**macOS:**
```bash
# Install using Homebrew
brew install rabbitmq

# Start RabbitMQ service
brew services start rabbitmq

# Enable management plugin (optional)
rabbitmq-plugins enable rabbitmq_management
```

**Windows:**
1. Download RabbitMQ from https://www.rabbitmq.com/download.html
2. Install and start the service
3. Enable management plugin: `rabbitmq-plugins enable rabbitmq_management`

### 3. Configure RabbitMQ (Optional)

```bash
# Create a dedicated user (optional)
sudo rabbitmqctl add_user trading_user trading_password
sudo rabbitmqctl set_user_tags trading_user administrator
sudo rabbitmqctl set_permissions -p / trading_user ".*" ".*" ".*"

# Update settings.py with custom credentials:
# CELERY_BROKER_URL = 'amqp://trading_user:trading_password@localhost:5672//'
```

### 4. Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Start the Trading Worker

```bash
# Option 1: Using Django management command
python manage.py run_trading_worker

# Option 2: Using Celery directly
celery -A traderelay_webapp worker --loglevel=info --queues=trading
```

### 6. Start Celery Beat (Optional, for scheduled tasks)

```bash
celery -A traderelay_webapp beat --loglevel=info
```

## Configuration

### Exchange Setup

1. Create an exchange account in the admin panel
2. Configure API credentials (API key, secret, etc.)
3. Test the connection

### Bot Configuration

1. Create a webhook endpoint
2. Create a bot with:
   - Name and description
   - Associated webhook
   - Associated exchange
   - Trading symbol (e.g., "BTC/USDT")
   - Position size

### Trading Signal Format

The system expects TradingView webhook signals in this format:

```json
{
  "type": "market",
  "side": "buy",
  "amount": 100,
  "symbol": "BTC/USDT",
  "takeProfit": 50000,
  "stopLoss": 45000,
  "timeInForce": "GTC",
  "reduceOnly": false
}
```

## Usage

### 1. Create a Webhook

1. Go to the webhooks section
2. Create a new webhook
3. Copy the webhook URL for TradingView

### 2. Create an Exchange

1. Go to the exchanges section
2. Add your exchange credentials
3. Test the connection

### 3. Create a Bot

1. Go to the bots section
2. Create a new bot with:
   - Select your webhook
   - Select your exchange
   - Set the trading symbol
   - Set the position size

### 4. Configure TradingView

In TradingView, set up an alert with:
- **Webhook URL**: Your webhook URL
- **Message**: JSON payload in the expected format

## Monitoring

### Logs

- **Bot Logs**: View individual bot execution logs
- **Exchange Logs**: View exchange interaction logs
- **Webhook Logs**: View incoming webhook logs

### RabbitMQ Management

Access RabbitMQ management interface at: http://localhost:15672
- Username: guest
- Password: guest

### Celery Monitoring

```bash
# Monitor Celery tasks
celery -A traderelay_webapp flower

# Check worker status
celery -A traderelay_webapp inspect active

# Check queue status
celery -A traderelay_webapp inspect stats
```

## Supported Exchanges

Currently supported exchanges:
- Binance
- Bybit
- Gate.io

To add more exchanges, update the `exchange_map` in `trading.py`.

## Security Considerations

1. **API Credentials**: Store securely and use environment variables
2. **Webhook Security**: Use HTTPS and validate webhook signatures
3. **Rate Limiting**: Configure appropriate rate limits per exchange
4. **Error Handling**: Monitor failed trades and implement alerts
5. **RabbitMQ Security**: Use dedicated users and secure passwords

## Troubleshooting

### Common Issues

1. **RabbitMQ Connection Error**
   - Ensure RabbitMQ is running: `sudo systemctl status rabbitmq-server`
   - Check RabbitMQ logs: `sudo tail -f /var/log/rabbitmq/rabbit@hostname.log`
   - Verify connection settings in settings.py

2. **Exchange API Errors**
   - Verify API credentials
   - Check exchange API limits
   - Ensure sufficient balance

3. **Task Queue Issues**
   - Check Celery worker is running
   - Monitor task logs
   - Verify queue configuration
   - Check RabbitMQ management interface

### Debug Mode

Enable debug logging:

```bash
python manage.py run_trading_worker --loglevel=debug
```

## Performance Tuning

### Worker Configuration

- **Concurrency**: Adjust based on server capacity
- **Rate Limiting**: Configure per-exchange rate limits
- **Task Timeouts**: Set appropriate timeouts for exchange operations

### RabbitMQ Tuning

```bash
# Set memory limit (adjust as needed)
sudo rabbitmqctl set_vm_memory_high_watermark 0.6

# Set disk free space limit
sudo rabbitmqctl set_disk_free_limit 2GB
```

### Scaling

- **Multiple Workers**: Run multiple Celery workers
- **Load Balancing**: Use RabbitMQ cluster for high availability
- **Monitoring**: Implement comprehensive monitoring and alerting

## API Reference

### process_trading_signal(payload, webhook)

Main function that processes incoming trading signals.

**Parameters:**
- `payload`: Trading signal JSON
- `webhook`: WebhookEndpoint instance

### execute_trade_task(bot_id, payload, webhook_id)

Celery task that executes trades on exchanges.

**Parameters:**
- `bot_id`: Bot ID to execute trade for
- `payload`: Trading signal payload
- `webhook_id`: Webhook ID for logging

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify configuration settings
3. Test with small amounts first
4. Monitor exchange API status
5. Check RabbitMQ management interface 