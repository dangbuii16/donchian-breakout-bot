from metrics.metrics import performance_report, drawdown_stats
from data.data_process import get_data_from_mt5, add_bid_ask_columns
from strategies.donchian_strat import donchian_breakout_channel_v2

def run_backtest_for_symbol(
    pair, timeframe, start_date, end_date,
    initial_capital, risk_per_trade, risk_mode, commission_per_lot,
    lookback, close_col_name='bid_c', spread_col='real_spread',
    backtest_func=None
):
    """
    Run backtest of Donchian breakout VERSION 2 for given symbol and return results including signals, trades, performance report, balance series, drawdown stats.
    
    Arguments:
    - pair: str, trading symbol
    - timeframe: MT5 timeframe constant (e.g., mt5.TIMEFRAME_H1)
    - start_date: datetime, start date for data retrieval
    - end_date: datetime, end date for data retrieval   
    - initial_capital: float, starting capital for backtest
    - risk_per_trade: float, risk amount or percentage per trade
    - risk_mode: str, either "FIXED_AMOUNT" or "PCT_BALANCE"
    - commission_per_lot: float, commission cost per lot traded
    - lookback: int, lookback period for Donchian channel
    - close_col_name: str, name of the close price column in DataFrame
    - spread_col: str, name of the spread column in DataFrame
    - backtest_func: function, optional custom backtest function to use
    """
    
    if backtest_func is None:
        from backtest.backtest import backtest_donchian_trades as backtest_func

    raw = get_data_from_mt5(pair, timeframe, start_date, end_date)
    data = add_bid_ask_columns(pair, raw)

    signal = donchian_breakout_channel_v2(data, lookback=lookback,
                                          close_col_name=close_col_name, spread_col=spread_col)

    trades = backtest_func(pair, signal, initial_capital, risk_per_trade, risk_mode, commission_per_lot)

    report_df, balance_series, balance_daily = performance_report(
        signals_df=signal,
        trade_df=trades,
        initial_capital=initial_capital,
        start_date=start_date,
        end_date=end_date,
        time_col='time',
    )

    dd_stats, dd_pct = drawdown_stats(balance_daily, return_dd_series=True)

    return {
        "pair": pair,
        "signal": signal,
        "trades": trades,
        "report_df": report_df,
        "balance_series": balance_series,
        "balance_daily": balance_daily,
        "dd_stats": dd_stats,
        "dd_pct": dd_pct,
    }