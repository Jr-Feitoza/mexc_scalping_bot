#!/usr/bin/env python3
"""
Teste de integração para validar o fluxo completo do sistema
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import numpy as np

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.mexc_client import MEXCClient
from src.strategies.signal_generator import SignalGenerator
from src.alerts.telegram_bot import TelegramBot
from src.utils.data_manager import DataManager

class TestIntegration(unittest.TestCase):
    """Testes de integração do sistema completo"""
    
    def setUp(self):
        """Configura mocks para os testes"""
        # Dados de teste
        dates = pd.date_range('2024-01-01', periods=100, freq='1min')
        np.random.seed(42)
        
        base_price = 50000
        prices = []
        volumes = []
        
        for i in range(100):
            # Simula movimento com tendência
            change = np.random.normal(0, 100) + (i * 2)  # Tendência de alta
            base_price += change
            
            open_price = base_price
            high_price = base_price + abs(np.random.normal(0, 50))
            low_price = base_price - abs(np.random.normal(0, 50))
            close_price = base_price + np.random.normal(0, 30)
            
            prices.append([open_price, high_price, low_price, close_price])
            volumes.append(np.random.uniform(1000, 5000))
        
        prices = np.array(prices)
        
        self.mock_data = pd.DataFrame({
            'timestamp': dates,
            'open': prices[:, 0],
            'high': prices[:, 1],
            'low': prices[:, 2],
            'close': prices[:, 3],
            'volume': volumes
        })
        self.mock_data.set_index('timestamp', inplace=True)
    
    @patch('src.api.mexc_client.requests.Session')
    def test_mexc_client_integration(self, mock_session):
        """Testa integração com cliente MEXC"""
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                [1640995200, 50000, 50100, 49900, 50050, 1000],
                [1640995260, 50050, 50150, 49950, 50100, 1200]
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_session.return_value.get.return_value = mock_response
        
        client = MEXCClient()
        
        # Testa obtenção de klines
        klines = client.get_klines('BTC_USDT', 'Min1')
        self.assertIsInstance(klines, list)
        self.assertGreater(len(klines), 0)
        
        # Testa conversão para DataFrame
        df = client.klines_to_dataframe(klines)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn('open', df.columns)
        self.assertIn('high', df.columns)
        self.assertIn('low', df.columns)
        self.assertIn('close', df.columns)
        self.assertIn('volume', df.columns)
    
    def test_signal_generation_flow(self):
        """Testa fluxo completo de geração de sinais"""
        signal_generator = SignalGenerator()
        
        # Simula análise de tendência do BTC
        btc_trend = signal_generator.analyze_btc_trend(self.mock_data)
        self.assertIn(btc_trend, ['bullish', 'bearish', 'neutral'])
        
        # Verifica condições de entrada
        signal = signal_generator.check_entry_conditions(
            self.mock_data, self.mock_data, btc_trend
        )
        
        self.assertIsInstance(signal, dict)
        self.assertIn('has_signal', signal)
        
        # Se houver sinal, valida estrutura
        if signal['has_signal']:
            self.assertIn('direction', signal)
            self.assertIn('strength', signal)
            self.assertIn('price', signal)
            self.assertIn('fibonacci_levels', signal)
            self.assertIn('stop_loss', signal)
            
            # Valida qualidade do sinal
            is_valid = signal_generator.validate_signal_quality(signal)
            self.assertIsInstance(is_valid, bool)
            
            # Testa formatação da mensagem
            position_size = 100
            message = signal_generator.format_signal_message('BTC_USDT', signal, position_size)
            
            if is_valid:
                self.assertIsInstance(message, str)
                self.assertGreater(len(message), 0)
                self.assertIn('BTC_USDT', message)
                self.assertIn(signal['direction'], message)
    
    @patch('aiohttp.ClientSession.post')
    async def test_telegram_integration(self, mock_post):
        """Testa integração com Telegram"""
        # Mock da resposta do Telegram
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'ok': True})
        
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Configura bot com credenciais de teste
        telegram_bot = TelegramBot('test_token', 'test_chat_id')
        
        # Testa envio de mensagem
        result = await telegram_bot.send_message("Teste de integração")
        self.assertTrue(result)
        
        # Testa envio de alerta de sinal
        signal_data = {
            'has_signal': True,
            'direction': 'LONG',
            'price': 50000,
            'rsi_7': 25,
            'rsi_14': 30,
            'volume_spike': True,
            'strength': 5,
            'reasons': ['RSI oversold', 'Volume spike'],
            'fibonacci_levels': {'TP1': 51000, 'TP2': 52000, 'TP3': 53000},
            'stop_loss': 49000
        }
        
        result = await telegram_bot.send_signal_alert('BTC_USDT', signal_data, 100)
        self.assertTrue(result)
    
    @patch('src.utils.data_manager.MEXCClient')
    def test_data_manager_integration(self, mock_mexc_client):
        """Testa integração do gerenciador de dados"""
        # Mock do cliente MEXC
        mock_client = Mock()
        mock_client.get_klines.return_value = [
            [1640995200, 50000, 50100, 49900, 50050, 1000],
            [1640995260, 50050, 50150, 49950, 50100, 1200]
        ]
        mock_client.klines_to_dataframe.return_value = self.mock_data.head(10)
        mock_mexc_client.return_value = mock_client
        
        data_manager = DataManager()
        
        # Testa obtenção de dados de mercado
        df = data_manager.get_market_data('BTC_USDT', 'Min1', use_cache=False)
        self.assertIsInstance(df, pd.DataFrame)
        
        # Testa múltiplos timeframes
        data = data_manager.get_multiple_timeframes('BTC_USDT', ['Min1', 'Min5'])
        self.assertIsInstance(data, dict)
        
        # Testa cache
        df_cached = data_manager.get_market_data('BTC_USDT', 'Min1', use_cache=True)
        self.assertIsInstance(df_cached, pd.DataFrame)
    
    def test_complete_analysis_flow(self):
        """Testa fluxo completo de análise"""
        signal_generator = SignalGenerator()
        
        # Simula dados com condições favoráveis para LONG
        favorable_data = self.mock_data.copy()
        
        # Modifica RSI para zona de sobrevenda
        from src.indicators.technical_analysis import TechnicalAnalysis
        ta = TechnicalAnalysis()
        
        # Força condições favoráveis
        favorable_data.loc[favorable_data.index[-5:], 'close'] = favorable_data['close'].iloc[-6] * 0.95  # Queda de 5%
        favorable_data.loc[favorable_data.index[-1], 'volume'] = favorable_data['volume'].mean() * 3  # Volume spike
        
        # Analisa tendência do BTC (simula bullish)
        btc_trend = 'bullish'
        
        # Verifica condições de entrada
        signal = signal_generator.check_entry_conditions(
            favorable_data, favorable_data, btc_trend
        )
        
        # Valida estrutura do sinal
        self.assertIsInstance(signal, dict)
        required_keys = ['has_signal', 'direction', 'strength', 'reasons', 'price', 'fibonacci_levels', 'stop_loss']
        for key in required_keys:
            self.assertIn(key, signal)
        
        # Se houver sinal, testa cálculos
        if signal['has_signal']:
            # Testa cálculo de posição
            position_size = signal_generator.calculate_position_size(1000, signal['price'])
            self.assertGreater(position_size, 0)
            
            # Testa validação
            is_valid = signal_generator.validate_signal_quality(signal)
            self.assertIsInstance(is_valid, bool)
            
            # Testa formatação
            message = signal_generator.format_signal_message('BTC_USDT', signal, position_size)
            if is_valid:
                self.assertIsInstance(message, str)
                self.assertGreater(len(message), 0)

def run_integration_tests():
    """Executa testes de integração"""
    # Cria suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adiciona testes de integração
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Executa testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

async def run_async_tests():
    """Executa testes assíncronos"""
    test_instance = TestIntegration()
    test_instance.setUp()
    
    try:
        await test_instance.test_telegram_integration()
        print("✅ Teste assíncrono do Telegram passou")
        return True
    except Exception as e:
        print(f"❌ Teste assíncrono do Telegram falhou: {e}")
        return False

if __name__ == '__main__':
    print("Executando testes de integração...")
    
    # Testes síncronos
    sync_success = run_integration_tests()
    
    # Testes assíncronos
    async_success = asyncio.run(run_async_tests())
    
    overall_success = sync_success and async_success
    
    if overall_success:
        print("\n✅ Todos os testes de integração passaram!")
    else:
        print("\n❌ Alguns testes de integração falharam!")
    
    sys.exit(0 if overall_success else 1)

