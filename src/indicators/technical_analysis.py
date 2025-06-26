import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import ta
from src.utils.logger import logger

class TechnicalAnalysis:
    """Classe para análise técnica de dados de mercado"""
    
    def __init__(self):
        self.indicators = {}
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calcula o RSI (Relative Strength Index)
        
        Args:
            df: DataFrame com dados OHLCV
            period: Período para cálculo do RSI
        
        Returns:
            Série com valores do RSI
        """
        try:
            return ta.momentum.RSIIndicator(df['close'], window=period).rsi()
        except Exception as e:
            logger.error(f"Erro ao calcular RSI: {str(e)}")
            return pd.Series(dtype=float)
    
    def calculate_ema(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calcula a EMA (Exponential Moving Average)
        
        Args:
            df: DataFrame com dados OHLCV
            period: Período para cálculo da EMA
        
        Returns:
            Série com valores da EMA
        """
        try:
            return ta.trend.EMAIndicator(df['close'], window=period).ema_indicator()
        except Exception as e:
            logger.error(f"Erro ao calcular EMA: {str(e)}")
            return pd.Series(dtype=float)
    
    def calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """
        Calcula o OBV (On-Balance Volume)
        
        Args:
            df: DataFrame com dados OHLCV
        
        Returns:
            Série com valores do OBV
        """
        try:
            return ta.volume.OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
        except Exception as e:
            logger.error(f"Erro ao calcular OBV: {str(e)}")
            return pd.Series(dtype=float)
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calcula o ATR (Average True Range)
        
        Args:
            df: DataFrame com dados OHLCV
            period: Período para cálculo do ATR
        
        Returns:
            Série com valores do ATR
        """
        try:
            return ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=period).average_true_range()
        except Exception as e:
            logger.error(f"Erro ao calcular ATR: {str(e)}")
            return pd.Series(dtype=float)
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: float = 2) -> Dict[str, pd.Series]:
        """
        Calcula as Bandas de Bollinger
        
        Args:
            df: DataFrame com dados OHLCV
            period: Período para cálculo
            std: Desvio padrão
        
        Returns:
            Dicionário com upper, middle e lower bands
        """
        try:
            bb = ta.volatility.BollingerBands(df['close'], window=period, window_dev=std)
            return {
                'upper': bb.bollinger_hband(),
                'middle': bb.bollinger_mavg(),
                'lower': bb.bollinger_lband()
            }
        except Exception as e:
            logger.error(f"Erro ao calcular Bandas de Bollinger: {str(e)}")
            return {'upper': pd.Series(dtype=float), 'middle': pd.Series(dtype=float), 'lower': pd.Series(dtype=float)}
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        Calcula o MACD
        
        Args:
            df: DataFrame com dados OHLCV
            fast: Período da EMA rápida
            slow: Período da EMA lenta
            signal: Período da linha de sinal
        
        Returns:
            Dicionário com MACD, signal e histogram
        """
        try:
            macd = ta.trend.MACD(df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
            return {
                'macd': macd.macd(),
                'signal': macd.macd_signal(),
                'histogram': macd.macd_diff()
            }
        except Exception as e:
            logger.error(f"Erro ao calcular MACD: {str(e)}")
            return {'macd': pd.Series(dtype=float), 'signal': pd.Series(dtype=float), 'histogram': pd.Series(dtype=float)}
    
    def detect_volume_spike(self, df: pd.DataFrame, multiplier: float = 2.0, lookback: int = 20) -> bool:
        """
        Detecta spike de volume
        
        Args:
            df: DataFrame com dados OHLCV
            multiplier: Multiplicador para detectar spike
            lookback: Período para calcular volume médio
        
        Returns:
            True se houver spike de volume
        """
        try:
            if len(df) < lookback + 1:
                return False
            
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].iloc[-lookback-1:-1].mean()
            
            return current_volume > (avg_volume * multiplier)
        except Exception as e:
            logger.error(f"Erro ao detectar spike de volume: {str(e)}")
            return False
    
    def identify_candlestick_patterns(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        Identifica padrões de candlestick
        
        Args:
            df: DataFrame com dados OHLCV
        
        Returns:
            Dicionário com padrões identificados
        """
        try:
            if len(df) < 3:
                return {}
            
            patterns = {}
            
            # Doji
            patterns['doji'] = self._is_doji(df.iloc[-1])
            
            # Hammer
            patterns['hammer'] = self._is_hammer(df.iloc[-1])
            
            # Inverted Hammer
            patterns['inverted_hammer'] = self._is_inverted_hammer(df.iloc[-1])
            
            # Engulfing (precisa de 2 candles)
            if len(df) >= 2:
                patterns['bullish_engulfing'] = self._is_bullish_engulfing(df.iloc[-2], df.iloc[-1])
                patterns['bearish_engulfing'] = self._is_bearish_engulfing(df.iloc[-2], df.iloc[-1])
            
            # Pinbar
            patterns['bullish_pinbar'] = self._is_bullish_pinbar(df.iloc[-1])
            patterns['bearish_pinbar'] = self._is_bearish_pinbar(df.iloc[-1])
            
            return patterns
            
        except Exception as e:
            logger.error(f"Erro ao identificar padrões de candlestick: {str(e)}")
            return {}
    
    def _is_doji(self, candle: pd.Series) -> bool:
        """Identifica padrão Doji"""
        body_size = abs(candle['close'] - candle['open'])
        candle_range = candle['high'] - candle['low']
        return body_size <= (candle_range * 0.1)
    
    def _is_hammer(self, candle: pd.Series) -> bool:
        """Identifica padrão Hammer"""
        body_size = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (lower_shadow >= body_size * 2 and 
                upper_shadow <= body_size * 0.5 and
                body_size > 0)
    
    def _is_inverted_hammer(self, candle: pd.Series) -> bool:
        """Identifica padrão Inverted Hammer"""
        body_size = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        return (upper_shadow >= body_size * 2 and 
                lower_shadow <= body_size * 0.5 and
                body_size > 0)
    
    def _is_bullish_engulfing(self, prev_candle: pd.Series, current_candle: pd.Series) -> bool:
        """Identifica padrão Bullish Engulfing"""
        prev_bearish = prev_candle['close'] < prev_candle['open']
        current_bullish = current_candle['close'] > current_candle['open']
        
        engulfs = (current_candle['open'] < prev_candle['close'] and 
                  current_candle['close'] > prev_candle['open'])
        
        return prev_bearish and current_bullish and engulfs
    
    def _is_bearish_engulfing(self, prev_candle: pd.Series, current_candle: pd.Series) -> bool:
        """Identifica padrão Bearish Engulfing"""
        prev_bullish = prev_candle['close'] > prev_candle['open']
        current_bearish = current_candle['close'] < current_candle['open']
        
        engulfs = (current_candle['open'] > prev_candle['close'] and 
                  current_candle['close'] < prev_candle['open'])
        
        return prev_bullish and current_bearish and engulfs
    
    def _is_bullish_pinbar(self, candle: pd.Series) -> bool:
        """Identifica padrão Bullish Pinbar"""
        body_size = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        total_range = candle['high'] - candle['low']
        
        return (lower_shadow >= total_range * 0.6 and
                body_size <= total_range * 0.3 and
                upper_shadow <= total_range * 0.2)
    
    def _is_bearish_pinbar(self, candle: pd.Series) -> bool:
        """Identifica padrão Bearish Pinbar"""
        body_size = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        total_range = candle['high'] - candle['low']
        
        return (upper_shadow >= total_range * 0.6 and
                body_size <= total_range * 0.3 and
                lower_shadow <= total_range * 0.2)
    
    def analyze_trend(self, df: pd.DataFrame, fast_ema: int = 20, slow_ema: int = 50) -> str:
        """
        Analisa a tendência baseada nas EMAs
        
        Args:
            df: DataFrame com dados OHLCV
            fast_ema: Período da EMA rápida
            slow_ema: Período da EMA lenta
        
        Returns:
            'bullish', 'bearish' ou 'neutral'
        """
        try:
            if len(df) < max(fast_ema, slow_ema):
                return 'neutral'
            
            ema_fast = self.calculate_ema(df, fast_ema)
            ema_slow = self.calculate_ema(df, slow_ema)
            
            if ema_fast.iloc[-1] > ema_slow.iloc[-1]:
                return 'bullish'
            elif ema_fast.iloc[-1] < ema_slow.iloc[-1]:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Erro ao analisar tendência: {str(e)}")
            return 'neutral'
    
    def calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """
        Calcula níveis de suporte e resistência
        
        Args:
            df: DataFrame com dados OHLCV
            window: Janela para cálculo
        
        Returns:
            Dicionário com níveis de suporte e resistência
        """
        try:
            if len(df) < window:
                return {'support': None, 'resistance': None}
            
            # Calcula máximas e mínimas locais
            highs = df['high'].rolling(window=window, center=True).max()
            lows = df['low'].rolling(window=window, center=True).min()
            
            # Encontra níveis mais recentes
            recent_high = highs.dropna().iloc[-1] if not highs.dropna().empty else df['high'].max()
            recent_low = lows.dropna().iloc[-1] if not lows.dropna().empty else df['low'].min()
            
            return {
                'resistance': recent_high,
                'support': recent_low
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular suporte e resistência: {str(e)}")
            return {'support': None, 'resistance': None}
    
    def get_comprehensive_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Realiza análise técnica completa
        
        Args:
            df: DataFrame com dados OHLCV
        
        Returns:
            Dicionário com análise completa
        """
        try:
            analysis = {}
            
            # Indicadores básicos
            analysis['rsi_7'] = self.calculate_rsi(df, 7).iloc[-1] if len(df) >= 7 else None
            analysis['rsi_14'] = self.calculate_rsi(df, 14).iloc[-1] if len(df) >= 14 else None
            analysis['ema_20'] = self.calculate_ema(df, 20).iloc[-1] if len(df) >= 20 else None
            analysis['ema_50'] = self.calculate_ema(df, 50).iloc[-1] if len(df) >= 50 else None
            
            # OBV
            obv = self.calculate_obv(df)
            analysis['obv'] = obv.iloc[-1] if not obv.empty else None
            analysis['obv_trend'] = 'rising' if len(obv) >= 2 and obv.iloc[-1] > obv.iloc[-2] else 'falling'
            
            # ATR
            atr = self.calculate_atr(df)
            analysis['atr'] = atr.iloc[-1] if not atr.empty else None
            
            # Tendência
            analysis['trend'] = self.analyze_trend(df)
            
            # Volume spike
            analysis['volume_spike'] = self.detect_volume_spike(df)
            
            # Padrões de candlestick
            analysis['candlestick_patterns'] = self.identify_candlestick_patterns(df)
            
            # Suporte e resistência
            sr_levels = self.calculate_support_resistance(df)
            analysis['support'] = sr_levels['support']
            analysis['resistance'] = sr_levels['resistance']
            
            # Preço atual
            analysis['current_price'] = df['close'].iloc[-1]
            analysis['current_volume'] = df['volume'].iloc[-1]
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro na análise técnica completa: {str(e)}")
            return {}

