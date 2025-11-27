# Telegram Forex Signal Hooks (tghooks)

[![GitHub stars](https://img.shields.io/github/stars/mamolas/tghooks)](https://github.com/mamolas/tghooks)
[![GitHub license](https://img.shields.io/github/license/mamolas/tghooks)](https://github.com/mamolas/tghooks/blob/main/LICENSE)

**tghooks** is a tool that bridges Telegram forex signal channels to MetaTrader 5 (MT5), automatically executing trades based on signals received from Telegram groups/channels by integrating Telethon with MT5 for automated trading.

## 🚀 Features

- Real-time Telegram signal parsing and execution
- MT5 trade automation
- Configurable risk management
- Multiple symbol support
- Signal filtering and validation
- Only processes messages containing BUY/SELL keywords
- Maps symbols using your SYMBOL_MAP
- Places market orders at current/specified price
- Places pending orders at best price when different
- Sets TP (closest level) and SL automatically
- Uses channel ID as magic number and comment

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

1. Get API credentials from https://my.telegram.org
Replace API_ID, API_HASH, and PHONE_NUMBER in the `config.json` with your settings:

```json
{
  "MT5_INSTANCE": {
    "main": "C:\\Program Files\\MetaTrader\\terminal64.exe"
  },
  "CHANNEL_IDS": [1002980294890,1001609594692, 1002080341106, 1001490446443,1001584939836,1001272542052,1002495224665],
  "SYMBOL_MAP": {
    "XAUUSD": "XAUUSDz",
    "GOLD": "XAUUSDz"
  },
  "API_ID": "your_api_id",
  "API_HASH": "your_api_hash",
  "PHONE_NUMBER": "1234567890",
  "TP_THRESHOLD": 0.0015,
  "SL_THRESHOLD": 0.0015
}

```
TP_THRESHOLD and SL_THRESHOLD (both default 0.0015 or 0.15%) act as maximum relative distance filters from entry price. They prevent execution of signals with unrealistically distant take profit/stop loss levels, or when the signal provider didn't define a TP/SL 
0.15% is very thight because the sample groups trade mostly 1min Gold scalping usually with a very small TP/SL.

2. MT5 Setup:

Ensure MT5 is installed at the specified path
Enable algorithmic trading in MT5


## ▶️ Usage

```bash
python main.py
```

## 📊 Signal Format

Supports common forex signal formats, it handles all the parsing automatically and executes both market and pending orders as needed.:

```
EURUSD BUY 1.0850 TP:1.0900 SL:1.0820
GBPUSD SELL 1.2650 | TP1:1.2600 TP2:1.2550 | SL:1.2700
"GOLD BUY 3527/ 3524" → Market buy + Buy limit at 3524
"GOLD SELL NOW PRICE: 3551 -3554" → Market sell + Sell limit at 3554
"Compro oro ahora 3538.4 - 3535" → Market buy + Buy limit at 3535

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
- [Telethon](https://github.com/LonamiWebs/Telethon)
- Forex trading community
