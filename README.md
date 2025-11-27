# Telegram Forex Signal Hooks (tghooks)

[![GitHub stars](https://img.shields.io/github/stars/mamolas/tghooks)](https://github.com/mamolas/tghooks)
[![GitHub license](https://img.shields.io/github/license/mamolas/tghooks)](https://github.com/mamolas/tghooks/blob/main/LICENSE)

**tghooks** is a tool that bridges Telegram forex signal channels to MetaTrader 5 (MT5), automatically executing trades based on signals received from Telegram groups/channels.

## 🚀 Features

- Real-time Telegram signal parsing and execution
- MT5 trade automation
- Configurable risk management
- Multiple symbol support
- Signal filtering and validation

## 📋 Prerequisites

- MetaTrader 5 terminal
- Telegram account and bot token
- Python 3.8+

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/mamolas/tghooks.git
cd tghooks

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

1. Create `config.json` with your settings:
```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "mt5": {
    "login": "YOUR_MT5_LOGIN",
    "password": "YOUR_MT5_PASSWORD",
    "server": "YOUR_BROKER_SERVER"
  },
  "risk": {
    "max_risk_percent": 2.0,
    "max_positions": 5
  }
}
```

2. Get Telegram Bot Token: [@BotFather](https://t.me/botfather)
3. Get Chat ID from your signal channel/group

## ▶️ Usage

```bash
python main.py
```

## 📊 Signal Format

Supports common forex signal formats:

```
EURUSD BUY 1.0850 TP:1.0900 SL:1.0820
GBPUSD SELL 1.2650 | TP1:1.2600 TP2:1.2550 | SL:1.2700
```

## 🛡️ Risk Management

- Automatic position sizing based on account balance
- Stop loss and take profit execution
- Maximum daily loss limits
- Partial close support

## 🔧 Development

```bash
# Run tests
pytest tests/

# Lint code
flake8 .

# Run with debug logging
debug=true python main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [MetaTrader 5 Python API](https://www.mql5.com/en/docs/integration/python_metatrader5)
- [python-telegram-bot](https://python-telegram-bot.org/)
- Forex trading community