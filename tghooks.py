import asyncio
import re
import logging
import json
import os
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import MetaTrader5 as mt5
from telethon import TelegramClient, events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load config
CONFIG_FILE = "config.json"
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Config file {CONFIG_FILE} not found")

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

MT5_INSTANCE = config["MT5_INSTANCE"]
CHANNEL_IDS = config["CHANNEL_IDS"]
SYMBOL_MAP = config["SYMBOL_MAP"]
API_ID = config["API_ID"]
API_HASH = config["API_HASH"]
PHONE_NUMBER = config["PHONE_NUMBER"]
TP_THRESHOLD = config.get("TP_THRESHOLD", 0.01)
SL_THRESHOLD = config.get("SL_THRESHOLD", 0.01)

KW_BUY = ["BUY", "compro"]
KW_SELL = ["SELL", "vendo"]
KW_TP = ["TP"]
KW_SL = ["SL"]

@dataclass
class TradingSignal:
    symbol: str
    action: str  # BUY or SELL
    entry_price: Optional[float] = None
    best_price: Optional[float] = None
    tp_levels: List[float] = None
    sl_level: Optional[float] = None
    channel_id: int = None
    magic_number: int = None
    comment: str = ""
    
    def __post_init__(self):
        if self.tp_levels is None:
            self.tp_levels = []

# --- Helper to sanitize MT5 comments ---
def sanitize_comment(c: str) -> str:
    safe = re.sub(r'[^A-Za-z0-9 ]', '', c)  # only alphanum + spaces
    return safe.strip()[:30]  # enforce max 30 chars

class MT5TelegramBot:
    def __init__(self):
        self.client = TelegramClient('session_name', API_ID, API_HASH)
        self.mt5_initialized = False
        
    async def initialize(self):
        await self.client.start(phone=PHONE_NUMBER)
        logger.info("Telegram client initialized")
        
        if not mt5.initialize(path=MT5_INSTANCE["main"]):
            logger.error(f"MT5 initialization failed: {mt5.last_error()}")
            return False
        
        self.mt5_initialized = True
        logger.info("MT5 initialized successfully")
        
        account_info = mt5.account_info()
        if account_info:
            logger.info(f"Connected to MT5 account: {account_info.login}")
        
        return True
    
    def parse_signal(self, message_text: str, channel_id: int) -> Optional[TradingSignal]:
        text = message_text.upper().strip()
        
        has_buy = any(kw in text for kw in [kw.upper() for kw in KW_BUY])
        has_sell = any(kw in text for kw in [kw.upper() for kw in KW_SELL])
        
        if not (has_buy or has_sell):
            return None
        
        action = "BUY" if has_buy else "SELL"
        
        symbol = None
        for key, mt5_symbol in SYMBOL_MAP.items():
            if key.upper() in text:
                symbol = mt5_symbol
                break
        
        if not symbol:
            logger.warning(f"No valid symbol found in message: {text[:100]}")
            return None
        
        price_patterns = [
            r'(\d+\.?\d*)\s*/\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*–\s*(\d+\.?\d*)',
        ]
        
        entry_price = None
        best_price = None
        
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                price1, price2 = float(matches[0][0]), float(matches[0][1])
                if action == "BUY":
                    entry_price = max(price1, price2)
                    best_price = min(price1, price2)
                else:
                    entry_price = min(price1, price2)
                    best_price = max(price1, price2)
                break
        
        if entry_price is None:
            price_matches = re.findall(r'(\d+\.?\d*)', text)
            if price_matches:
                entry_price = float(price_matches[0])
        
        tp_levels = []
        tp_patterns = [
            r'TP\s*[¹²³⁴1234]?\s*:??\s*(\d+\.?\d*)',
            r'TP\s*[¹²³⁴1234]?\s*(\d+\.?\d*)',
            r'(\d+)\s*PIPS?\)',
        ]
        
        for pattern in tp_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if 'PIP' in pattern:
                    if entry_price:
                        pip_value = int(match)
                        if action == "BUY":
                            tp_price = entry_price + (pip_value * 0.01)
                        else:
                            tp_price = entry_price - (pip_value * 0.01)
                        tp_levels.append(tp_price)
                else:
                    tp_levels.append(float(match))
        
        sl_level = None
        sl_patterns = [
            r'SL\s*:??\s*(\d+\.?\d*)',
        ]
        
        for pattern in sl_patterns:
            match = re.search(pattern, text)
            if match:
                sl_level = float(match.group(1))
                break
        
        magic_number = channel_id
        comment = str(channel_id)
        
        signal = TradingSignal(
            symbol=symbol,
            action=action,
            entry_price=entry_price,
            best_price=best_price,
            tp_levels=tp_levels,
            sl_level=sl_level,
            channel_id=channel_id,
            magic_number=magic_number,
            comment=comment
        )
        
        return signal
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        if not self.mt5_initialized:
            return None
            
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Symbol {symbol} not found")
            return None
            
        return {
            'digits': symbol_info.digits,
            'point': symbol_info.point,
            'min_lot': symbol_info.volume_min,
            'max_lot': symbol_info.volume_max,
            'lot_step': symbol_info.volume_step,
            'tick_size': symbol_info.trade_tick_size,
            'tick_value': symbol_info.trade_tick_value,
        }
    
    def calculate_lot_size(self, symbol: str, risk_amount: float = 100.0) -> float:
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            return 0.01
        lot_size = max(symbol_info['min_lot'], 0.01)
        return min(lot_size, symbol_info['max_lot'])
    
    async def execute_trades(self, signal: TradingSignal):
        if not self.mt5_initialized:
            logger.error("MT5 not initialized")
            return
        
        if not mt5.symbol_select(signal.symbol, True):
            logger.error(f"Failed to select symbol {signal.symbol}")
            return
        
        symbol_info = self.get_symbol_info(signal.symbol)
        if not symbol_info:
            return
        
        lot_size = self.calculate_lot_size(signal.symbol)
        tick = mt5.symbol_info_tick(signal.symbol)
        if not tick:
            logger.error(f"Failed to get tick data for {signal.symbol}")
            return
        
        current_price = tick.ask if signal.action == "BUY" else tick.bid
        entry_price = signal.entry_price or current_price
        
        # --- Handle TP ---
        tp_price = signal.tp_levels[0] if signal.tp_levels else None
        tp_comment = ""
        if not tp_price or abs(tp_price - entry_price) / entry_price > TP_THRESHOLD:
            if signal.action == "BUY":
                tp_price = entry_price * (1 + TP_THRESHOLD)
            else:
                tp_price = entry_price * (1 - TP_THRESHOLD)
            tp_comment = " TPT"
            logger.info(f"TP adjusted to {tp_price} using threshold")
        
        # --- Handle SL ---
        sl_price = signal.sl_level
        sl_comment = ""
        if not sl_price or abs(sl_price - entry_price) / entry_price > SL_THRESHOLD:
            if signal.action == "BUY":
                sl_price = entry_price * (1 - SL_THRESHOLD)
            else:
                sl_price = entry_price * (1 + SL_THRESHOLD)
            sl_comment = " SLT"
            logger.info(f"SL adjusted to {sl_price} using threshold")
        
        digits = symbol_info['digits']
        current_price = round(current_price, digits)
        tp_price = round(tp_price, digits)
        sl_price = round(sl_price, digits)
        
        magic_number = int(str(abs(signal.channel_id))[-6:])
        comment = (str(abs(signal.channel_id))[-6:] + tp_comment + sl_comment)
        comment = sanitize_comment(comment)
        
        try:
            market_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": signal.symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_BUY if signal.action == "BUY" else mt5.ORDER_TYPE_SELL,
                "price": current_price,
                "magic": magic_number,
                "comment": sanitize_comment(comment),
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
                "sl": float(sl_price),
                "tp": float(tp_price),
            }
            
            logger.info(f"Sending market order: {market_request}")
            result = mt5.order_send(market_request)
            
            if result is None:
                logger.error(f"Order send returned None, last error: {mt5.last_error()}")
                return
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Market order failed: {result.retcode} - {result.comment}")
            else:
                logger.info(f"Market order executed: {signal.action} {signal.symbol} at {current_price}")
        
        except Exception as e:
            logger.error(f"Exception during market order: {e}")
            return
        
        if signal.best_price and abs(signal.best_price - current_price) > symbol_info['tick_size']:
            try:
                pending_type = None
                if signal.action == "BUY":
                    pending_type = mt5.ORDER_TYPE_BUY_LIMIT if signal.best_price < current_price else mt5.ORDER_TYPE_BUY_STOP
                else:
                    pending_type = mt5.ORDER_TYPE_SELL_LIMIT if signal.best_price > current_price else mt5.ORDER_TYPE_SELL_STOP
                
                pending_request = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": signal.symbol,
                    "volume": lot_size,
                    "type": pending_type,
                    "price": signal.best_price,
                    "magic": magic_number,
                    "comment": sanitize_comment(f"{comment[:26]}_pend"),
                    "type_time": mt5.ORDER_TIME_SPECIFIED,
                    "expiration": int(time.time()) + 15 * 60,  # expire in 15 minutes
                    "sl": float(sl_price),
                    "tp": float(tp_price),
                }
                
                logger.info(f"Sending pending order: {pending_request}")
                result = mt5.order_send(pending_request)
                
                if result is None:
                    logger.error(f"Pending order send returned None, last error: {mt5.last_error()}")
                    return
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    logger.error(f"Pending order failed: {result.retcode} - {result.comment}")
                else:
                    logger.info(f"Pending order placed: {signal.action} {signal.symbol} at {signal.best_price}")
                    
            except Exception as e:
                logger.error(f"Exception during pending order: {e}")
    
    async def start_listening(self):
        @self.client.on(events.NewMessage(chats=CHANNEL_IDS))
        async def message_handler(event):
            try:
                channel_id = event.chat_id
                message_text = event.raw_text
                
                logger.info(f"Received message from {channel_id}: {message_text[:100]}...")
                
                signal = self.parse_signal(message_text, channel_id)
                
                if signal:
                    logger.info(f"Valid signal parsed: {signal}")
                    await self.execute_trades(signal)
                else:
                    logger.info("Message discarded - no valid signal found")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
        
        logger.info("Starting to listen for messages...")
        await self.client.run_until_disconnected()
    
    async def shutdown(self):
        await self.client.disconnect()
        if self.mt5_initialized:
            mt5.shutdown()
        logger.info("Bot shutdown complete")

async def main():
    bot = MT5TelegramBot()
    
    try:
        if await bot.initialize():
            await bot.start_listening()
        else:
            logger.error("Failed to initialize bot")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
