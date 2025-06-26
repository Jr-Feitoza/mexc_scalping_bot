import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from config.config import Config, TradingPairs
from src.indicators.technical_analysis import TechnicalAnalysis
from src.utils.helpers import calculate_fibonacci_levels, calculate_atr_stop_loss
from src.utils.logger import logger

class SignalGenerator:
    """Gerador de sinais de trading baseado em análise técnica"""
    
    def __init__(self):
        self.ta = TechnicalAnalysis()
        self.config = Config()
        
    def analyze_btc_trend(self, btc_data: pd.DataFrame) -> str:
        """
        Analisa a tendência do BTC como referência para o mercado
        
        Args:
            btc_data: DataFrame com dados do BTC_USDT
        
        Returns:
            'bullish', 'bearish' ou 'neutral'
        """
        try:
            if len(btc_data) < 50:
                return 'neutral'
            
            # Análise baseada em EMAs
            trend = self.ta.analyze_trend(btc_data, 20, 50)
            
            # Análise adicional com RSI
            rsi = self.ta.calculate_rsi(btc_data, 14)
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            
            # Confirma tendência com RSI
            if trend == 'bullish' and current_rsi > 40:
                return 'bullish'
            elif trend == 'bearish' and current_rsi < 60:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Erro ao analisar tendência do BTC: {str(e)}")
            return 'neutral'
    
    def check_entry_conditions(self, df_1m: pd.DataFrame, df_5m: pd.DataFrame, btc_trend: str) -> Dict:
        """
        Verifica condições de entrada para um par
        
        Args:
            df_1m: DataFrame com dados de 1 minuto
            df_5m: DataFrame com dados de 5 minutos
            btc_trend: Tendência do BTC
        
        Returns:
            Dicionário com resultado da análise
        """
        try:
            signal = {
                'has_signal': False,
                'direction': None,
                'strength': 0,
                'reasons': [],
                'price': None,
                'rsi_7': None,
                'rsi_14': None,
                'volume_spike': False,
                'candlestick_patterns': {},
                'fibonacci_levels': {},
                'stop_loss': None
            }
            
            if len(df_1m) < 50 or len(df_5m) < 50:
                return signal
            
            # Análise técnica completa
            analysis_1m = self.ta.get_comprehensive_analysis(df_1m)
            analysis_5m = self.ta.get_comprehensive_analysis(df_5m)
            
            signal['price'] = analysis_1m.get('current_price')
            signal['rsi_7'] = analysis_1m.get('rsi_7')
            signal['rsi_14'] = analysis_1m.get('rsi_14')
            signal['volume_spike'] = analysis_1m.get('volume_spike', False)
            signal['candlestick_patterns'] = analysis_1m.get('candlestick_patterns', {})
            
            # Verifica condições para LONG
            long_conditions = self._check_long_conditions(analysis_1m, analysis_5m, btc_trend)
            
            # Verifica condições para SHORT
            short_conditions = self._check_short_conditions(analysis_1m, analysis_5m, btc_trend)
            
            # Determina sinal
            if long_conditions['score'] > short_conditions['score'] and long_conditions['score'] >= 3:
                signal['has_signal'] = True
                signal['direction'] = 'LONG'
                signal['strength'] = long_conditions['score']
                signal['reasons'] = long_conditions['reasons']
                
                # Calcula níveis de Fibonacci para LONG
                high = df_5m['high'].tail(20).max()
                low = df_5m['low'].tail(20).min()
                signal['fibonacci_levels'] = calculate_fibonacci_levels(high, low, 'long')
                
                # Calcula stop loss
                signal['stop_loss'] = calculate_atr_stop_loss(df_1m, 14, 2.0, 'long')
                
            elif short_conditions['score'] > long_conditions['score'] and short_conditions['score'] >= 3:
                signal['has_signal'] = True
                signal['direction'] = 'SHORT'
                signal['strength'] = short_conditions['score']
                signal['reasons'] = short_conditions['reasons']
                
                # Calcula níveis de Fibonacci para SHORT
                high = df_5m['high'].tail(20).max()
                low = df_5m['low'].tail(20).min()
                signal['fibonacci_levels'] = calculate_fibonacci_levels(high, low, 'short')
                
                # Calcula stop loss
                signal['stop_loss'] = calculate_atr_stop_loss(df_1m, 14, 2.0, 'short')
            
            return signal
            
        except Exception as e:
            logger.error(f"Erro ao verificar condições de entrada: {str(e)}")
            return signal
    
    def _check_long_conditions(self, analysis_1m: Dict, analysis_5m: Dict, btc_trend: str) -> Dict:
        """
        Verifica condições específicas para entrada LONG
        
        Args:
            analysis_1m: Análise técnica de 1 minuto
            analysis_5m: Análise técnica de 5 minutos
            btc_trend: Tendência do BTC
        
        Returns:
            Dicionário com score e razões
        """
        score = 0
        reasons = []
        
        try:
            # 1. Tendência do BTC favorável
            if btc_trend == 'bullish':
                score += 1
                reasons.append("Tendência do BTC bullish")
            
            # 2. RSI em zona de sobrevenda (1m)
            rsi_7 = analysis_1m.get('rsi_7')
            rsi_14 = analysis_1m.get('rsi_14')
            
            if rsi_7 and rsi_7 < Config.RSI_OVERSOLD:
                score += 1
                reasons.append(f"RSI 7 em sobrevenda ({rsi_7:.1f})")
            
            if rsi_14 and rsi_14 < Config.RSI_OVERSOLD:
                score += 1
                reasons.append(f"RSI 14 em sobrevenda ({rsi_14:.1f})")
            
            # 3. Tendência das EMAs (5m)
            if analysis_5m.get('trend') == 'bullish':
                score += 1
                reasons.append("Tendência das EMAs bullish (5m)")
            
            # 4. OBV crescente
            if analysis_1m.get('obv_trend') == 'rising':
                score += 1
                reasons.append("OBV em alta")
            
            # 5. Volume spike
            if analysis_1m.get('volume_spike'):
                score += 1
                reasons.append("Spike de volume detectado")
            
            # 6. Padrões de candlestick bullish
            patterns = analysis_1m.get('candlestick_patterns', {})
            bullish_patterns = ['hammer', 'bullish_engulfing', 'bullish_pinbar']
            
            for pattern in bullish_patterns:
                if patterns.get(pattern):
                    score += 1
                    reasons.append(f"Padrão {pattern} detectado")
                    break  # Conta apenas um padrão
            
            # 7. Preço próximo ao suporte
            current_price = analysis_1m.get('current_price')
            support = analysis_5m.get('support')
            
            if current_price and support and current_price <= support * 1.02:  # 2% acima do suporte
                score += 1
                reasons.append("Preço próximo ao suporte")
            
            return {'score': score, 'reasons': reasons}
            
        except Exception as e:
            logger.error(f"Erro ao verificar condições LONG: {str(e)}")
            return {'score': 0, 'reasons': []}
    
    def _check_short_conditions(self, analysis_1m: Dict, analysis_5m: Dict, btc_trend: str) -> Dict:
        """
        Verifica condições específicas para entrada SHORT
        
        Args:
            analysis_1m: Análise técnica de 1 minuto
            analysis_5m: Análise técnica de 5 minutos
            btc_trend: Tendência do BTC
        
        Returns:
            Dicionário com score e razões
        """
        score = 0
        reasons = []
        
        try:
            # 1. Tendência do BTC favorável
            if btc_trend == 'bearish':
                score += 1
                reasons.append("Tendência do BTC bearish")
            
            # 2. RSI em zona de sobrecompra (1m)
            rsi_7 = analysis_1m.get('rsi_7')
            rsi_14 = analysis_1m.get('rsi_14')
            
            if rsi_7 and rsi_7 > Config.RSI_OVERBOUGHT:
                score += 1
                reasons.append(f"RSI 7 em sobrecompra ({rsi_7:.1f})")
            
            if rsi_14 and rsi_14 > Config.RSI_OVERBOUGHT:
                score += 1
                reasons.append(f"RSI 14 em sobrecompra ({rsi_14:.1f})")
            
            # 3. Tendência das EMAs (5m)
            if analysis_5m.get('trend') == 'bearish':
                score += 1
                reasons.append("Tendência das EMAs bearish (5m)")
            
            # 4. OBV decrescente
            if analysis_1m.get('obv_trend') == 'falling':
                score += 1
                reasons.append("OBV em queda")
            
            # 5. Volume spike
            if analysis_1m.get('volume_spike'):
                score += 1
                reasons.append("Spike de volume detectado")
            
            # 6. Padrões de candlestick bearish
            patterns = analysis_1m.get('candlestick_patterns', {})
            bearish_patterns = ['inverted_hammer', 'bearish_engulfing', 'bearish_pinbar']
            
            for pattern in bearish_patterns:
                if patterns.get(pattern):
                    score += 1
                    reasons.append(f"Padrão {pattern} detectado")
                    break  # Conta apenas um padrão
            
            # 7. Preço próximo à resistência
            current_price = analysis_1m.get('current_price')
            resistance = analysis_5m.get('resistance')
            
            if current_price and resistance and current_price >= resistance * 0.98:  # 2% abaixo da resistência
                score += 1
                reasons.append("Preço próximo à resistência")
            
            return {'score': score, 'reasons': reasons}
            
        except Exception as e:
            logger.error(f"Erro ao verificar condições SHORT: {str(e)}")
            return {'score': 0, 'reasons': []}
    
    def is_priority_time(self) -> bool:
        """
        Verifica se é um horário prioritário para análise
        
        Returns:
            True se for horário prioritário
        """
        try:
            current_hour = datetime.now(timezone.utc).hour
            return current_hour in Config.PRIORITY_HOURS
        except Exception as e:
            logger.error(f"Erro ao verificar horário prioritário: {str(e)}")
            return False
    
    def calculate_position_size(self, balance: float, price: float, leverage: int = None) -> float:
        """
        Calcula o tamanho da posição baseado na configuração
        
        Args:
            balance: Saldo disponível
            price: Preço atual do ativo
            leverage: Alavancagem (opcional)
        
        Returns:
            Tamanho da posição em USDT
        """
        try:
            leverage = leverage or Config.LEVERAGE
            
            # Calcula 1% da margem
            position_value = balance * (Config.POSITION_SIZE_PERCENT / 100)
            
            # Aplica valor mínimo
            position_value = max(position_value, Config.MIN_POSITION_SIZE_USDT)
            
            return position_value
            
        except Exception as e:
            logger.error(f"Erro ao calcular tamanho da posição: {str(e)}")
            return Config.MIN_POSITION_SIZE_USDT
    
    def format_signal_message(self, symbol: str, signal: Dict, position_size: float) -> str:
        """
        Formata mensagem do sinal para envio
        
        Args:
            symbol: Símbolo do par
            signal: Dados do sinal
            position_size: Tamanho da posição
        
        Returns:
            Mensagem formatada
        """
        try:
            if not signal.get('has_signal'):
                return ""
            
            # Formata níveis de Fibonacci
            fib_levels = signal.get('fibonacci_levels', {})
            tp1 = fib_levels.get('TP1', 0)
            tp2 = fib_levels.get('TP2', 0)
            tp3 = fib_levels.get('TP3', 0)
            
            # Formata razões do sinal
            reasons = "\n".join([f"• {reason}" for reason in signal.get('reasons', [])])
            
            # Formata padrões de candlestick
            patterns = signal.get('candlestick_patterns', {})
            active_patterns = [pattern for pattern, active in patterns.items() if active]
            patterns_text = ", ".join(active_patterns) if active_patterns else "Nenhum"
            
            message = f"""
🚨 SINAL DE ENTRADA DETECTADO 🚨

💰 Par: {symbol}
📈 Direção: {signal['direction']}
💵 Preço Atual: ${signal['price']:.6f}
📊 RSI 7: {signal['rsi_7']:.1f} | RSI 14: {signal['rsi_14']:.1f}
📊 Volume Spike: {'✅' if signal['volume_spike'] else '❌'}
🕯️ Padrões: {patterns_text}

🎯 Alvos Fibonacci:
• TP1 (38.2%): ${tp1:.6f}
• TP2 (61.8%): ${tp2:.6f}
• TP3 (100%): ${tp3:.6f}

🛡️ Stop Loss Sugerido: ${signal['stop_loss']:.6f}

⚡ Alavancagem: {Config.LEVERAGE}x
💰 Tamanho da Posição: ${position_size:.2f} USDT
⭐ Força do Sinal: {signal['strength']}/7

📊 Motivos do Sinal:
{reasons}

⏰ Horário: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"Erro ao formatar mensagem do sinal: {str(e)}")
            return ""
    
    def validate_signal_quality(self, signal: Dict) -> bool:
        """
        Valida a qualidade do sinal antes de enviar
        
        Args:
            signal: Dados do sinal
        
        Returns:
            True se o sinal for válido
        """
        try:
            if not signal.get('has_signal'):
                return False
            
            # Verifica força mínima do sinal
            if signal.get('strength', 0) < 3:
                return False
            
            # Verifica se tem preço válido
            if not signal.get('price') or signal['price'] <= 0:
                return False
            
            # Verifica se tem stop loss válido
            if not signal.get('stop_loss') or signal['stop_loss'] <= 0:
                return False
            
            # Verifica se tem níveis de Fibonacci
            fib_levels = signal.get('fibonacci_levels', {})
            if not fib_levels or not all(level > 0 for level in fib_levels.values()):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar qualidade do sinal: {str(e)}")
            return False

