#!/usr/bin/env python3
"""
Testes básicos para validar a funcionalidade do sistema de trading
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.indicators.technical_analysis import TechnicalAnalysis
from src.strategies.signal_generator import SignalGenerator
from src.utils.helpers import (
    calculate_fibonacci_levels, 
    calculate_atr_stop_loss,
    format_number,
    validate_symbol
)
from config.config import Config

class TestTechnicalAnalysis(unittest.TestCase):
    """Testes para análise técnica"""
    
    def setUp(self):
        self.ta = TechnicalAnalysis()
        
        # Cria dados de teste
        dates = pd.date_range('2024-01-01', periods=100, freq='1min')
        np.random.seed(42)  # Para resultados reproduzíveis
        
        # Simula dados OHLCV realistas
        base_price = 100
        prices = []
        volumes = []
        
        for i in range(100):
            # Simula movimento de preço com tendência leve
            change = np.random.normal(0, 0.5) + (i * 0.01)  # Tendência de alta leve
            base_price += change
            
            # OHLC baseado no preço base
            open_price = base_price
            high_price = base_price + abs(np.random.normal(0, 0.3))
            low_price = base_price - abs(np.random.normal(0, 0.3))
            close_price = base_price + np.random.normal(0, 0.2)
            
            prices.append([open_price, high_price, low_price, close_price])
            volumes.append(np.random.uniform(1000, 5000))
        
        prices = np.array(prices)
        
        self.test_df = pd.DataFrame({
            'timestamp': dates,
            'open': prices[:, 0],
            'high': prices[:, 1],
            'low': prices[:, 2],
            'close': prices[:, 3],
            'volume': volumes
        })
        self.test_df.set_index('timestamp', inplace=True)
    
    def test_rsi_calculation(self):
        """Testa cálculo do RSI"""
        rsi = self.ta.calculate_rsi(self.test_df, 14)
        
        self.assertFalse(rsi.empty)
        self.assertTrue(all(0 <= val <= 100 for val in rsi.dropna()))
        self.assertEqual(len(rsi), len(self.test_df))
    
    def test_ema_calculation(self):
        """Testa cálculo da EMA"""
        ema = self.ta.calculate_ema(self.test_df, 20)
        
        self.assertFalse(ema.empty)
        self.assertEqual(len(ema), len(self.test_df))
        
        # EMA deve ser próxima aos preços de fechamento
        last_close = self.test_df['close'].iloc[-1]
        last_ema = ema.iloc[-1]
        self.assertLess(abs(last_ema - last_close), last_close * 0.1)  # Diferença < 10%
    
    def test_volume_spike_detection(self):
        """Testa detecção de spike de volume"""
        # Cria um spike artificial
        test_df = self.test_df.copy()
        test_df.loc[test_df.index[-1], 'volume'] = test_df['volume'].mean() * 3
        
        spike_detected = self.ta.detect_volume_spike(test_df, multiplier=2.0)
        self.assertTrue(spike_detected)
        
        # Testa sem spike
        normal_spike = self.ta.detect_volume_spike(self.test_df, multiplier=2.0)
        # Pode ou não detectar dependendo dos dados aleatórios
    
    def test_trend_analysis(self):
        """Testa análise de tendência"""
        trend = self.ta.analyze_trend(self.test_df, 20, 50)
        self.assertIn(trend, ['bullish', 'bearish', 'neutral'])
    
    def test_candlestick_patterns(self):
        """Testa identificação de padrões de candlestick"""
        patterns = self.ta.identify_candlestick_patterns(self.test_df)
        
        self.assertIsInstance(patterns, dict)
        # Verifica se retorna padrões conhecidos
        expected_patterns = ['doji', 'hammer', 'inverted_hammer', 'bullish_pinbar', 'bearish_pinbar']
        for pattern in expected_patterns:
            self.assertIn(pattern, patterns)
            self.assertIsInstance(patterns[pattern], bool)

class TestSignalGenerator(unittest.TestCase):
    """Testes para geração de sinais"""
    
    def setUp(self):
        self.signal_generator = SignalGenerator()
        
        # Cria dados de teste similares ao TestTechnicalAnalysis
        dates = pd.date_range('2024-01-01', periods=100, freq='1min')
        np.random.seed(42)
        
        base_price = 100
        prices = []
        volumes = []
        
        for i in range(100):
            change = np.random.normal(0, 0.5)
            base_price += change
            
            open_price = base_price
            high_price = base_price + abs(np.random.normal(0, 0.3))
            low_price = base_price - abs(np.random.normal(0, 0.3))
            close_price = base_price + np.random.normal(0, 0.2)
            
            prices.append([open_price, high_price, low_price, close_price])
            volumes.append(np.random.uniform(1000, 5000))
        
        prices = np.array(prices)
        
        self.test_df_1m = pd.DataFrame({
            'timestamp': dates,
            'open': prices[:, 0],
            'high': prices[:, 1],
            'low': prices[:, 2],
            'close': prices[:, 3],
            'volume': volumes
        })
        self.test_df_1m.set_index('timestamp', inplace=True)
        
        # Cria dados de 5m (simplificado)
        self.test_df_5m = self.test_df_1m.copy()
    
    def test_btc_trend_analysis(self):
        """Testa análise de tendência do BTC"""
        trend = self.signal_generator.analyze_btc_trend(self.test_df_5m)
        self.assertIn(trend, ['bullish', 'bearish', 'neutral'])
    
    def test_entry_conditions_check(self):
        """Testa verificação de condições de entrada"""
        signal = self.signal_generator.check_entry_conditions(
            self.test_df_1m, self.test_df_5m, 'bullish'
        )
        
        self.assertIsInstance(signal, dict)
        self.assertIn('has_signal', signal)
        self.assertIn('direction', signal)
        self.assertIn('strength', signal)
        self.assertIn('reasons', signal)
        self.assertIsInstance(signal['has_signal'], bool)
        
        if signal['has_signal']:
            self.assertIn(signal['direction'], ['LONG', 'SHORT'])
            self.assertIsInstance(signal['strength'], int)
            self.assertIsInstance(signal['reasons'], list)
    
    def test_position_size_calculation(self):
        """Testa cálculo do tamanho da posição"""
        balance = 1000
        price = 50000
        
        position_size = self.signal_generator.calculate_position_size(balance, price)
        
        self.assertGreater(position_size, 0)
        self.assertGreaterEqual(position_size, Config.MIN_POSITION_SIZE_USDT)
    
    def test_signal_validation(self):
        """Testa validação de qualidade do sinal"""
        # Sinal válido
        valid_signal = {
            'has_signal': True,
            'strength': 5,
            'price': 50000,
            'stop_loss': 49000,
            'fibonacci_levels': {'TP1': 51000, 'TP2': 52000, 'TP3': 53000}
        }
        
        self.assertTrue(self.signal_generator.validate_signal_quality(valid_signal))
        
        # Sinal inválido (força baixa)
        invalid_signal = {
            'has_signal': True,
            'strength': 2,
            'price': 50000,
            'stop_loss': 49000,
            'fibonacci_levels': {'TP1': 51000, 'TP2': 52000, 'TP3': 53000}
        }
        
        self.assertFalse(self.signal_generator.validate_signal_quality(invalid_signal))

class TestHelperFunctions(unittest.TestCase):
    """Testes para funções auxiliares"""
    
    def test_fibonacci_levels_long(self):
        """Testa cálculo de níveis de Fibonacci para LONG"""
        high = 110
        low = 100
        
        levels = calculate_fibonacci_levels(high, low, 'long')
        
        self.assertIn('TP1', levels)
        self.assertIn('TP2', levels)
        self.assertIn('TP3', levels)
        
        # Para LONG, TP1 deve ser menor que TP2, que deve ser menor que TP3
        self.assertLess(levels['TP1'], levels['TP2'])
        self.assertLess(levels['TP2'], levels['TP3'])
        
        # Todos os níveis devem estar entre low e high + diferença
        self.assertGreaterEqual(levels['TP1'], low)
        self.assertLessEqual(levels['TP3'], high + (high - low))
    
    def test_fibonacci_levels_short(self):
        """Testa cálculo de níveis de Fibonacci para SHORT"""
        high = 110
        low = 100
        
        levels = calculate_fibonacci_levels(high, low, 'short')
        
        # Para SHORT, TP1 deve ser maior que TP2, que deve ser maior que TP3
        self.assertGreater(levels['TP1'], levels['TP2'])
        self.assertGreater(levels['TP2'], levels['TP3'])
    
    def test_format_number(self):
        """Testa formatação de números"""
        self.assertEqual(format_number(123.456789, 2), "123.46")
        self.assertEqual(format_number(0.001234, 6), "0.001234")
    
    def test_validate_symbol(self):
        """Testa validação de símbolos"""
        self.assertEqual(validate_symbol("btc/usdt"), "BTC_USDT")
        self.assertEqual(validate_symbol("eth_usdt"), "ETH_USDT")
        self.assertEqual(validate_symbol("BTC_USDT"), "BTC_USDT")

class TestConfiguration(unittest.TestCase):
    """Testes para configurações"""
    
    def test_config_values(self):
        """Testa se as configurações têm valores válidos"""
        self.assertGreater(Config.LEVERAGE, 0)
        self.assertGreater(Config.POSITION_SIZE_PERCENT, 0)
        self.assertGreater(Config.MIN_POSITION_SIZE_USDT, 0)
        
        self.assertGreater(Config.RSI_PERIOD_SHORT, 0)
        self.assertGreater(Config.RSI_PERIOD_LONG, Config.RSI_PERIOD_SHORT)
        
        self.assertGreater(Config.EMA_FAST, 0)
        self.assertGreater(Config.EMA_SLOW, Config.EMA_FAST)
        
        self.assertGreater(Config.RSI_OVERSOLD, 0)
        self.assertLess(Config.RSI_OVERSOLD, 50)
        self.assertGreater(Config.RSI_OVERBOUGHT, 50)
        self.assertLess(Config.RSI_OVERBOUGHT, 100)

def run_tests():
    """Executa todos os testes"""
    # Cria suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adiciona classes de teste
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestSignalGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestHelperFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    
    # Executa testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

