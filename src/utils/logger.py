import logging
import os
from datetime import datetime
from config.config import Config

class TradingLogger:
    """Sistema de logging para o bot de trading"""
    
    def __init__(self, name: str = 'TradingBot'):
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self):
        """Configura o sistema de logging"""
        # Remove handlers existentes para evitar duplicação
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Define o nível de log
        level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Cria o diretório de logs se não existir
        log_dir = os.path.dirname(Config.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Formato das mensagens de log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para arquivo
        if Config.LOG_FILE:
            file_handler = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log de informação"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log de aviso"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log de erro"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log de debug"""
        self.logger.debug(message)
    
    def critical(self, message: str):
        """Log crítico"""
        self.logger.critical(message)
    
    def log_signal(self, symbol: str, direction: str, price: float, reason: str):
        """Log específico para sinais de trading"""
        message = f"SIGNAL - {symbol} {direction} @ {price} - Reason: {reason}"
        self.info(message)
    
    def log_error_with_context(self, error: Exception, context: str):
        """Log de erro com contexto adicional"""
        message = f"ERROR in {context}: {str(error)}"
        self.error(message)
    
    def log_api_call(self, endpoint: str, status_code: int, response_time: float):
        """Log para chamadas de API"""
        message = f"API Call - {endpoint} - Status: {status_code} - Time: {response_time:.2f}s"
        self.debug(message)

# Instância global do logger
logger = TradingLogger()

