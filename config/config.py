import os
from datetime import datetime as dt
import MetaTrader5 as mt5
from dotenv import load_dotenv

load_dotenv()

# --- MT5 Credentials ---
MT5_LOGIN = int(os.getenv("MT5_LOGIN") or 0)
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_SERVER = os.getenv("MT5_SERVER")

# --- Pair & Risk management ---
RISK_FREE_RATE = 0.0

PAIR = "BTCUSD"
TIMEFRAME = mt5.TIMEFRAME_H1           
START_DATE = dt(2018,3,1)
END_DATE   = dt(2023,12,1)

INITIAL_CAPITAL = 5000
# Risk modes
RISK_MODE_FIXED_AMOUNT = "FIXED_AMOUNT"
RISK_MODE_PCT_BALANCE  = "PCT_BALANCE"

RISK_MODE = RISK_MODE_FIXED_AMOUNT

if RISK_MODE == RISK_MODE_FIXED_AMOUNT:
    RISK_PER_TRADE = 150          # fixed USD/trade
else:
    RISK_PER_TRADE = 0.02           # pecent of balance

COMMISSION_PER_LOT = 0

# --- Strategy parameters ---
DONCHIAN_LOOKBACK = 100