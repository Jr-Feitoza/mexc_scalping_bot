# MEXC Scalping Bot

Sistema automatizado de análise de oportunidades de scalping na exchange MEXC com alertas via Telegram.

## 📋 Características

- **Análise Técnica Completa**: RSI, EMA, OBV, ATR, Bandas de Bollinger, MACD
- **Detecção de Padrões**: Candlestick patterns (Hammer, Engulfing, Pinbar, etc.)
- **Análise de Volume**: Detecção de spikes de volume
- **Níveis de Fibonacci**: Cálculo automático de take profits
- **Stop Loss Dinâmico**: Baseado em ATR e análise técnica
- **Alertas via Telegram**: Notificações em tempo real
- **Análise de Tendência**: Usa BTC como referência de mercado
- **Gerenciamento de Risco**: Cálculo automático do tamanho da posição

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Conta na MEXC com API habilitada
- Bot do Telegram configurado

### 1. Clone o repositório

```bash
git clone <repository-url>
cd mexc_scalping_bot
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure suas credenciais:

```bash
cp .env.example .env
```

Edite o arquivo `.env`:

```env
# Configurações da API MEXC
MEXC_API_KEY=sua_chave_api_mexc
MEXC_SECRET_KEY=sua_chave_secreta_mexc

# Configurações do Telegram
TELEGRAM_BOT_TOKEN=token_do_seu_bot_telegram
TELEGRAM_CHAT_ID=id_do_chat_telegram
```

## 🔧 Configuração

### API MEXC

1. Acesse sua conta MEXC
2. Vá para "API Management"
3. Crie uma nova API Key com permissões de leitura
4. **Importante**: A API da MEXC não permite envio de ordens automáticas para usuários comuns

### Bot do Telegram

1. Crie um bot no Telegram através do @BotFather
2. Obtenha o token do bot
3. Obtenha seu Chat ID (pode usar @userinfobot)

## 🎯 Como Usar

### Execução Básica

```bash
python main.py
```

### Execução em Background (Linux/Mac)

```bash
nohup python main.py > logs/bot.log 2>&1 &
```

### Usando Docker (Opcional)

```bash
# Build da imagem
docker build -t mexc-scalping-bot .

# Execução
docker run -d --name mexc-bot --env-file .env mexc-scalping-bot
```

## 📊 Funcionalidades

### Análise Técnica

O bot analisa os seguintes indicadores:

- **RSI (7 e 14 períodos)**: Identifica condições de sobrecompra/sobrevenda
- **EMA (20 e 50 períodos)**: Determina tendência
- **OBV**: Analisa intenção de grandes players
- **Volume Spike**: Detecta aumentos significativos de volume
- **Padrões de Candlestick**: Hammer, Engulfing, Pinbar, etc.

### Geração de Sinais

O bot gera sinais baseado em:

1. **Tendência do BTC**: Usa BTC_USDT como referência de mercado
2. **Confluência de Indicadores**: Múltiplos indicadores devem confirmar
3. **Força do Sinal**: Score de 1-7 baseado no número de confirmações
4. **Horários Prioritários**: 00:00, 06:00 e 13:00 UTC

### Alertas via Telegram

Cada alerta contém:

- Par e direção da operação
- Preço atual e indicadores
- Níveis de take profit (Fibonacci)
- Stop loss sugerido
- Tamanho da posição recomendado
- Motivos do sinal

## ⚙️ Configurações Avançadas

### Arquivo `config/config.py`

```python
# Configurações de Trading
LEVERAGE = 7
POSITION_SIZE_PERCENT = 1.0  # 1% da margem
MIN_POSITION_SIZE_USDT = 1.0

# Configurações de RSI
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Configurações de Volume
VOLUME_SPIKE_MULTIPLIER = 2.0

# Horários prioritários (UTC)
PRIORITY_HOURS = [0, 6, 13]
```

### Pares Monitorados

Edite `TradingPairs.USDT_PAIRS` em `config/config.py` para personalizar os pares monitorados.

## 📁 Estrutura do Projeto

```
mexc_scalping_bot/
├── config/
│   └── config.py              # Configurações principais
├── src/
│   ├── api/
│   │   └── mexc_client.py     # Cliente da API MEXC
│   ├── indicators/
│   │   └── technical_analysis.py  # Indicadores técnicos
│   ├── strategies/
│   │   └── signal_generator.py    # Geração de sinais
│   ├── alerts/
│   │   └── telegram_bot.py    # Bot do Telegram
│   └── utils/
│       ├── logger.py          # Sistema de logging
│       ├── helpers.py         # Funções auxiliares
│       └── data_manager.py    # Gerenciamento de dados
├── data/                      # Cache de dados
├── logs/                      # Arquivos de log
├── tests/                     # Testes unitários
├── main.py                    # Arquivo principal
├── requirements.txt           # Dependências
└── README.md                  # Esta documentação
```

## 🔍 Logs e Monitoramento

### Logs

Os logs são salvos em `logs/trading_bot.log` e incluem:

- Sinais detectados
- Erros de API
- Status do bot
- Análises realizadas

### Monitoramento via Telegram

O bot envia automaticamente:

- Status a cada hora
- Alertas de erro
- Resumo diário
- Teste de conexão na inicialização

## ⚠️ Limitações Importantes

1. **Sem Execução Automática**: A API da MEXC não permite envio de ordens automáticas para usuários comuns
2. **Apenas Alertas**: O bot envia alertas para entrada manual
3. **Rate Limiting**: Respeita os limites da API (20 requests/2 segundos)
4. **Dados Históricos**: Limitado aos dados disponíveis na API pública

## 🛡️ Gerenciamento de Risco

### Recomendações

1. **Nunca invista mais do que pode perder**
2. **Use sempre stop loss**
3. **Diversifique suas operações**
4. **Monitore o mercado constantemente**
5. **Teste em conta demo primeiro**

### Configurações de Risco

- Tamanho da posição: 1% da margem (configurável)
- Stop loss baseado em ATR
- Múltiplos take profits (Fibonacci)
- Análise de tendência obrigatória

## 🔧 Troubleshooting

### Problemas Comuns

1. **Erro de API Key**
   - Verifique se as chaves estão corretas
   - Confirme se a API está habilitada na MEXC

2. **Bot não envia mensagens**
   - Verifique o token do Telegram
   - Confirme o Chat ID
   - Teste a conexão manualmente

3. **Dados não carregam**
   - Verifique conexão com internet
   - Confirme se a API da MEXC está funcionando
   - Limpe o cache: `rm -rf data/*.json`

### Debug

Para debug detalhado, altere em `config/config.py`:

```python
LOG_LEVEL = 'DEBUG'
```

## 📈 Backtesting (Futuro)

O sistema está preparado para implementação de backtesting:

- Estrutura de dados compatível
- Configurações de período
- Métricas de performance

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

## ⚠️ Disclaimer

Este software é fornecido apenas para fins educacionais e informativos. O trading de criptomoedas envolve riscos significativos e você pode perder todo o seu capital investido. Os desenvolvedores não se responsabilizam por perdas financeiras decorrentes do uso deste software.

**USE POR SUA PRÓPRIA CONTA E RISCO.**

## 📞 Suporte

Para suporte e dúvidas:

1. Abra uma issue no GitHub
2. Consulte a documentação
3. Verifique os logs para diagnóstico

---

**Desenvolvido com ❤️ pela equipe Manus AI**

