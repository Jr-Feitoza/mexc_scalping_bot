#!/usr/bin/env python3
"""
Demonstração do funcionamento completo do bot de trading
Este script simula o funcionamento do bot sem usar APIs reais
"""

import sys
import os
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.indicators.technical_analysis import TechnicalAnalysis
from src.strategies.signal_generator import SignalGenerator
from src.alerts.telegram_bot import TelegramBot
from src.utils.data_manager import DataManager

class TradingBotDemo:
    """Demonstração do bot de trading"""
    
    def __init__(self):
        self.ta = TechnicalAnalysis()
        self.signal_generator = SignalGenerator()
        self.demo_pairs = ['BTC_USDT', 'ETH_USDT', 'BNB_USDT', 'ADA_USDT', 'SOL_USDT']
    
    def generate_realistic_data(self, symbol: str, periods: int = 100) -> pd.DataFrame:
        """
        Gera dados realistas de mercado para demonstração
        
        Args:
            symbol: Símbolo do par
            periods: Número de períodos
        
        Returns:
            DataFrame com dados OHLCV
        """
        # Define preço base baseado no símbolo
        base_prices = {
            'BTC_USDT': 50000,
            'ETH_USDT': 3000,
            'BNB_USDT': 300,
            'ADA_USDT': 0.5,
            'SOL_USDT': 100
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # Gera timestamps
        dates = pd.date_range('2024-06-26 10:00:00', periods=periods, freq='1min')
        
        # Simula movimento de preço com diferentes cenários
        np.random.seed(hash(symbol) % 1000)  # Seed baseado no símbolo para consistência
        
        prices = []
        volumes = []
        current_price = base_price
        
        # Simula diferentes fases do mercado
        for i in range(periods):
            # Fase 1: Consolidação (primeiros 30%)
            if i < periods * 0.3:
                change = np.random.normal(0, base_price * 0.002)  # 0.2% volatilidade
            # Fase 2: Tendência (próximos 40%)
            elif i < periods * 0.7:
                trend_strength = 0.001 if symbol in ['BTC_USDT', 'ETH_USDT'] else 0.002
                change = np.random.normal(trend_strength * base_price, base_price * 0.003)  # Tendência de alta
            # Fase 3: Reversão (últimos 30%)
            else:
                change = np.random.normal(-0.0005 * base_price, base_price * 0.004)  # Pequena correção
            
            current_price += change
            
            # Gera OHLC baseado no preço atual
            volatility = base_price * 0.001
            open_price = current_price + np.random.normal(0, volatility * 0.5)
            high_price = max(open_price, current_price) + abs(np.random.normal(0, volatility))
            low_price = min(open_price, current_price) - abs(np.random.normal(0, volatility))
            close_price = current_price + np.random.normal(0, volatility * 0.5)
            
            # Volume baseado na volatilidade
            base_volume = 1000 if symbol in ['BTC_USDT', 'ETH_USDT'] else 5000
            volume_multiplier = 1 + abs(change / base_price) * 10  # Mais volume em movimentos grandes
            volume = base_volume * volume_multiplier * np.random.uniform(0.5, 2.0)
            
            prices.append([open_price, high_price, low_price, close_price])
            volumes.append(volume)
        
        prices = np.array(prices)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices[:, 0],
            'high': prices[:, 1],
            'low': prices[:, 2],
            'close': prices[:, 3],
            'volume': volumes
        })
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def analyze_pair(self, symbol: str) -> dict:
        """
        Analisa um par específico
        
        Args:
            symbol: Símbolo do par
        
        Returns:
            Resultado da análise
        """
        print(f"\n📊 Analisando {symbol}...")
        
        # Gera dados de 1m e 5m
        data_1m = self.generate_realistic_data(symbol, 100)
        data_5m = self.generate_realistic_data(symbol, 50)  # Simula timeframe maior
        
        # Análise técnica completa
        analysis = self.ta.get_comprehensive_analysis(data_1m)
        
        print(f"   💰 Preço atual: ${analysis.get('current_price', 0):.6f}")
        print(f"   📈 RSI 7: {analysis.get('rsi_7', 0):.1f} | RSI 14: {analysis.get('rsi_14', 0):.1f}")
        print(f"   📊 Tendência: {analysis.get('trend', 'N/A')}")
        print(f"   📈 Volume spike: {'✅' if analysis.get('volume_spike') else '❌'}")
        
        # Padrões de candlestick
        patterns = analysis.get('candlestick_patterns', {})
        active_patterns = [pattern for pattern, active in patterns.items() if active]
        if active_patterns:
            print(f"   🕯️ Padrões: {', '.join(active_patterns)}")
        
        # Verifica condições de entrada
        btc_trend = 'bullish'  # Simula tendência bullish do BTC
        signal = self.signal_generator.check_entry_conditions(data_1m, data_5m, btc_trend)
        
        return {
            'symbol': symbol,
            'analysis': analysis,
            'signal': signal,
            'data_1m': data_1m,
            'data_5m': data_5m
        }
    
    def format_signal_summary(self, signal: dict, symbol: str) -> str:
        """Formata resumo do sinal"""
        if not signal.get('has_signal'):
            return f"   ❌ Nenhum sinal detectado para {symbol}"
        
        direction_emoji = "🟢" if signal['direction'] == 'LONG' else "🔴"
        
        summary = f"""   {direction_emoji} SINAL {signal['direction']} detectado!
   ⭐ Força: {signal['strength']}/7
   💰 Preço: ${signal['price']:.6f}
   🎯 TP1: ${signal['fibonacci_levels'].get('TP1', 0):.6f}
   🛡️ SL: ${signal['stop_loss']:.6f}
   📋 Motivos: {len(signal['reasons'])} confirmações"""
        
        return summary
    
    async def run_demo(self):
        """Executa demonstração completa"""
        print("🤖 MEXC Scalping Bot - Demonstração")
        print("=" * 50)
        print(f"⏰ Horário: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"📈 Tendência do BTC: BULLISH (simulado)")
        print(f"💰 Pares monitorados: {len(self.demo_pairs)}")
        
        signals_found = []
        
        # Analisa cada par
        for symbol in self.demo_pairs:
            try:
                result = self.analyze_pair(symbol)
                
                # Mostra resumo do sinal
                signal_summary = self.format_signal_summary(result['signal'], symbol)
                print(signal_summary)
                
                # Coleta sinais válidos
                if result['signal'].get('has_signal'):
                    if self.signal_generator.validate_signal_quality(result['signal']):
                        signals_found.append(result)
                        print(f"   ✅ Sinal válido adicionado à lista")
                    else:
                        print(f"   ⚠️ Sinal não passou na validação de qualidade")
                
            except Exception as e:
                print(f"   ❌ Erro ao analisar {symbol}: {str(e)}")
        
        # Resumo final
        print("\n" + "=" * 50)
        print(f"📊 RESUMO DA ANÁLISE")
        print(f"🔍 Pares analisados: {len(self.demo_pairs)}")
        print(f"🚨 Sinais encontrados: {len(signals_found)}")
        
        # Mostra sinais detalhados
        if signals_found:
            print(f"\n📋 SINAIS DETECTADOS:")
            for i, result in enumerate(signals_found, 1):
                signal = result['signal']
                symbol = result['symbol']
                
                print(f"\n{i}. {symbol} - {signal['direction']}")
                print(f"   💰 Preço: ${signal['price']:.6f}")
                print(f"   ⭐ Força: {signal['strength']}/7")
                print(f"   📊 RSI: {signal['rsi_7']:.1f} / {signal['rsi_14']:.1f}")
                print(f"   🎯 Take Profits:")
                for level, price in signal['fibonacci_levels'].items():
                    print(f"      {level}: ${price:.6f}")
                print(f"   🛡️ Stop Loss: ${signal['stop_loss']:.6f}")
                print(f"   📋 Motivos:")
                for reason in signal['reasons']:
                    print(f"      • {reason}")
                
                # Simula envio de alerta
                position_size = self.signal_generator.calculate_position_size(1000, signal['price'])
                print(f"   💰 Tamanho sugerido: ${position_size:.2f} USDT")
                print(f"   📱 Alerta enviado via Telegram (simulado)")
        else:
            print("   ℹ️ Nenhum sinal válido encontrado neste ciclo")
        
        print(f"\n⏰ Próxima análise em 5 minutos...")
        print("🛑 Demonstração concluída!")
    
    def show_technical_analysis_details(self, symbol: str):
        """Mostra detalhes da análise técnica"""
        print(f"\n🔬 ANÁLISE TÉCNICA DETALHADA - {symbol}")
        print("-" * 40)
        
        data = self.generate_realistic_data(symbol, 100)
        analysis = self.ta.get_comprehensive_analysis(data)
        
        print(f"📊 Indicadores:")
        print(f"   RSI 7: {analysis.get('rsi_7', 0):.2f}")
        print(f"   RSI 14: {analysis.get('rsi_14', 0):.2f}")
        print(f"   EMA 20: ${analysis.get('ema_20', 0):.6f}")
        print(f"   EMA 50: ${analysis.get('ema_50', 0):.6f}")
        print(f"   ATR: {analysis.get('atr', 0):.6f}")
        
        print(f"\n📈 Análise:")
        print(f"   Tendência: {analysis.get('trend', 'N/A')}")
        print(f"   OBV Trend: {analysis.get('obv_trend', 'N/A')}")
        print(f"   Volume Spike: {'Sim' if analysis.get('volume_spike') else 'Não'}")
        
        print(f"\n🕯️ Padrões de Candlestick:")
        patterns = analysis.get('candlestick_patterns', {})
        for pattern, active in patterns.items():
            status = "✅" if active else "❌"
            print(f"   {status} {pattern.replace('_', ' ').title()}")
        
        print(f"\n📊 Suporte e Resistência:")
        print(f"   Suporte: ${analysis.get('support', 0):.6f}")
        print(f"   Resistência: ${analysis.get('resistance', 0):.6f}")

def main():
    """Função principal da demonstração"""
    demo = TradingBotDemo()
    
    print("Escolha uma opção:")
    print("1. Demonstração completa")
    print("2. Análise técnica detalhada de um par")
    print("3. Análise de todos os pares")
    
    try:
        choice = input("\nDigite sua escolha (1-3): ").strip()
        
        if choice == "1":
            asyncio.run(demo.run_demo())
        elif choice == "2":
            print("\nPares disponíveis:", ", ".join(demo.demo_pairs))
            symbol = input("Digite o símbolo (ex: BTC_USDT): ").strip().upper()
            if symbol in demo.demo_pairs:
                demo.show_technical_analysis_details(symbol)
            else:
                print("Símbolo não encontrado!")
        elif choice == "3":
            for symbol in demo.demo_pairs:
                demo.show_technical_analysis_details(symbol)
        else:
            print("Opção inválida!")
            
    except KeyboardInterrupt:
        print("\n\nDemonstração interrompida pelo usuário.")
    except Exception as e:
        print(f"\nErro na demonstração: {str(e)}")

if __name__ == "__main__":
    main()

