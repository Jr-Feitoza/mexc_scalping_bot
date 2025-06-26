import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from config.config import Config
from src.indicators.technical_analysis import TechnicalAnalysis
from src.utils.helpers import calculate_fibonacci_levels, calculate_atr_stop_loss
from src.utils.logger import logger

class ExitManager:
    """
    Gerenciador de saída para posições abertas
    
    Nota: Este módulo é condicional pois a API da MEXC pode não permitir
    modificação de ordens para usuários comuns. Serve como base para
    futuras implementações ou para exchanges que permitam.
    """
    
    def __init__(self):
        self.ta = TechnicalAnalysis()
        self.config = Config()
        self.active_positions = {}  # Cache de posições ativas
    
    def analyze_exit_conditions(self, symbol: str, position_data: Dict, market_data_1m: pd.DataFrame, 
                               market_data_5m: pd.DataFrame) -> Dict:
        """
        Analisa condições de saída para uma posição
        
        Args:
            symbol: Símbolo do par
            position_data: Dados da posição (direção, preço de entrada, etc.)
            market_data_1m: Dados de 1 minuto
            market_data_5m: Dados de 5 minutos
        
        Returns:
            Dicionário com análise de saída
        """
        try:
            exit_analysis = {
                'should_exit': False,
                'exit_reason': None,
                'exit_type': None,  # 'take_profit', 'stop_loss', 'trailing_stop', 'reversal'
                'suggested_exit_price': None,
                'profit_loss_pct': 0,
                'fibonacci_hit': None,
                'technical_signals': {}
            }
            
            if market_data_1m.empty or market_data_5m.empty:
                return exit_analysis
            
            current_price = market_data_1m['close'].iloc[-1]
            entry_price = position_data.get('entry_price', 0)
            direction = position_data.get('direction', '').upper()
            
            if not entry_price or not direction:
                return exit_analysis
            
            # Calcula P&L atual
            if direction == 'LONG':
                profit_loss_pct = ((current_price - entry_price) / entry_price) * 100
            else:  # SHORT
                profit_loss_pct = ((entry_price - current_price) / entry_price) * 100
            
            exit_analysis['profit_loss_pct'] = profit_loss_pct
            exit_analysis['suggested_exit_price'] = current_price
            
            # Verifica níveis de Fibonacci (Take Profit)
            fib_hit = self._check_fibonacci_levels(position_data, current_price)
            if fib_hit:
                exit_analysis['should_exit'] = True
                exit_analysis['exit_type'] = 'take_profit'
                exit_analysis['exit_reason'] = f"Fibonacci {fib_hit} atingido"
                exit_analysis['fibonacci_hit'] = fib_hit
                return exit_analysis
            
            # Verifica Stop Loss dinâmico
            stop_loss_hit = self._check_dynamic_stop_loss(position_data, market_data_1m, market_data_5m)
            if stop_loss_hit['should_stop']:
                exit_analysis['should_exit'] = True
                exit_analysis['exit_type'] = 'stop_loss'
                exit_analysis['exit_reason'] = stop_loss_hit['reason']
                return exit_analysis
            
            # Verifica reversão de tendência
            reversal_signal = self._check_trend_reversal(position_data, market_data_1m, market_data_5m)
            if reversal_signal['should_exit']:
                exit_analysis['should_exit'] = True
                exit_analysis['exit_type'] = 'reversal'
                exit_analysis['exit_reason'] = reversal_signal['reason']
                exit_analysis['technical_signals'] = reversal_signal['signals']
                return exit_analysis
            
            # Verifica trailing stop
            trailing_stop = self._check_trailing_stop(position_data, market_data_1m)
            if trailing_stop['should_stop']:
                exit_analysis['should_exit'] = True
                exit_analysis['exit_type'] = 'trailing_stop'
                exit_analysis['exit_reason'] = trailing_stop['reason']
                return exit_analysis
            
            return exit_analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar condições de saída para {symbol}: {str(e)}")
            return exit_analysis
    
    def _check_fibonacci_levels(self, position_data: Dict, current_price: float) -> Optional[str]:
        """
        Verifica se algum nível de Fibonacci foi atingido
        
        Args:
            position_data: Dados da posição
            current_price: Preço atual
        
        Returns:
            Nome do nível atingido ou None
        """
        try:
            fibonacci_levels = position_data.get('fibonacci_levels', {})
            direction = position_data.get('direction', '').upper()
            
            if not fibonacci_levels:
                return None
            
            # Para posições LONG, verifica se preço atingiu níveis superiores
            if direction == 'LONG':
                for level_name in ['TP1', 'TP2', 'TP3']:
                    level_price = fibonacci_levels.get(level_name)
                    if level_price and current_price >= level_price:
                        return level_name
            
            # Para posições SHORT, verifica se preço atingiu níveis inferiores
            elif direction == 'SHORT':
                for level_name in ['TP1', 'TP2', 'TP3']:
                    level_price = fibonacci_levels.get(level_name)
                    if level_price and current_price <= level_price:
                        return level_name
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao verificar níveis de Fibonacci: {str(e)}")
            return None
    
    def _check_dynamic_stop_loss(self, position_data: Dict, df_1m: pd.DataFrame, df_5m: pd.DataFrame) -> Dict:
        """
        Verifica stop loss dinâmico baseado em múltiplos critérios
        
        Args:
            position_data: Dados da posição
            df_1m: Dados de 1 minuto
            df_5m: Dados de 5 minutos
        
        Returns:
            Dicionário com resultado da verificação
        """
        try:
            result = {'should_stop': False, 'reason': None}
            
            direction = position_data.get('direction', '').upper()
            entry_price = position_data.get('entry_price', 0)
            current_price = df_1m['close'].iloc[-1]
            
            # 1. Stop Loss baseado em ATR
            atr_stop = calculate_atr_stop_loss(df_1m, 14, 2.0, direction.lower())
            if atr_stop:
                if direction == 'LONG' and current_price <= atr_stop:
                    result['should_stop'] = True
                    result['reason'] = f"Stop Loss ATR atingido: {atr_stop:.6f}"
                    return result
                elif direction == 'SHORT' and current_price >= atr_stop:
                    result['should_stop'] = True
                    result['reason'] = f"Stop Loss ATR atingido: {atr_stop:.6f}"
                    return result
            
            # 2. Stop Loss baseado na mínima/máxima do candle anterior
            prev_candle = df_1m.iloc[-2]
            if direction == 'LONG' and current_price <= prev_candle['low']:
                result['should_stop'] = True
                result['reason'] = f"Preço rompeu mínima do candle anterior: {prev_candle['low']:.6f}"
                return result
            elif direction == 'SHORT' and current_price >= prev_candle['high']:
                result['should_stop'] = True
                result['reason'] = f"Preço rompeu máxima do candle anterior: {prev_candle['high']:.6f}"
                return result
            
            # 3. Stop Loss baseado em cruzamento de EMAs
            if len(df_5m) >= 50:
                ema_20 = self.ta.calculate_ema(df_5m, 20)
                ema_50 = self.ta.calculate_ema(df_5m, 50)
                
                if not ema_20.empty and not ema_50.empty:
                    current_ema_20 = ema_20.iloc[-1]
                    current_ema_50 = ema_50.iloc[-1]
                    prev_ema_20 = ema_20.iloc[-2] if len(ema_20) >= 2 else current_ema_20
                    prev_ema_50 = ema_50.iloc[-2] if len(ema_50) >= 2 else current_ema_50
                    
                    # Verifica cruzamento contrário à posição
                    if direction == 'LONG':
                        if prev_ema_20 > prev_ema_50 and current_ema_20 < current_ema_50:
                            result['should_stop'] = True
                            result['reason'] = "Cruzamento bearish das EMAs (20 < 50)"
                            return result
                    elif direction == 'SHORT':
                        if prev_ema_20 < prev_ema_50 and current_ema_20 > current_ema_50:
                            result['should_stop'] = True
                            result['reason'] = "Cruzamento bullish das EMAs (20 > 50)"
                            return result
            
            # 4. Stop Loss baseado em RSI extremo reverso
            rsi = self.ta.calculate_rsi(df_1m, 14)
            if not rsi.empty:
                current_rsi = rsi.iloc[-1]
                
                if direction == 'LONG' and current_rsi < 20:  # RSI muito baixo em posição long
                    result['should_stop'] = True
                    result['reason'] = f"RSI extremamente baixo: {current_rsi:.1f}"
                    return result
                elif direction == 'SHORT' and current_rsi > 80:  # RSI muito alto em posição short
                    result['should_stop'] = True
                    result['reason'] = f"RSI extremamente alto: {current_rsi:.1f}"
                    return result
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao verificar stop loss dinâmico: {str(e)}")
            return {'should_stop': False, 'reason': None}
    
    def _check_trend_reversal(self, position_data: Dict, df_1m: pd.DataFrame, df_5m: pd.DataFrame) -> Dict:
        """
        Verifica sinais de reversão de tendência
        
        Args:
            position_data: Dados da posição
            df_1m: Dados de 1 minuto
            df_5m: Dados de 5 minutos
        
        Returns:
            Dicionário com resultado da verificação
        """
        try:
            result = {'should_exit': False, 'reason': None, 'signals': {}}
            
            direction = position_data.get('direction', '').upper()
            
            # Análise técnica completa
            analysis_1m = self.ta.get_comprehensive_analysis(df_1m)
            analysis_5m = self.ta.get_comprehensive_analysis(df_5m)
            
            reversal_signals = 0
            signals_detected = []
            
            # 1. Divergência de OBV
            if analysis_1m.get('obv_trend'):
                if direction == 'LONG' and analysis_1m['obv_trend'] == 'falling':
                    reversal_signals += 1
                    signals_detected.append("OBV divergente (falling)")
                elif direction == 'SHORT' and analysis_1m['obv_trend'] == 'rising':
                    reversal_signals += 1
                    signals_detected.append("OBV divergente (rising)")
            
            # 2. Padrões de reversão
            patterns = analysis_1m.get('candlestick_patterns', {})
            if direction == 'LONG':
                bearish_patterns = ['inverted_hammer', 'bearish_engulfing', 'bearish_pinbar']
                for pattern in bearish_patterns:
                    if patterns.get(pattern):
                        reversal_signals += 1
                        signals_detected.append(f"Padrão bearish: {pattern}")
                        break
            elif direction == 'SHORT':
                bullish_patterns = ['hammer', 'bullish_engulfing', 'bullish_pinbar']
                for pattern in bullish_patterns:
                    if patterns.get(pattern):
                        reversal_signals += 1
                        signals_detected.append(f"Padrão bullish: {pattern}")
                        break
            
            # 3. RSI em zona extrema oposta
            rsi_14 = analysis_1m.get('rsi_14')
            if rsi_14:
                if direction == 'LONG' and rsi_14 > 75:
                    reversal_signals += 1
                    signals_detected.append(f"RSI sobrecomprado: {rsi_14:.1f}")
                elif direction == 'SHORT' and rsi_14 < 25:
                    reversal_signals += 1
                    signals_detected.append(f"RSI sobrevendido: {rsi_14:.1f}")
            
            # 4. Mudança de tendência no timeframe maior
            trend_5m = analysis_5m.get('trend')
            if trend_5m:
                if direction == 'LONG' and trend_5m == 'bearish':
                    reversal_signals += 1
                    signals_detected.append("Tendência 5m bearish")
                elif direction == 'SHORT' and trend_5m == 'bullish':
                    reversal_signals += 1
                    signals_detected.append("Tendência 5m bullish")
            
            # Decide se deve sair baseado no número de sinais
            if reversal_signals >= 2:  # Pelo menos 2 sinais de reversão
                result['should_exit'] = True
                result['reason'] = f"Sinais de reversão detectados: {', '.join(signals_detected)}"
                result['signals'] = {
                    'count': reversal_signals,
                    'signals': signals_detected
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao verificar reversão de tendência: {str(e)}")
            return {'should_exit': False, 'reason': None, 'signals': {}}
    
    def _check_trailing_stop(self, position_data: Dict, df_1m: pd.DataFrame) -> Dict:
        """
        Verifica trailing stop baseado em máximas/mínimas favoráveis
        
        Args:
            position_data: Dados da posição
            df_1m: Dados de 1 minuto
        
        Returns:
            Dicionário com resultado da verificação
        """
        try:
            result = {'should_stop': False, 'reason': None}
            
            direction = position_data.get('direction', '').upper()
            entry_price = position_data.get('entry_price', 0)
            current_price = df_1m['close'].iloc[-1]
            
            # Calcula profit atual
            if direction == 'LONG':
                profit_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                profit_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Só ativa trailing stop se já estiver em lucro
            if profit_pct <= 1:  # Menos de 1% de lucro
                return result
            
            # Calcula trailing stop baseado nas últimas 10 velas
            lookback_period = min(10, len(df_1m))
            recent_data = df_1m.tail(lookback_period)
            
            if direction == 'LONG':
                # Para LONG, trailing stop na mínima recente
                trailing_level = recent_data['low'].max() * 0.995  # 0.5% abaixo da máxima das mínimas
                if current_price <= trailing_level:
                    result['should_stop'] = True
                    result['reason'] = f"Trailing stop ativado: {trailing_level:.6f}"
            
            elif direction == 'SHORT':
                # Para SHORT, trailing stop na máxima recente
                trailing_level = recent_data['high'].min() * 1.005  # 0.5% acima da mínima das máximas
                if current_price >= trailing_level:
                    result['should_stop'] = True
                    result['reason'] = f"Trailing stop ativado: {trailing_level:.6f}"
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao verificar trailing stop: {str(e)}")
            return {'should_stop': False, 'reason': None}
    
    def format_exit_alert(self, symbol: str, position_data: Dict, exit_analysis: Dict) -> str:
        """
        Formata alerta de saída para Telegram
        
        Args:
            symbol: Símbolo do par
            position_data: Dados da posição
            exit_analysis: Análise de saída
        
        Returns:
            Mensagem formatada
        """
        try:
            if not exit_analysis.get('should_exit'):
                return ""
            
            direction = position_data.get('direction', '').upper()
            entry_price = position_data.get('entry_price', 0)
            current_price = exit_analysis.get('suggested_exit_price', 0)
            profit_loss = exit_analysis.get('profit_loss_pct', 0)
            exit_type = exit_analysis.get('exit_type', '')
            exit_reason = exit_analysis.get('exit_reason', '')
            
            # Emoji baseado no tipo de saída
            emoji_map = {
                'take_profit': '🎯',
                'stop_loss': '🛡️',
                'trailing_stop': '📈',
                'reversal': '🔄'
            }
            
            emoji = emoji_map.get(exit_type, '🚪')
            profit_emoji = '💚' if profit_loss > 0 else '❌'
            
            message = f"""
{emoji} <b>SINAL DE SAÍDA DETECTADO</b> {emoji}

💰 <b>Par:</b> {symbol}
📈 <b>Direção:</b> {direction}
💵 <b>Preço de Entrada:</b> ${entry_price:.6f}
💵 <b>Preço Atual:</b> ${current_price:.6f}
{profit_emoji} <b>P&L:</b> {profit_loss:+.2f}%

🚪 <b>Tipo de Saída:</b> {exit_type.replace('_', ' ').title()}
📋 <b>Motivo:</b> {exit_reason}

⏰ <b>Horário:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
            """.strip()
            
            return message
            
        except Exception as e:
            logger.error(f"Erro ao formatar alerta de saída: {str(e)}")
            return ""
    
    def update_position_cache(self, symbol: str, position_data: Dict):
        """
        Atualiza cache de posições ativas
        
        Args:
            symbol: Símbolo do par
            position_data: Dados da posição
        """
        try:
            self.active_positions[symbol] = {
                **position_data,
                'last_update': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao atualizar cache de posição: {str(e)}")
    
    def remove_position_from_cache(self, symbol: str):
        """
        Remove posição do cache
        
        Args:
            symbol: Símbolo do par
        """
        try:
            if symbol in self.active_positions:
                del self.active_positions[symbol]
        except Exception as e:
            logger.error(f"Erro ao remover posição do cache: {str(e)}")
    
    def get_active_positions(self) -> Dict:
        """
        Retorna posições ativas do cache
        
        Returns:
            Dicionário com posições ativas
        """
        return self.active_positions.copy()

