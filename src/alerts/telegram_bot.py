import asyncio
import aiohttp
from typing import Optional, Dict, List
from datetime import datetime, timezone
from config.config import Config, AlertMessages
from src.utils.logger import logger

class TelegramBot:
    """Bot para envio de alertas via Telegram"""
    
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or Config.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or Config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        # Controle de rate limiting
        self.last_message_time = 0
        self.min_message_interval = 1.0  # 1 segundo entre mensagens
        
        # Cache de mensagens para evitar spam
        self.message_cache = {}
        self.cache_duration = 300  # 5 minutos
    
    async def send_message(self, text: str, parse_mode: str = 'HTML', disable_notification: bool = False) -> bool:
        """
        Envia mensagem via Telegram
        
        Args:
            text: Texto da mensagem
            parse_mode: Modo de parsing (HTML ou Markdown)
            disable_notification: Se deve desabilitar notificação
        
        Returns:
            True se enviado com sucesso
        """
        try:
            if not self.token or not self.chat_id:
                logger.error("Token do Telegram ou Chat ID não configurados")
                return False
            
            # Verifica cache para evitar mensagens duplicadas
            message_hash = hash(text)
            current_time = datetime.now().timestamp()
            
            if message_hash in self.message_cache:
                last_sent = self.message_cache[message_hash]
                if current_time - last_sent < self.cache_duration:
                    logger.debug("Mensagem duplicada ignorada (cache)")
                    return True
            
            # Rate limiting
            await self._wait_for_rate_limit()
            
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_notification': disable_notification
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        # Atualiza cache
                        self.message_cache[message_hash] = current_time
                        logger.info("Mensagem enviada via Telegram com sucesso")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Erro ao enviar mensagem via Telegram: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem via Telegram: {str(e)}")
            return False
    
    async def _wait_for_rate_limit(self):
        """Implementa rate limiting para mensagens"""
        current_time = datetime.now().timestamp()
        time_since_last = current_time - self.last_message_time
        
        if time_since_last < self.min_message_interval:
            sleep_time = self.min_message_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_message_time = datetime.now().timestamp()
    
    async def send_signal_alert(self, symbol: str, signal_data: Dict, position_size: float) -> bool:
        """
        Envia alerta de sinal de trading
        
        Args:
            symbol: Símbolo do par
            signal_data: Dados do sinal
            position_size: Tamanho da posição
        
        Returns:
            True se enviado com sucesso
        """
        try:
            if not signal_data.get('has_signal'):
                return False
            
            # Formata níveis de Fibonacci
            fib_levels = signal_data.get('fibonacci_levels', {})
            tp1 = fib_levels.get('TP1', 0)
            tp2 = fib_levels.get('TP2', 0)
            tp3 = fib_levels.get('TP3', 0)
            
            # Formata razões do sinal
            reasons = "\n".join([f"• {reason}" for reason in signal_data.get('reasons', [])])
            
            # Determina emoji da direção
            direction_emoji = "🟢" if signal_data['direction'] == 'LONG' else "🔴"
            
            message = f"""
{direction_emoji} <b>SINAL DE ENTRADA DETECTADO</b> {direction_emoji}

💰 <b>Par:</b> {symbol}
📈 <b>Direção:</b> {signal_data['direction']}
💵 <b>Preço Atual:</b> ${signal_data['price']:.6f}
📊 <b>RSI 7:</b> {signal_data['rsi_7']:.1f} | <b>RSI 14:</b> {signal_data['rsi_14']:.1f}
📊 <b>Volume Spike:</b> {'✅' if signal_data['volume_spike'] else '❌'}

🎯 <b>Alvos Fibonacci:</b>
• TP1 (38.2%): ${tp1:.6f}
• TP2 (61.8%): ${tp2:.6f}
• TP3 (100%): ${tp3:.6f}

🛡️ <b>Stop Loss Sugerido:</b> ${signal_data['stop_loss']:.6f}

⚡ <b>Alavancagem:</b> {Config.LEVERAGE}x
💰 <b>Tamanho da Posição:</b> ${position_size:.2f} USDT
⭐ <b>Força do Sinal:</b> {signal_data['strength']}/7

📊 <b>Motivos do Sinal:</b>
{reasons}

⏰ <b>Horário:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
            """.strip()
            
            return await self.send_message(message)
            
        except Exception as e:
            logger.error(f"Erro ao enviar alerta de sinal: {str(e)}")
            return False
    
    async def send_error_alert(self, error_message: str, location: str = "") -> bool:
        """
        Envia alerta de erro
        
        Args:
            error_message: Mensagem de erro
            location: Localização do erro
        
        Returns:
            True se enviado com sucesso
        """
        try:
            message = f"""
❌ <b>ERRO NO BOT DE TRADING</b>

🔍 <b>Erro:</b> {error_message}
📍 <b>Localização:</b> {location}
⏰ <b>Horário:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
            """.strip()
            
            return await self.send_message(message, disable_notification=True)
            
        except Exception as e:
            logger.error(f"Erro ao enviar alerta de erro: {str(e)}")
            return False
    
    async def send_status_update(self, status_data: Dict) -> bool:
        """
        Envia atualização de status do bot
        
        Args:
            status_data: Dados do status
        
        Returns:
            True se enviado com sucesso
        """
        try:
            message = f"""
📊 <b>STATUS DO BOT</b>

✅ <b>Status:</b> {status_data.get('status', 'Desconhecido')}
🔄 <b>Última Análise:</b> {status_data.get('last_analysis', 'N/A')}
📈 <b>Sinais Enviados Hoje:</b> {status_data.get('signals_today', 0)}
💰 <b>Pares Monitorados:</b> {status_data.get('monitored_pairs', 0)}
⏰ <b>Próxima Análise:</b> {status_data.get('next_analysis', 'N/A')}
            """.strip()
            
            return await self.send_message(message, disable_notification=True)
            
        except Exception as e:
            logger.error(f"Erro ao enviar status: {str(e)}")
            return False
    
    async def send_daily_summary(self, summary_data: Dict) -> bool:
        """
        Envia resumo diário
        
        Args:
            summary_data: Dados do resumo
        
        Returns:
            True se enviado com sucesso
        """
        try:
            message = f"""
📈 <b>RESUMO DIÁRIO</b>

📊 <b>Sinais Enviados:</b> {summary_data.get('total_signals', 0)}
🟢 <b>Sinais LONG:</b> {summary_data.get('long_signals', 0)}
🔴 <b>Sinais SHORT:</b> {summary_data.get('short_signals', 0)}
⭐ <b>Força Média:</b> {summary_data.get('avg_strength', 0):.1f}/7
💰 <b>Pares Mais Ativos:</b> {', '.join(summary_data.get('top_pairs', []))}

📅 <b>Data:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
            """.strip()
            
            return await self.send_message(message, disable_notification=True)
            
        except Exception as e:
            logger.error(f"Erro ao enviar resumo diário: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Testa conexão com o Telegram
        
        Returns:
            True se conexão estiver funcionando
        """
        try:
            test_message = f"""
🤖 <b>TESTE DE CONEXÃO</b>

✅ Bot de Trading conectado com sucesso!
⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
            """.strip()
            
            return await self.send_message(test_message, disable_notification=True)
            
        except Exception as e:
            logger.error(f"Erro no teste de conexão: {str(e)}")
            return False
    
    def clear_message_cache(self):
        """Limpa o cache de mensagens"""
        try:
            current_time = datetime.now().timestamp()
            expired_messages = []
            
            for message_hash, sent_time in self.message_cache.items():
                if current_time - sent_time > self.cache_duration:
                    expired_messages.append(message_hash)
            
            for message_hash in expired_messages:
                del self.message_cache[message_hash]
                
            logger.debug(f"Cache limpo: {len(expired_messages)} mensagens removidas")
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")

# Função auxiliar para uso síncrono
def send_telegram_message(text: str, token: str = None, chat_id: str = None) -> bool:
    """
    Função auxiliar para envio síncrono de mensagens
    
    Args:
        text: Texto da mensagem
        token: Token do bot (opcional)
        chat_id: ID do chat (opcional)
    
    Returns:
        True se enviado com sucesso
    """
    try:
        bot = TelegramBot(token, chat_id)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bot.send_message(text))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Erro no envio síncrono: {str(e)}")
        return False

