import numpy as np
import pandas as pd
import MetaTrader5 as mt5
import datetime as dt


def donchian_breakout_channel_v1(df, lookback = 50, close_col_name='bid_c', spread_col='real_spread'):
    """ 
    Generates Donchian Channel breakout signals and stop-loss levels
    """
    
    df['donchian_high'] = df[close_col_name].rolling(window=lookback -1).max().shift(1)
    df['donchian_low'] = df[close_col_name].rolling(window=lookback -1).min().shift(1)

    df['signal'] = 0
    df.loc[df[close_col_name] > df['donchian_high'], 'signal'] = 1
    df.loc[df[close_col_name] < df['donchian_low'], 'signal'] = -1
    df['signal'] = df['signal'].ffill().fillna(0).astype(int)

    # Store entry value
    s = df['signal']
    df['entry'] = np.where(( s!= 0 ) & (s != s.shift(1)), s, 0).astype(int)

    # Store current position
    df['position'] = df['entry'].replace(0, np.nan).ffill().fillna(0).astype(int)

    # Add Stop Loss
    spread_tick = df[spread_col]
    df['sl_buy'] = df['donchian_low'] - spread_tick
    df['sl_sell'] = df['donchian_high'] + spread_tick

    return df


def donchian_breakout_channel_v2(df, lookback=50, close_col_name='bid_c', spread_col='real_spread'):
    """
    Donchian breakout v2: only open 1 position at a time
    """
    df = df.copy()

    dh = df[close_col_name].rolling(window=lookback-1).max().shift(1)
    dl = df[close_col_name].rolling(window=lookback-1).min().shift(1)
    df['donchian_high'] = dh
    df['donchian_low']  = dl

    # 2) Tín hiệu thô của NẾN HIỆN TẠI (không ffill)
    #    +1: close > dh, -1: close < dl, 0: còn lại
    sig_raw = np.where(df[close_col_name] > df['donchian_high'],  1,
               np.where(df[close_col_name] < df['donchian_low'],  -1, 0))
    df['signal_raw'] = sig_raw

    # 3) Sinh entry & position theo state machine để tránh vào chồng lệnh
    entry = np.zeros(len(df), dtype=int)
    position = np.zeros(len(df), dtype=int)  # -1/0/1

    for i in range(len(df)):
        s = sig_raw[i]          # breakout ở nến hiện tại (có thể 0)
        pos_prev = position[i-1] if i > 0 else 0

        if pos_prev == 0:
            # đang flat: chỉ vào nếu có breakout (±1)
            if s != 0:
                entry[i] = s
                position[i] = s
            else:
                position[i] = 0
        else:
            # đang có vị thế: chỉ vào khi breakout đảo chiều
            if s != 0 and s == -pos_prev:
                entry[i] = s
                position[i] = s    # đảo chiều luôn
            else:
                position[i] = pos_prev  # giữ nguyên, KHÔNG vào thêm cùng chiều

    df['entry'] = entry.astype(int)
    df['position'] = position.astype(int)

    spread_tick = df[spread_col].astype(float)
    df['sl_buy']  = df['donchian_low']  - spread_tick
    df['sl_sell'] = df['donchian_high'] + spread_tick

    return df