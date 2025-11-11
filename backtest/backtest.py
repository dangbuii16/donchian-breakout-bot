import numpy as np
import pandas as pd
import MetaTrader5 as mt5
import math
import datetime as dt


def calculate_lot_size(pair, entry_price, stop_loss, capital, risk_pct, risk_mode, order_type):
    """ 
    Calculate lot size based on risk percentage. If min_volume leads to a loss greater than list_pct return 0
    """
    
    if risk_mode == 'FIXED_AMOUNT':
        risk_money = risk_pct

    else:
        risk_money = capital * risk_pct

    info = mt5.symbol_info(pair)

    vol_step = float(info.volume_step)
    min_vol = float(info.volume_min)
    max_vol = float(info.volume_max)

    # Calculate loss per 1 lot 
    order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL
    loss_per_1lot = abs(mt5.order_calc_profit(order_type_mt5, pair, 1, entry_price, stop_loss))
    if loss_per_1lot <= 0:
        return 0
    
    # Calculate final lot size
    raw_lot = risk_money / loss_per_1lot
    raw_lot = max(min_vol, min(max_vol, raw_lot))

    steps = (raw_lot - min_vol) / vol_step
    steps_floor = math.floor(steps)
    lot = round(min_vol + steps_floor * vol_step, 2)

    # Check if min_volume leads to a loss greater than risk_pct
    potential_loss = abs(mt5.order_calc_profit(order_type_mt5, pair, lot, entry_price, stop_loss))
    if potential_loss > risk_money:
        return 0
    
    return lot

def backtest_donchian_trades(pair, df, capital, risk_pct, risk_mode, commission):
    """ 
    Backtest donchian breakout strategy with given DataFrame and return a DataFrame of trade results 
    """

    trade_log = []

    for i, row in df.iterrows():
        if row['entry'] != 0:
            side = "BUY" if row['entry'] == 1 else "SELL"
            if side == "BUY": 
                entry_price = row['ask_c'] 
                stop_loss = row['sl_buy']
            else:
                entry_price = row['bid_c'] 
                stop_loss = row['sl_sell']

            # Calculate lot size
            lot = calculate_lot_size(pair, entry_price, stop_loss, capital, risk_pct, risk_mode, side)
            if lot == 0:
                continue

            # Find exit price and calculate PnL
            exit_row = None
            for j in range(i+1, len(df)):
                next_bar = df.iloc[j]
                # opposite entry -> exit trade
                if next_bar['entry'] == -row['entry']:
                    exit_row = next_bar
                    exit_reason = "Reverse_signal"
                    break
                # hit stop loss
                if side == "BUY" and next_bar['bid_l'] <= stop_loss:
                    exit_row = next_bar 
                    exit_reason = "SL"    
                    break
                if side == "SELL" and next_bar['ask_h'] >= stop_loss:
                    exit_row = next_bar
                    exit_reason = "SL"
                    break

            # If trade still open at the end of data, close at last bar
            if exit_row is None:
                exit_row = df.iloc[-1]
                exit_reason = "End of Data"

            if exit_reason == "SL":
                exit_price = stop_loss
            else:
                exit_price = exit_row['bid_c'] if side == 'BUY' else exit_row['ask_c']

            # Calculate PnL
            order_type_mt5 = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL
            profit_bc = mt5.order_calc_profit(order_type_mt5, pair, lot, entry_price, exit_price)
            total_commission = commission * lot
            profit_ac = profit_bc -total_commission

            capital += profit_ac

            trade_log.append({
                "symbol": pair,
                "entry_time": row['time'],
                "exit_time": exit_row['time'],
                "exit_reason": exit_reason,
                "side": side,
                "lot": lot,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "profit_bc": profit_bc,
                "commission": total_commission,
                "profit_ac": profit_ac,
                "acc_balance": capital
            })

    trade_df = pd.DataFrame(trade_log)
    return trade_df

