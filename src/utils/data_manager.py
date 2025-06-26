import os
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import time
from config.config import Config, TradingPairs
from src.api.mexc_client import MEXCClient
from src.utils.logger import logger

class DataManager:
    """Gerenciador de dados de mercado e cache"""
    
    def __init__(self):
        self.mexc_client = MEXCClient()
        self.data_folder = Config.DATA_FOLDER
        self.cache_duration = 60  # Cache de 1 minuto para dados de mercado
        
        # Cria pasta de dados se não existir
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
    
    def get_market_data(self, symbol: str, interval: str, limit: int = 100, use_cache: bool = True) -> pd.DataFrame:
        """
        Obtém dados de mercado com cache
        
        Args:
            symbol: Símbolo do par
            interval: Intervalo (Min1, Min5, etc.)
            limit: Número de candles
            use_cache: Se deve usar cache
        
        Returns:
            DataFrame com dados OHLCV
        """
        try:
            cache_key = f"{symbol}_{interval}_{limit}"
            
            # Verifica cache se habilitado
            if use_cache:
                cached_data = self._get_cached_data(cache_key)
                if cached_data is not None:
                    return cached_data
            
            # Busca dados da API
            logger.debug(f"Buscando dados da API: {symbol} {interval}")
            
            # Calcula timestamps para buscar dados históricos
            end_time = int(time.time() * 1000)
            
            # Converte intervalo para segundos
            interval_seconds = self._interval_to_seconds(interval)
            start_time = end_time - (limit * interval_seconds * 1000)
            
            klines = self.mexc_client.get_klines(symbol, interval, start_time, end_time)
            
            if not klines:
                logger.warning(f"Nenhum dado retornado para {symbol} {interval}")
                return pd.DataFrame()
            
            # Converte para DataFrame
            df = self.mexc_client.klines_to_dataframe(klines)
            
            # Salva no cache
            if use_cache and not df.empty:
                self._save_to_cache(cache_key, df)
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao obter dados de mercado para {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_multiple_timeframes(self, symbol: str, intervals: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Obtém dados de múltiplos timeframes
        
        Args:
            symbol: Símbolo do par
            intervals: Lista de intervalos
        
        Returns:
            Dicionário com DataFrames por intervalo
        """
        try:
            intervals = intervals or Config.CANDLE_INTERVALS
            data = {}
            
            for interval in intervals:
                df = self.get_market_data(symbol, interval)
                if not df.empty:
                    data[interval] = df
                else:
                    logger.warning(f"Dados vazios para {symbol} {interval}")
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao obter múltiplos timeframes para {symbol}: {str(e)}")
            return {}
    
    def get_all_usdt_pairs(self, use_cache: bool = True) -> List[str]:
        """
        Obtém lista de todos os pares USDT
        
        Args:
            use_cache: Se deve usar cache
        
        Returns:
            Lista de pares USDT
        """
        try:
            cache_key = "usdt_pairs"
            
            # Verifica cache
            if use_cache:
                cached_pairs = self._get_cached_data(cache_key, cache_duration=3600)  # Cache de 1 hora
                if cached_pairs is not None:
                    return cached_pairs
            
            # Busca da API
            pairs = self.mexc_client.get_all_usdt_pairs()
            
            # Remove pares excluídos
            filtered_pairs = [pair for pair in pairs if pair not in TradingPairs.EXCLUDED_PAIRS]
            
            # Salva no cache
            if use_cache and filtered_pairs:
                self._save_to_cache(cache_key, filtered_pairs, cache_duration=3600)
            
            return filtered_pairs
            
        except Exception as e:
            logger.error(f"Erro ao obter pares USDT: {str(e)}")
            return TradingPairs.USDT_PAIRS  # Fallback para lista padrão
    
    def get_volume_analysis(self, symbol: str, days: int = 7) -> Dict:
        """
        Analisa volume médio por hora nos últimos dias
        
        Args:
            symbol: Símbolo do par
            days: Número de dias para análise
        
        Returns:
            Dicionário com análise de volume
        """
        try:
            # Busca dados de 1 hora para análise de volume
            end_time = int(time.time() * 1000)
            start_time = end_time - (days * 24 * 60 * 60 * 1000)  # X dias atrás
            
            klines = self.mexc_client.get_klines(symbol, 'Hour1', start_time, end_time)
            
            if not klines:
                return {'avg_volume': 0, 'volume_by_hour': {}}
            
            df = self.mexc_client.klines_to_dataframe(klines)
            
            # Calcula volume médio
            avg_volume = df['volume'].mean()
            
            # Analisa volume por hora do dia
            df['hour'] = df.index.hour
            volume_by_hour = df.groupby('hour')['volume'].mean().to_dict()
            
            return {
                'avg_volume': avg_volume,
                'volume_by_hour': volume_by_hour,
                'total_candles': len(df)
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de volume para {symbol}: {str(e)}")
            return {'avg_volume': 0, 'volume_by_hour': {}}
    
    def _get_cached_data(self, cache_key: str, cache_duration: int = None) -> Optional[any]:
        """
        Obtém dados do cache
        
        Args:
            cache_key: Chave do cache
            cache_duration: Duração do cache em segundos
        
        Returns:
            Dados do cache ou None
        """
        try:
            cache_duration = cache_duration or self.cache_duration
            cache_file = os.path.join(self.data_folder, f"{cache_key}.json")
            
            if not os.path.exists(cache_file):
                return None
            
            # Verifica se o cache ainda é válido
            file_time = os.path.getmtime(cache_file)
            current_time = time.time()
            
            if current_time - file_time > cache_duration:
                # Cache expirado, remove o arquivo
                os.remove(cache_file)
                return None
            
            # Lê dados do cache
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Se for DataFrame, reconstrói
            if cache_data.get('type') == 'dataframe':
                df = pd.DataFrame(cache_data['data'])
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                return df
            else:
                return cache_data.get('data')
                
        except Exception as e:
            logger.debug(f"Erro ao ler cache {cache_key}: {str(e)}")
            return None
    
    def _save_to_cache(self, cache_key: str, data: any, cache_duration: int = None):
        """
        Salva dados no cache
        
        Args:
            cache_key: Chave do cache
            data: Dados para salvar
            cache_duration: Duração do cache (não usado, apenas para compatibilidade)
        """
        try:
            cache_file = os.path.join(self.data_folder, f"{cache_key}.json")
            
            # Prepara dados para serialização
            if isinstance(data, pd.DataFrame):
                # Para DataFrame, salva como dict
                df_copy = data.copy()
                if df_copy.index.name == 'timestamp':
                    df_copy.reset_index(inplace=True)
                    df_copy['timestamp'] = df_copy['timestamp'].astype(str)
                
                cache_data = {
                    'type': 'dataframe',
                    'data': df_copy.to_dict('records'),
                    'timestamp': time.time()
                }
            else:
                # Para outros tipos
                cache_data = {
                    'type': 'data',
                    'data': data,
                    'timestamp': time.time()
                }
            
            # Salva no arquivo
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            logger.debug(f"Erro ao salvar cache {cache_key}: {str(e)}")
    
    def _interval_to_seconds(self, interval: str) -> int:
        """
        Converte intervalo para segundos
        
        Args:
            interval: Intervalo (Min1, Min5, Hour1, etc.)
        
        Returns:
            Segundos correspondentes
        """
        interval_map = {
            'Min1': 60,
            'Min5': 300,
            'Min15': 900,
            'Min30': 1800,
            'Min60': 3600,
            'Hour1': 3600,
            'Hour4': 14400,
            'Hour8': 28800,
            'Day1': 86400,
            'Week1': 604800,
            'Month1': 2592000
        }
        
        return interval_map.get(interval, 60)
    
    def clear_cache(self, older_than_hours: int = 24):
        """
        Limpa cache antigo
        
        Args:
            older_than_hours: Remove arquivos mais antigos que X horas
        """
        try:
            current_time = time.time()
            cutoff_time = current_time - (older_than_hours * 3600)
            
            removed_count = 0
            
            for filename in os.listdir(self.data_folder):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.data_folder, filename)
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        removed_count += 1
            
            logger.info(f"Cache limpo: {removed_count} arquivos removidos")
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
    
    def get_market_summary(self, symbols: List[str]) -> Dict:
        """
        Obtém resumo do mercado para múltiplos símbolos
        
        Args:
            symbols: Lista de símbolos
        
        Returns:
            Dicionário com resumo do mercado
        """
        try:
            summary = {
                'total_pairs': len(symbols),
                'active_pairs': 0,
                'avg_volume': 0,
                'top_volume_pairs': [],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            volumes = {}
            
            for symbol in symbols[:20]:  # Limita a 20 pares para não sobrecarregar
                try:
                    ticker = self.mexc_client.get_ticker(symbol)
                    if ticker and 'data' in ticker:
                        volume = float(ticker['data'].get('volume24', 0))
                        if volume > 0:
                            volumes[symbol] = volume
                            summary['active_pairs'] += 1
                except:
                    continue
            
            if volumes:
                summary['avg_volume'] = sum(volumes.values()) / len(volumes)
                summary['top_volume_pairs'] = sorted(volumes.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo do mercado: {str(e)}")
            return {'total_pairs': 0, 'active_pairs': 0, 'avg_volume': 0, 'top_volume_pairs': []}

