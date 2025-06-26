import time
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np

def generate_signature(secret_key: str, access_key: str, timestamp: str, params: str = "") -> str:
    """
    Gera assinatura HMAC SHA256 para autenticação na API MEXC
    
    Args:
        secret_key: Chave secreta da API
        access_key: Chave de acesso da API
        timestamp: Timestamp em milissegundos
        params: Parâmetros da requisição
    
    Returns:
        Assinatura HMAC SHA256
    """
    # String para assinatura: accessKey + timestamp + params
    signature_string = access_key + timestamp + params
    
    # Gera a assinatura HMAC SHA256
    signature = hmac.new(
        secret_key.encode('utf-8'),
        signature_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def get_current_timestamp() -> str:
    """
    Retorna o timestamp atual em milissegundos
    
    Returns:
        Timestamp em milissegundos como string
    """
    return str(int(time.time() * 1000))

def format_datetime(timestamp: Union[int, float, str]) -> str:
    """
    Formata timestamp para string legível
    
    Args:
        timestamp: Timestamp em segundos ou milissegundos
    
    Returns:
        Data formatada como string
    """
    if isinstance(timestamp, str):
        timestamp = float(timestamp)
    
    # Se o timestamp está em milissegundos, converte para segundos
    if timestamp > 1e10:
        timestamp = timestamp / 1000
    
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')

def calculate_position_size(balance: float, percentage: float, min_size: float = 1.0) -> float:
    """
    Calcula o tamanho da posição baseado na porcentagem da margem
    
    Args:
        balance: Saldo disponível
        percentage: Porcentagem a ser usada (ex: 1.0 para 1%)
        min_size: Tamanho mínimo da posição
    
    Returns:
        Tamanho da posição calculado
    """
    position_size = balance * (percentage / 100)
    return max(position_size, min_size)

def calculate_fibonacci_levels(high: float, low: float, direction: str = 'long') -> Dict[str, float]:
    """
    Calcula níveis de Fibonacci para take profit
    
    Args:
        high: Preço máximo do movimento
        low: Preço mínimo do movimento
        direction: Direção da operação ('long' ou 'short')
    
    Returns:
        Dicionário com os níveis de Fibonacci
    """
    diff = high - low
    
    if direction.lower() == 'long':
        # Para operações long, os níveis são calculados a partir do low
        levels = {
            'TP1': low + (diff * 0.382),
            'TP2': low + (diff * 0.618),
            'TP3': low + (diff * 1.0),
            'TP4': low + (diff * 1.618)
        }
    else:
        # Para operações short, os níveis são calculados a partir do high
        levels = {
            'TP1': high - (diff * 0.382),
            'TP2': high - (diff * 0.618),
            'TP3': high - (diff * 1.0),
            'TP4': high - (diff * 1.618)
        }
    
    return levels

def is_priority_hour(hour: int, priority_hours: List[int]) -> bool:
    """
    Verifica se a hora atual está nos horários prioritários
    
    Args:
        hour: Hora atual (0-23)
        priority_hours: Lista de horas prioritárias
    
    Returns:
        True se for horário prioritário
    """
    return hour in priority_hours

def calculate_atr_stop_loss(df: pd.DataFrame, atr_period: int = 14, multiplier: float = 2.0, direction: str = 'long') -> float:
    """
    Calcula stop loss baseado no ATR (Average True Range)
    
    Args:
        df: DataFrame com dados OHLCV
        atr_period: Período para cálculo do ATR
        multiplier: Multiplicador do ATR
        direction: Direção da operação ('long' ou 'short')
    
    Returns:
        Preço do stop loss
    """
    if len(df) < atr_period:
        return None
    
    # Calcula True Range
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift(1))
    df['low_close'] = abs(df['low'] - df['close'].shift(1))
    df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    
    # Calcula ATR
    atr = df['true_range'].rolling(window=atr_period).mean().iloc[-1]
    current_price = df['close'].iloc[-1]
    
    if direction.lower() == 'long':
        stop_loss = current_price - (atr * multiplier)
    else:
        stop_loss = current_price + (atr * multiplier)
    
    return stop_loss

def detect_volume_spike(df: pd.DataFrame, spike_multiplier: float = 2.0, lookback_period: int = 20) -> bool:
    """
    Detecta spike de volume
    
    Args:
        df: DataFrame com dados OHLCV
        spike_multiplier: Multiplicador para detectar spike
        lookback_period: Período para calcular volume médio
    
    Returns:
        True se houver spike de volume
    """
    if len(df) < lookback_period + 1:
        return False
    
    current_volume = df['volume'].iloc[-1]
    avg_volume = df['volume'].iloc[-lookback_period-1:-1].mean()
    
    return current_volume > (avg_volume * spike_multiplier)

def format_number(number: float, decimals: int = 4) -> str:
    """
    Formata número com número específico de casas decimais
    
    Args:
        number: Número a ser formatado
        decimals: Número de casas decimais
    
    Returns:
        Número formatado como string
    """
    return f"{number:.{decimals}f}"

def validate_symbol(symbol: str) -> str:
    """
    Valida e formata símbolo de trading
    
    Args:
        symbol: Símbolo do par de trading
    
    Returns:
        Símbolo formatado
    """
    return symbol.upper().replace('/', '_')

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Divisão segura que evita divisão por zero
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor padrão se denominador for zero
    
    Returns:
        Resultado da divisão ou valor padrão
    """
    if denominator == 0:
        return default
    return numerator / denominator

def round_to_precision(value: float, precision: int) -> float:
    """
    Arredonda valor para precisão específica
    
    Args:
        value: Valor a ser arredondado
        precision: Número de casas decimais
    
    Returns:
        Valor arredondado
    """
    return round(value, precision)

def get_candle_pattern_name(pattern_code: int) -> str:
    """
    Converte código de padrão de candlestick para nome
    
    Args:
        pattern_code: Código do padrão
    
    Returns:
        Nome do padrão
    """
    patterns = {
        100: "Doji",
        200: "Hammer",
        300: "Inverted Hammer",
        400: "Hanging Man",
        500: "Shooting Star",
        600: "Engulfing Bullish",
        700: "Engulfing Bearish",
        800: "Morning Star",
        900: "Evening Star"
    }
    
    return patterns.get(pattern_code, "Unknown Pattern")

