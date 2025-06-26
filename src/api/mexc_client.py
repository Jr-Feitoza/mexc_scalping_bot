import requests
import time
from typing import Dict, List, Optional, Union
import pandas as pd
from config.config import Config
from src.utils.helpers import generate_signature, get_current_timestamp
from src.utils.logger import logger

class MEXCClient:
    """Cliente para interação com a API da MEXC"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key or Config.MEXC_API_KEY
        self.secret_key = secret_key or Config.MEXC_SECRET_KEY
        self.base_url = Config.MEXC_BASE_URL
        self.session = requests.Session()
        
        # Headers padrão
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MEXC-Scalping-Bot/1.0'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0 / Config.API_RATE_LIMIT  # 20 requests per 2 seconds
    
    def _wait_for_rate_limit(self):
        """Implementa rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """
        Faz requisição para a API da MEXC
        
        Args:
            method: Método HTTP (GET, POST, DELETE)
            endpoint: Endpoint da API
            params: Parâmetros da requisição
            signed: Se a requisição precisa de assinatura
        
        Returns:
            Resposta da API
        """
        self._wait_for_rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        # Adiciona autenticação se necessário
        if signed:
            timestamp = get_current_timestamp()
            
            # Prepara parâmetros para assinatura
            if method.upper() == 'GET':
                param_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
            else:
                param_string = str(params) if params else ""
            
            # Gera assinatura
            signature = generate_signature(self.secret_key, self.api_key, timestamp, param_string)
            
            # Adiciona headers de autenticação
            headers = {
                'ApiKey': self.api_key,
                'Request-Time': timestamp,
                'Signature': signature
            }
            self.session.headers.update(headers)
        
        try:
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=params)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response_time = time.time() - start_time
            logger.log_api_call(endpoint, response.status_code, response_time)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {endpoint}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado na requisição para {endpoint}: {str(e)}")
            raise
    
    # Métodos públicos (não requerem autenticação)
    
    def ping(self) -> Dict:
        """Testa conectividade com a API"""
        return self._make_request('GET', 'api/v1/contract/ping')
    
    def get_contract_details(self, symbol: str = None) -> Dict:
        """
        Obtém detalhes dos contratos
        
        Args:
            symbol: Símbolo do contrato (opcional)
        
        Returns:
            Detalhes dos contratos
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request('GET', 'api/v1/contract/detail', params)
    
    def get_klines(self, symbol: str, interval: str, start: int = None, end: int = None) -> List[List]:
        """
        Obtém dados de candlesticks
        
        Args:
            symbol: Símbolo do par
            interval: Intervalo (Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1)
            start: Timestamp de início (opcional)
            end: Timestamp de fim (opcional)
        
        Returns:
            Lista de candlesticks
        """
        params = {
            'symbol': symbol,
            'interval': interval
        }
        
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        
        response = self._make_request('GET', 'api/v1/contract/kline', params)
        return response.get('data', [])
    
    def get_ticker(self, symbol: str = None) -> Dict:
        """
        Obtém dados de ticker
        
        Args:
            symbol: Símbolo do par (opcional)
        
        Returns:
            Dados do ticker
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request('GET', 'api/v1/contract/ticker', params)
    
    def get_depth(self, symbol: str, limit: int = 100) -> Dict:
        """
        Obtém book de ofertas
        
        Args:
            symbol: Símbolo do par
            limit: Número de níveis (máximo 100)
        
        Returns:
            Book de ofertas
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        return self._make_request('GET', 'api/v1/contract/depth', params)
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> Dict:
        """
        Obtém negociações recentes
        
        Args:
            symbol: Símbolo do par
            limit: Número de negociações (máximo 100)
        
        Returns:
            Negociações recentes
        """
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        return self._make_request('GET', 'api/v1/contract/deals', params)
    
    # Métodos privados (requerem autenticação)
    
    def get_account_assets(self) -> Dict:
        """
        Obtém informações dos ativos da conta
        
        Returns:
            Informações dos ativos
        """
        return self._make_request('GET', 'api/v1/private/account/assets', signed=True)
    
    def get_asset_info(self, currency: str) -> Dict:
        """
        Obtém informações de um ativo específico
        
        Args:
            currency: Moeda (ex: USDT)
        
        Returns:
            Informações do ativo
        """
        return self._make_request('GET', f'api/v1/private/account/asset/{currency}', signed=True)
    
    def get_positions(self, symbol: str = None) -> Dict:
        """
        Obtém posições atuais
        
        Args:
            symbol: Símbolo do par (opcional)
        
        Returns:
            Posições atuais
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request('GET', 'api/v1/private/position/open_positions', params, signed=True)
    
    def get_open_orders(self, symbol: str = None) -> Dict:
        """
        Obtém ordens abertas
        
        Args:
            symbol: Símbolo do par (opcional)
        
        Returns:
            Ordens abertas
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._make_request('GET', 'api/v1/private/order/list/open_orders', params, signed=True)
    
    # Métodos auxiliares para conversão de dados
    
    def klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """
        Converte dados de klines para DataFrame
        
        Args:
            klines: Lista de klines da API
        
        Returns:
            DataFrame com dados OHLCV
        """
        if not klines:
            return pd.DataFrame()
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume'
        ])
        
        # Converte tipos de dados
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        # Define timestamp como índice
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def get_all_usdt_pairs(self) -> List[str]:
        """
        Obtém todos os pares USDT disponíveis
        
        Returns:
            Lista de pares USDT
        """
        try:
            contracts = self.get_contract_details()
            usdt_pairs = []
            
            if 'data' in contracts:
                for contract in contracts['data']:
                    symbol = contract.get('symbol', '')
                    if symbol.endswith('_USDT') and contract.get('apiAllowed', False):
                        usdt_pairs.append(symbol)
            
            return sorted(usdt_pairs)
            
        except Exception as e:
            logger.error(f"Erro ao obter pares USDT: {str(e)}")
            return []

