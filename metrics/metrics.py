import pandas as pd
import numpy as np
from config.config import INITIAL_CAPITAL, RISK_FREE_RATE


def acc_balance_from_signals(signals_df, trade_df, initial_capital = INITIAL_CAPITAL,
                             time_col ='time', exit_col='exit_time'):
    """ 
    Return a Series of account balance over time based on signals and trade results.
    
    signal_df: df from donchian_breakout_channel() or strategy signal function
    trade_df: df from backtest_donchian_trades() or backtest function
    """

    sig = signals_df[[time_col]].copy()
    sig[time_col] = pd.to_datetime(sig[time_col])
    sig = sig.set_index(time_col).sort_index()

    exits = trade_df[[exit_col, 'acc_balance']].copy()
    exits[exit_col] = pd.to_datetime(exits[exit_col])
    exits = exits.set_index(exit_col).sort_index()

    merged = sig.join(exits[['acc_balance']], how='left')

    if len(merged) == 0:
        return pd.Series([], name='acc_balance')
    
    merged.loc[merged.index[0], 'acc_balance'] = float(initial_capital)
    merged['acc_balance'] = merged['acc_balance'].ffill().fillna(float(initial_capital))

    return merged['acc_balance']


def to_balance_daily(balance_series: pd.Series):
    """ 
    Convert balance series to daily frequency by resampling and ffill
    """
    # group by day, take the last value of each day then ffill
    
    daily_balance = balance_series.resample('D').last().ffill()
    daily_balance.name = 'balance_daily'
    return daily_balance


def drawdown_stats(balance_series, return_dd_series=False):
    """ 
    Calculate drawdown statistics from balance series and return a dictionary of max DD, avg DD, max DD duration, avg DD duration
    If return_dd_series is True return the drawdown stats dictionary & drawdown series for plotting the DD over time    
    """

    peak = balance_series.cummax()
    dd = balance_series/peak - 1.0
    dd_pct = dd * 100.0

    # Calculate durations of drawdowns
    durations, cur = [], 0
    for is_dd in (dd < 0).tolist():
        if is_dd:
            cur += 1
        else:
            if cur > 0:
                durations.append(cur)
            cur = 0
    if cur > 0:
        durations.append(cur)

    dd_stats = {
        'max_dd_pct': float(dd_pct.min()) if dd_pct.any() else 0.0,
        'avg_dd_pct': float(dd_pct[dd_pct < 0].mean()) if (dd_pct < 0).any() else 0.0,
        'max_dd_duration_days': int(max(durations)) if durations else 0,
        'avg_dd_duration_days': float(np.mean(durations)) if durations else 0.0
    }
    if return_dd_series:
        return dd_stats, dd_pct
    else:
        return dd_stats
    

def sharpe_sortino_from_balance(balance_series, rf_daily=RISK_FREE_RATE):
    """ 
    Calculate Sharpe and Sortino ratios from balance series
    """ 
    balance_daily = to_balance_daily(balance_series)
    rets = balance_daily.pct_change().dropna()
    if len(rets) == 0 or rets.std(ddof=1) == 0:
        return 0.0, 0.0
    
    excess_rets = rets - rf_daily
    sharpe = float(excess_rets.mean()/rets.std(ddof=1) * np.sqrt(252))

    downside_rets = rets[rets < 0]
    if len(downside_rets) == 0 or downside_rets.std(ddof=1) == 0:
        sortino = float('inf') # No downside volatility => infinite sortino
    else:
        sortino = float(excess_rets.mean()/downside_rets.std(ddof=1) * np.sqrt(252))
    
    return sharpe, sortino

def trade_returns(trade_df: pd.DataFrame, mode: str = "pct"):
    """
    Calculate returns of each trade. if:
    - mode='pct': %return = profit_ac / capital_before_entry
    - mode='abs': absolute return = profit_ac
    """
    if trade_df.empty:
        return pd.Series(dtype=float, name="trade_returns")

    cap_before = trade_df['acc_balance'] - trade_df['profit_ac']

    if mode == "pct":
        ret = trade_df['profit_ac'] / cap_before.replace(0, np.nan)
        ret = ret.replace([np.inf, -np.inf], np.nan).dropna()
        ret.name = "trade_return_pct"
        return ret * 100.0
    
    elif mode == "abs":
        ret = trade_df['profit_ac'].astype(float)
        ret.name = "trade_return_abs"
        return ret
    
    else:
        raise ValueError("mode must be 'pct' or 'abs'")



def performance_report(signals_df, trade_df, initial_capital=INITIAL_CAPITAL,
                       start_date=None, end_date=None, time_col='time'):
    """ 
    Build a performance report in form of DataFrame from signals and trade results:
    - signal_df: DataFrame from strategy signal function
    - trade_df : DataFrame from backtest results function
    - initial_capital: starting balance
    - start_date, end_date: optional override for date range
    """
    
    # Full time series of account balance
    balance_series = acc_balance_from_signals(signals_df, trade_df, initial_capital, time_col=time_col)
    if balance_series.empty:
        raise ValueError("Balance series is empty")
    
    # Convert to daily balance series
    balance_daily = to_balance_daily(balance_series)

    start = pd.to_datetime(start_date) if start_date else balance_daily.index.min()
    end = pd.to_datetime(end_date) if end_date else balance_daily.index.max()
    duration_days = int((end-start).days)
    years = max(duration_days/365.25, 1e-9)
    months = max(duration_days/30.44, 1e-9)

    # Compute metrics
    # Return metrics
    balance_final = float(balance_daily.iloc[-1])
    balance_peak = float(balance_daily.max())
    net_profit = balance_final - initial_capital
    
    if balance_final <= 0:
        total_return = -100.0
        annualized_return = -100.0
        monthly_return = -100.0
    else:
        total_return = (balance_final/initial_capital -1) * 100.0
        annualized_return = ((balance_final/initial_capital) ** (1/years) -1) * 100.0
        monthly_return = ((balance_final/initial_capital) ** (1/months) -1) * 100.0

    # Risk metrics
    sharpe, sortino = sharpe_sortino_from_balance(balance_series)
    dd_stats = drawdown_stats(balance_series)

    # Trade-level metrics
    n = len(trade_df)

    trade_pct_ret = trade_returns(trade_df, mode="pct") 

    # Winrate, % returns per trade
    winrate = float((trade_df['profit_ac'] > 0).sum() / n * 100.0)
    best_trade = float(np.nanmax(trade_pct_ret))
    worst_trade = float(np.nanmin(trade_pct_ret))
    avg_trade = float(np.nanmean(trade_pct_ret))

    # Trade duration stats
    dur_mins_trade = (pd.to_datetime(trade_df['exit_time']) - pd.to_datetime(trade_df['entry_time'])).dt.total_seconds() / 60.0
    max_trade_dur_mins = float(dur_mins_trade.max())
    avg_trade_dur_mins = float(dur_mins_trade.mean())

    # Profit factor
    gross_profit = float(trade_df.loc[trade_df['profit_ac'] > 0, 'profit_ac'].sum())
    gross_loss = float(trade_df.loc[trade_df['profit_ac'] < 0, 'profit_ac'].sum())
    profit_factor = gross_profit / abs(gross_loss) if gross_loss != 0 else float('inf')

    # Long/Short stats
    long_trades = trade_df[trade_df['side'] == "BUY"]
    short_trades = trade_df[trade_df['side'] == "SELL"]

    if len(long_trades) > 0:
        long_winrate = (long_trades['profit_ac'] > 0).mean() * 100.0
        long_profit = long_trades['profit_ac'].sum()

    else:
        long_winrate, long_profit = 0.0, 0.0

    if len(short_trades) > 0:
        short_winrate = (short_trades['profit_ac'] > 0).mean() * 100.0
        short_profit = short_trades['profit_ac'].sum()
    
    else:
        short_winrate, short_profit = 0.0, 0.0
    
    # Conseutive wins/losses
    profit_ac_value = trade_df['profit_ac'].values
    wins = (profit_ac_value > 0).astype(int)
    losses = (profit_ac_value < 0).astype(int)

    def longest_streak(mask, profit_array):
        max_count, max_sum, cur_count, cur_sum = 0, 0.0, 0, 0.0
        for i in range(len(profit_array)):
            if mask[i] == 1:
                cur_count += 1
                cur_sum += profit_array[i]

                if cur_count > max_count:
                    max_count = cur_count
                    max_sum = cur_sum
            else:
                cur_count, cur_sum = 0, 0.0 # reset value to 0
        
        return max_count, max_sum
    
    win_streak, win_strak_profit = longest_streak(wins, profit_ac_value)
    loss_streak, loss_streak_loss = longest_streak(losses, profit_ac_value)


    report = {
        # --- Basic info ---
        "Start date": pd.to_datetime(start),
        "End date": pd.to_datetime(end),
        "Duration (days)": duration_days,
        "Trades": int(n),

        # --- Return metrics ---
        "Equity Final ($)": round(balance_final, 2),
        "Equity Peak ($)": round(balance_peak, 2),
        "Net Profit ($)": round(net_profit, 2),
        "Return (%)": round(total_return, 2),
        "Return (annual - %)": round(annualized_return, 2),
        "Return (monthly - %)": round(monthly_return, 2),

        # --- Risk metrics ---
        "Sharpe ratio": round(sharpe, 3),
        "Sortino ratio": "No downside returns" if np.isinf(sortino) else round(sortino, 3),
        "Max DD (%)": round(dd_stats['max_dd_pct'], 2),
        "Avg DD (%)": round(dd_stats['avg_dd_pct'], 2),
        "Max DD Duration (days)": int(dd_stats['max_dd_duration_days']),
        "Avg DD Duration (days)": round(dd_stats['avg_dd_duration_days'], 1),

        # --- Trade-level metrics ---
        "Win rate (%)": round(winrate, 2),
        "Best trade (%)": round(best_trade, 2),
        "Worst trade (%)": round(worst_trade, 2),
        "Avg trade (%)": round(avg_trade, 2),
        "Max trade duration (mins)": round(max_trade_dur_mins, 2),
        "Avg trade duration (mins)": round(avg_trade_dur_mins, 2),
        "Profit factor": 0.0 if np.isinf(profit_factor) else round(profit_factor, 3),

        # --- Long/Short stats ---
        "Long trades winrate (%)": round(long_winrate, 2),
        "Long trades profit ($)": round(long_profit, 2),
        "Short trades winrate (%)": round(short_winrate, 2),
        "Short trades profit ($)": round(short_profit, 2),

        # --- Consecutive streaks ---
        "Consecutive wins (count)": int(win_streak),
        "Consecutive profit ($)": round(win_strak_profit, 2),
        "Consecutive losses (count)": int(loss_streak),
        "Consecutive losses ($)": round(loss_streak_loss, 2)
    }

    # Return report df, balance series and daily balance series for plotting
    report_df = pd.DataFrame([report])
    
    return report_df, balance_series, balance_daily