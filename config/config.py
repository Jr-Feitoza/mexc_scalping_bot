import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Configurações principais do bot de trading"""
    
    # Configurações da API MEXC
    MEXC_API_KEY = os.getenv('MEXC_API_KEY', '')
    MEXC_SECRET_KEY = os.getenv('MEXC_SECRET_KEY', '')
    MEXC_BASE_URL = 'https://contract.mexc.com'
    
    # Configurações do Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Configurações de Trading
    LEVERAGE = 7
    POSITION_SIZE_PERCENT = 1.0  # 1% da margem
    MIN_POSITION_SIZE_USDT = 1.0
    
    # Configurações de Análise Técnica
    RSI_PERIOD_SHORT = 7
    RSI_PERIOD_LONG = 14
    EMA_FAST = 20
    EMA_SLOW = 50
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    # Configurações de Fibonacci
    FIBONACCI_LEVELS = {
        'TP1': 0.382,
        'TP2': 0.618,
        'TP3': 1.0
    }
    
    # Configurações de Stop Loss
    ATR_MULTIPLIER = 2.0
    
    # Configurações de Volume
    VOLUME_SPIKE_MULTIPLIER = 2.0
    VOLUME_ANALYSIS_DAYS = 7
    
    # Horários prioritários (UTC)
    PRIORITY_HOURS = [0, 6, 13]
    
    # Configurações de Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/trading_bot.log'
    
    # Configurações de Dados
    DATA_FOLDER = 'data'
    CANDLE_INTERVALS = ['1m', '5m']
    
    # Configurações de Rate Limiting
    API_RATE_LIMIT = 20  # requests per 2 seconds
    
    # Configurações de Backtesting (futuro)
    BACKTEST_START_DATE = '2024-01-01'
    BACKTEST_END_DATE = '2024-12-31'

class TradingPairs:
    """Configurações dos pares de trading"""
    
    # Par de referência para análise de tendência
    REFERENCE_PAIR = 'BTC_USDT'
    
    # Lista de pares USDT para análise
    USDT_PAIRS = [
        'BTC_USDT', 'ETH_USDT', 'BNB_USDT', 'ADA_USDT', 'SOL_USDT',
        'XRP_USDT', 'DOT_USDT', 'DOGE_USDT', 'AVAX_USDT', 'MATIC_USDT',
        'LINK_USDT', 'UNI_USDT', 'LTC_USDT', 'BCH_USDT', 'ATOM_USDT'
    ]
    
    # Pares excluídos da análise
    EXCLUDED_PAIRS = []

class AlertMessages:
    """Templates de mensagens para alertas"""
    
    SIGNAL_TEMPLATE = """
🚨 SINAL DE ENTRADA DETECTADO 🚨

💰 Par: {symbol}
📈 Direção: {direction}
💵 Preço Atual: {current_price}
📊 RSI: {rsi}
📈 Tendência BTC: {btc_trend}
📊 Volume Spike: {volume_spike}

🎯 Alvos Fibonacci:
• TP1 (38.2%): {tp1}
• TP2 (61.8%): {tp2}
• TP3 (100%): {tp3}

🛡️ Stop Loss Sugerido: {stop_loss}

⚡ Alavancagem: {leverage}x
💰 Tamanho da Posição: {position_size} USDT

📊 Motivo do Sinal:
{signal_reason}

⏰ Horário: {timestamp}
    """
    
    ERROR_TEMPLATE = """
❌ ERRO NO BOT DE TRADING

🔍 Erro: {error_message}
📍 Localização: {location}
⏰ Horário: {timestamp}
    """
    
    STATUS_TEMPLATE = """
📊 STATUS DO BOT

✅ Status: {status}
🔄 Última Análise: {last_analysis}
📈 Sinais Enviados Hoje: {signals_today}
💰 Pares Monitorados: {monitored_pairs}
⏰ Próxima Análise: {next_analysis}
    """

