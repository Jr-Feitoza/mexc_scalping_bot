# Guia de Instalação - MEXC Scalping Bot

## 📋 Pré-requisitos

### Sistema Operacional
- **Linux**: Ubuntu 18.04+ (recomendado)
- **Windows**: Windows 10+ com WSL2
- **macOS**: macOS 10.15+

### Software Necessário
- **Python**: 3.8 ou superior
- **pip**: Gerenciador de pacotes Python
- **git**: Para clonar o repositório

### Contas Necessárias
- **Conta MEXC**: Com API habilitada
- **Bot Telegram**: Token do BotFather
- **Chat Telegram**: ID do chat para receber alertas

## 🔧 Instalação Passo a Passo

### 1. Preparação do Ambiente

#### Linux/macOS
```bash
# Atualiza o sistema
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# ou
brew update && brew upgrade  # macOS

# Instala Python e pip (se necessário)
sudo apt install python3 python3-pip git -y  # Ubuntu/Debian
# ou
brew install python3 git  # macOS

# Verifica versões
python3 --version
pip3 --version
```

#### Windows (WSL2)
```powershell
# Instala WSL2 (se necessário)
wsl --install

# No terminal WSL:
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip git -y
```

### 2. Download do Projeto

```bash
# Clone o repositório
git clone <repository-url>
cd mexc_scalping_bot

# Ou baixe e extraia o arquivo ZIP
wget <download-url>
unzip mexc_scalping_bot.zip
cd mexc_scalping_bot
```

### 3. Configuração do Ambiente Virtual

```bash
# Cria ambiente virtual
python3 -m venv venv

# Ativa o ambiente virtual
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Verifica se está ativo (deve mostrar (venv) no prompt)
which python
```

### 4. Instalação das Dependências

```bash
# Instala dependências
pip install -r requirements.txt

# Verifica instalação
pip list
```

### 5. Configuração das Credenciais

#### 5.1 Crie o arquivo .env
```bash
# Copia o arquivo de exemplo
cp .env.example .env

# Edita o arquivo
nano .env  # ou vim, code, etc.
```

#### 5.2 Configure as variáveis
```env
# API MEXC
MEXC_API_KEY=sua_chave_api_mexc_aqui
MEXC_SECRET_KEY=sua_chave_secreta_mexc_aqui

# Telegram
TELEGRAM_BOT_TOKEN=seu_token_telegram_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# Opcional
LOG_LEVEL=INFO
DEBUG_MODE=False
```

## 🔑 Configuração das APIs

### MEXC API

1. **Acesse sua conta MEXC**
   - Faça login em [mexc.com](https://mexc.com)
   - Vá para "API Management"

2. **Crie uma nova API Key**
   - Clique em "Create API Key"
   - Nome: "Scalping Bot"
   - Permissões: **Apenas leitura** (Read Only)
   - ⚠️ **Importante**: NÃO habilite permissões de trading

3. **Copie as credenciais**
   - API Key: Cole em `MEXC_API_KEY`
   - Secret Key: Cole em `MEXC_SECRET_KEY`

4. **Configure IP (opcional)**
   - Adicione o IP do seu servidor
   - Para uso local, pode deixar em branco

### Telegram Bot

1. **Crie um bot**
   - Abra o Telegram
   - Procure por `@BotFather`
   - Digite `/newbot`
   - Escolha um nome e username
   - Copie o token fornecido

2. **Obtenha seu Chat ID**
   - Procure por `@userinfobot`
   - Digite `/start`
   - Copie o ID fornecido

3. **Configure no .env**
   - Token: Cole em `TELEGRAM_BOT_TOKEN`
   - Chat ID: Cole em `TELEGRAM_CHAT_ID`

## ✅ Teste da Instalação

### 1. Teste Básico
```bash
# Ativa o ambiente virtual
source venv/bin/activate

# Testa importações
python3 -c "
import pandas as pd
import numpy as np
import ta
import requests
from telegram import Bot
print('✅ Todas as dependências instaladas com sucesso!')
"
```

### 2. Teste de Configuração
```bash
# Executa teste de configuração
python3 -c "
from config.config import Config
print(f'API Key configurada: {bool(Config.MEXC_API_KEY)}')
print(f'Telegram configurado: {bool(Config.TELEGRAM_BOT_TOKEN)}')
"
```

### 3. Teste de Conectividade
```bash
# Executa demonstração
python3 tests/test_demo.py
# Escolha opção 1 para demonstração completa
```

### 4. Teste dos Módulos
```bash
# Executa testes unitários
python3 tests/test_basic_functionality.py

# Executa testes de integração
python3 tests/test_integration.py
```

## 🚀 Primeira Execução

### 1. Execução em Modo Teste
```bash
# Ativa ambiente virtual
source venv/bin/activate

# Executa demonstração
echo "1" | python3 tests/test_demo.py
```

### 2. Execução Real (com APIs)
```bash
# Executa o bot principal
python3 main.py
```

### 3. Execução em Background
```bash
# Linux/macOS
nohup python3 main.py > logs/bot.log 2>&1 &

# Para parar
pkill -f "python3 main.py"
```

## 🔧 Configurações Avançadas

### Personalização de Pares
Edite `config/config.py`:
```python
class TradingPairs:
    USDT_PAIRS = [
        'BTC_USDT', 'ETH_USDT', 'BNB_USDT',
        # Adicione seus pares preferidos
    ]
```

### Ajuste de Parâmetros
```python
class Config:
    # Configurações de risco
    LEVERAGE = 7
    POSITION_SIZE_PERCENT = 1.0  # 1% da margem
    
    # RSI
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    # Volume
    VOLUME_SPIKE_MULTIPLIER = 2.0
```

### Horários Prioritários
```python
# Horários UTC para análise intensiva
PRIORITY_HOURS = [0, 6, 13]  # 00:00, 06:00, 13:00 UTC
```

## 🐳 Instalação com Docker (Opcional)

### 1. Crie o Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

### 2. Build e Execução
```bash
# Build da imagem
docker build -t mexc-scalping-bot .

# Execução
docker run -d \
  --name mexc-bot \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  mexc-scalping-bot
```

## 🔍 Solução de Problemas

### Erro: "Module not found"
```bash
# Verifica se está no ambiente virtual
which python
# Deve mostrar caminho com 'venv'

# Reinstala dependências
pip install -r requirements.txt --force-reinstall
```

### Erro: "API Key inválida"
```bash
# Verifica configuração
python3 -c "
from config.config import Config
print('API Key:', Config.MEXC_API_KEY[:10] + '...')
print('Secret Key:', Config.MEXC_SECRET_KEY[:10] + '...')
"
```

### Erro: "Telegram não responde"
```bash
# Testa token manualmente
curl -X GET "https://api.telegram.org/bot<SEU_TOKEN>/getMe"
```

### Erro: "Permission denied"
```bash
# Corrige permissões
chmod +x main.py
chmod -R 755 src/
```

### Problemas de Conectividade
```bash
# Testa conectividade
ping mexc.com
ping api.telegram.org

# Verifica firewall
sudo ufw status
```

## 📊 Monitoramento

### Logs
```bash
# Visualiza logs em tempo real
tail -f logs/trading_bot.log

# Busca por erros
grep "ERROR" logs/trading_bot.log

# Busca por sinais
grep "SIGNAL" logs/trading_bot.log
```

### Status do Bot
```bash
# Verifica se está rodando
ps aux | grep "python3 main.py"

# Verifica uso de recursos
top -p $(pgrep -f "python3 main.py")
```

## 🔄 Atualizações

### Atualização Manual
```bash
# Para o bot
pkill -f "python3 main.py"

# Atualiza código
git pull origin main

# Reinstala dependências (se necessário)
pip install -r requirements.txt --upgrade

# Reinicia
python3 main.py
```

### Backup de Configurações
```bash
# Backup das configurações
cp .env .env.backup
cp config/config.py config/config.py.backup

# Backup dos logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

## 📞 Suporte

### Verificação de Saúde
```bash
# Script de verificação completa
python3 -c "
import sys
import os
sys.path.append('.')

try:
    from config.config import Config
    from src.api.mexc_client import MEXCClient
    from src.alerts.telegram_bot import TelegramBot
    
    print('✅ Configurações carregadas')
    print('✅ Módulos importados')
    print('✅ Sistema funcionando')
except Exception as e:
    print(f'❌ Erro: {e}')
"
```

### Informações do Sistema
```bash
# Informações úteis para suporte
echo "Sistema: $(uname -a)"
echo "Python: $(python3 --version)"
echo "Pip: $(pip --version)"
echo "Diretório: $(pwd)"
echo "Usuário: $(whoami)"
```

---

**✅ Instalação Concluída!**

Após seguir este guia, seu bot estará pronto para uso. Lembre-se de:
- Manter as credenciais seguras
- Monitorar os logs regularmente
- Fazer backup das configurações
- Testar em ambiente controlado primeiro

Para dúvidas, consulte o README.md ou abra uma issue no repositório.

