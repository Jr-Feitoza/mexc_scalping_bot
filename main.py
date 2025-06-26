#!/usr/bin/env python3
"""
MEXC Scalping Bot - Sistema de Análise e Alertas de Trading

Este bot analisa oportunidades de scalping na MEXC e envia alertas via Telegram
para entrada manual nas posições.

Autor: Manus AI
Data: 2025-06-26
"""

import asyncio
import sys
import os
import signal
from datetime import datetime, timezone
from typing import Dict, List

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import Config, TradingPairs
from src.api.mexc_client import MEXCClient
from src.strategies.signal_generator import SignalGenerator
from src.alerts.telegram_bot import TelegramBot
from src.utils.data_manager import DataManager
from src.utils.logger import logger

class MEXCScalpingBot:
    """Bot principal de scalping para MEXC"""
    
    def __init__(self):
        self.mexc_client = MEXCClient()
        self.signal_generator = SignalGenerator()
        self.telegram_bot = TelegramBot()
        self.data_manager = DataManager()
        
        # Estado do bot
        self.is_running = False
        self.signals_sent_today = 0
        self.last_analysis_time = None
        self.monitored_pairs = []
        
        # Configuração de sinais
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de sistema"""
        logger.info(f"Sinal {signum} recebido. Parando o bot...")
        self.is_running = False
    
    async def initialize(self) -> bool:
        """
        Inicializa o bot e verifica configurações
        
        Returns:
            True se inicialização foi bem-sucedida
        """
        try:
            logger.info("Inicializando MEXC Scalping Bot...")
            
            # Verifica configurações essenciais
            if not Config.MEXC_API_KEY or not Config.MEXC_SECRET_KEY:
                logger.error("Chaves da API MEXC não configuradas")
                return False
            
            if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
                logger.error("Configurações do Telegram não encontradas")
                return False
            
            # Testa conexão com MEXC
            try:
                ping_result = self.mexc_client.ping()
                logger.info("Conexão com MEXC estabelecida")
            except Exception as e:
                logger.error(f"Erro ao conectar com MEXC: {str(e)}")
                return False
            
            # Testa conexão com Telegram
            telegram_test = await self.telegram_bot.test_connection()
            if not telegram_test:
                logger.error("Erro ao conectar com Telegram")
                return False
            
            # Obtém lista de pares para monitoramento
            self.monitored_pairs = self.data_manager.get_all_usdt_pairs()
            logger.info(f"Monitorando {len(self.monitored_pairs)} pares USDT")
            
            # Limpa cache antigo
            self.data_manager.clear_cache(older_than_hours=24)
            
            logger.info("Bot inicializado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro na inicialização: {str(e)}")
            return False
    
    async def analyze_market(self) -> List[Dict]:
        """
        Analisa o mercado em busca de oportunidades
        
        Returns:
            Lista de sinais encontrados
        """
        signals_found = []
        
        try:
            logger.info("Iniciando análise do mercado...")
            
            # Primeiro, analisa a tendência do BTC
            btc_data_1m = self.data_manager.get_market_data(TradingPairs.REFERENCE_PAIR, 'Min1', 100)
            btc_data_5m = self.data_manager.get_market_data(TradingPairs.REFERENCE_PAIR, 'Min5', 100)
            
            if btc_data_1m.empty or btc_data_5m.empty:
                logger.warning("Não foi possível obter dados do BTC")
                return signals_found
            
            btc_trend = self.signal_generator.analyze_btc_trend(btc_data_5m)
            logger.info(f"Tendência do BTC: {btc_trend}")
            
            # Analisa cada par monitorado
            analyzed_count = 0
            max_pairs_per_cycle = 20  # Limita para não sobrecarregar a API
            
            for symbol in self.monitored_pairs[:max_pairs_per_cycle]:
                try:
                    # Obtém dados de 1m e 5m
                    data_1m = self.data_manager.get_market_data(symbol, 'Min1', 100)
                    data_5m = self.data_manager.get_market_data(symbol, 'Min5', 100)
                    
                    if data_1m.empty or data_5m.empty:
                        continue
                    
                    # Verifica condições de entrada
                    signal = self.signal_generator.check_entry_conditions(data_1m, data_5m, btc_trend)
                    
                    if signal['has_signal'] and self.signal_generator.validate_signal_quality(signal):
                        signal['symbol'] = symbol
                        signals_found.append(signal)
                        logger.info(f"Sinal encontrado para {symbol}: {signal['direction']} (força: {signal['strength']})")
                    
                    analyzed_count += 1
                    
                    # Pequena pausa para não sobrecarregar a API
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.debug(f"Erro ao analisar {symbol}: {str(e)}")
                    continue
            
            self.last_analysis_time = datetime.now(timezone.utc)
            logger.info(f"Análise concluída: {analyzed_count} pares analisados, {len(signals_found)} sinais encontrados")
            
            return signals_found
            
        except Exception as e:
            logger.error(f"Erro na análise do mercado: {str(e)}")
            return signals_found
    
    async def send_signals(self, signals: List[Dict]) -> int:
        """
        Envia sinais via Telegram
        
        Args:
            signals: Lista de sinais para enviar
        
        Returns:
            Número de sinais enviados com sucesso
        """
        sent_count = 0
        
        try:
            for signal in signals:
                try:
                    symbol = signal['symbol']
                    
                    # Calcula tamanho da posição (simulado)
                    position_size = self.signal_generator.calculate_position_size(1000, signal['price'])  # Assume $1000 de margem
                    
                    # Envia alerta
                    success = await self.telegram_bot.send_signal_alert(symbol, signal, position_size)
                    
                    if success:
                        sent_count += 1
                        self.signals_sent_today += 1
                        logger.info(f"Sinal enviado para {symbol}")
                    else:
                        logger.warning(f"Falha ao enviar sinal para {symbol}")
                    
                    # Pausa entre envios
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar sinal: {str(e)}")
                    continue
            
            return sent_count
            
        except Exception as e:
            logger.error(f"Erro no envio de sinais: {str(e)}")
            return sent_count
    
    async def send_status_update(self):
        """Envia atualização de status"""
        try:
            status_data = {
                'status': 'Ativo' if self.is_running else 'Parado',
                'last_analysis': self.last_analysis_time.strftime('%H:%M:%S UTC') if self.last_analysis_time else 'N/A',
                'signals_today': self.signals_sent_today,
                'monitored_pairs': len(self.monitored_pairs),
                'next_analysis': 'Em 5 minutos'
            }
            
            await self.telegram_bot.send_status_update(status_data)
            
        except Exception as e:
            logger.error(f"Erro ao enviar status: {str(e)}")
    
    async def run_analysis_cycle(self):
        """Executa um ciclo completo de análise"""
        try:
            # Analisa mercado
            signals = await self.analyze_market()
            
            # Envia sinais encontrados
            if signals:
                sent_count = await self.send_signals(signals)
                logger.info(f"{sent_count} sinais enviados de {len(signals)} encontrados")
            
            # Limpa cache do Telegram
            self.telegram_bot.clear_message_cache()
            
        except Exception as e:
            logger.error(f"Erro no ciclo de análise: {str(e)}")
            await self.telegram_bot.send_error_alert(str(e), "Ciclo de análise")
    
    async def run(self):
        """Loop principal do bot"""
        try:
            # Inicializa o bot
            if not await self.initialize():
                logger.error("Falha na inicialização. Bot não será iniciado.")
                return
            
            self.is_running = True
            
            # Envia mensagem de início
            await self.telegram_bot.send_message("🤖 Bot de Scalping MEXC iniciado!")
            
            # Contadores para controle
            cycle_count = 0
            status_update_interval = 12  # Envia status a cada 12 ciclos (1 hora)
            
            logger.info("Bot iniciado. Pressione Ctrl+C para parar.")
            
            while self.is_running:
                try:
                    cycle_start_time = datetime.now(timezone.utc)
                    
                    # Executa análise
                    await self.run_analysis_cycle()
                    
                    cycle_count += 1
                    
                    # Envia status periodicamente
                    if cycle_count % status_update_interval == 0:
                        await self.send_status_update()
                    
                    # Calcula tempo de espera
                    cycle_duration = (datetime.now(timezone.utc) - cycle_start_time).total_seconds()
                    wait_time = max(300 - cycle_duration, 60)  # Mínimo 1 minuto, ideal 5 minutos
                    
                    logger.info(f"Ciclo {cycle_count} concluído em {cycle_duration:.1f}s. Próxima análise em {wait_time:.0f}s")
                    
                    # Espera até o próximo ciclo
                    await asyncio.sleep(wait_time)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Erro no loop principal: {str(e)}")
                    await self.telegram_bot.send_error_alert(str(e), "Loop principal")
                    await asyncio.sleep(60)  # Espera 1 minuto antes de tentar novamente
            
        except Exception as e:
            logger.critical(f"Erro crítico no bot: {str(e)}")
            await self.telegram_bot.send_error_alert(str(e), "Erro crítico")
        
        finally:
            self.is_running = False
            logger.info("Bot parado.")
            await self.telegram_bot.send_message("🛑 Bot de Scalping MEXC parado.")

async def main():
    """Função principal"""
    try:
        bot = MEXCScalpingBot()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário")
    except Exception as e:
        logger.critical(f"Erro fatal: {str(e)}")

if __name__ == "__main__":
    # Configura o loop de eventos
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Executa o bot
    asyncio.run(main())

