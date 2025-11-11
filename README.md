# Donchian Breakout Strategy

## Hypothesis
This project implements a **Donchian Channel Breakout** trading strategy, tested on MetaTrader 5 data.  
The system detects breakouts of price above or below the Donchian channel and executes trades according to two versions.

### Version 1 — Basic Donchian Breakout
- **Entry Conditions:**
  - **Buy (1)** when the close price is higher than the previous *Donchian High*.
  - **Sell (-1)** when the close price is lower than the previous *Donchian Low*.
- **Position Handling:**
  - Multiple entries are allowed in the same direction when new breakouts occur.
- **Stop-Loss:**
  - **Buy:** `SL = Donchian Low − Spread`
  - **Sell:** `SL = Donchian High + Spread`

### Version 2 — Single Position Donchian Breakout
Same breakout conditions as Version 1, but the system only keeps **one open position at a time**.  
New entries are ignored until the current position is closed or reversed by an opposite breakout.

---

## Data
- **Source:** Historical OHLC data retrieved directly from MetaTrader 5 (MT5) using the `MetaTrader5` Python API.
- **Period:** Defined in `config.py` (`START_DATE`, `END_DATE`).
- **Columns:**
  - `bid_o, bid_h, bid_l, bid_c` — Bid OHLC prices  
  - `ask_o, ask_h, ask_l, ask_c` — Ask OHLC prices  
  - `real_spread` — Actual spread calculated per symbol

### Data Retrieval
Data is obtained through the `data_process.py` script:
```python
from data_process import get_data_from_mt5, add_bid_ask_columns
df = get_data_from_mt5(pair, timeframe, start_date, end_date)
df = add_bid_ask_columns(pair, df)
```

## Implementation

### 1. Environment Setup

Install dependencies:
```bash
pip install -r requirements.txt
```
Create a .env file containing MT5 credentials:
```python
MT5_LOGIN=<your MT5 login>
MT5_PASSWORD=<your MT5 password>
MT5_SERVER=<your MT5 server name>
```

### 2. Backtest Execution

Run the backtest pipeline inside your notebook or script:
```python
from runner_v2 import run_backtest_for_symbol
from plotting_utils import plot_equity_and_dd, plot_trade_distribution_and_side_pnl
from datetime import datetime as dt
import MetaTrader5 as mt5

res = run_backtest_for_symbol(
    pair="BTCUSD",
    timeframe=mt5.TIMEFRAME_H1,
    start_date=dt(2020,1,1),
    end_date=dt(2025,1,1),
    initial_capital=5000,
    risk_per_trade=150,
    risk_mode="FIXED_AMOUNT",
    commission_per_lot=0,
    lookback=100
)
```

### 3. Output Components

- **Signals DataFrame:** includes `signal`, `entry`, `position`, `sl_buy`, and `sl_sell`  
- **Trade Log:** includes `entry_time`, `exit_time`, `side`, `profit_ac`, and `acc_balance`  
- **Performance Report:** includes Sharpe ratio, Profit factor, Max Drawdown, Win rate, etc.  
- **Plots:** equity curve, drawdown curve, and trade distribution charts

## Optimization

Use `grind_search.py` to run parameter sweeps for Donchian lookback values:
```python
from grind_search import grind_search_parameters
from datetime import datetime as dt
import MetaTrader5 as mt5

grind_df, figs = grind_search_parameters(
    pairs=["BTCUSD"],
    timeframe=mt5.TIMEFRAME_H1,
    start_date=dt(2020,1,1),
    end_date=dt(2023,1,1),
    lookbacks=[20,50,100,150],
    initial_capital=5000,
    risk_per_trade=150,
    risk_mode="FIXED_AMOUNT"
)
```
Each test produces performance metrics (`Sharpe, Profit Factor, Max DD`) and comparison plots for parameter evaluation.

## Evaluation Metrics

Metrics are computed via `metrics.py`:

- **Sharpe Ratio** and **Sortino Ratio**  
- **Maximum Drawdown (%)**  
- **Profit Factor**  
- **Win Rate (%)**  
- **Average / Best / Worst Trade Return**  
- **Trade Duration (minutes)**  
- **Consecutive Wins/Losses**  
- **Equity Curve and Drawdown Charts**  

---

## Result Summary

- The **backtest results for BTCUSD** and the **optimized parameters** are stored and visualized in the `btc_main.ipynb` file.  
- The notebook includes equity & drawdown charts and trade distribution plots for both training and test periods.  



