import pandas as pd
import MetaTrader5 as mt5
import os
from datetime import datetime as dt


def get_data_from_mt5(pair, timeframe, start_date, end_date):
    avai_symbol_names = [symbol.name for symbol in mt5.symbols_get()]
    if pair not in avai_symbol_names:
        print(f'{pair} is not available in MT5 terminal')
    else:
        df = pd.DataFrame(mt5.copy_rates_range(pair, timeframe, start_date, end_date))
        df.time = pd.to_datetime(df.time, unit="s")
        print(f"Getting data of {pair}_{timeframe} successfully ")
    return df

def create_excel_from_mt5(pair, timeframe, start_date, end_date, file_path):
    df = get_data_from_mt5(pair, timeframe, start_date, end_date)
    
    start_year = start_date.year
    end_year = end_date.year
    timeframe_str = {mt5.TIMEFRAME_M1: "M1", mt5.TIMEFRAME_M5: "M5", mt5.TIMEFRAME_M15: "M15", mt5.TIMEFRAME_M30: "M30", mt5.TIMEFRAME_H1: "H1", mt5.TIMEFRAME_H4: "H4"}[timeframe]
    filename = f"{pair}_{timeframe_str}_{start_year}_{end_year}.xlsx"
    file_full_path = f"{file_path}\\{filename}"
    
    df.to_excel(file_full_path, index=False)
    print(f"Data saved in {file_full_path}")
    
    return df


def get_digits_number(pair: str):
    if not mt5.initialize():
        raise RuntimeError("MT5 is not initialized.")
    
    else:
        symbols = mt5.symbols_get()
        digits_dict = {symbol.name: symbol.digits for symbol in symbols}
        return digits_dict.get(pair, None)

def add_bid_ask_columns(pair : str, df: pd.DataFrame):
    bid_ask_df = df.copy()
    
    digit = get_digits_number(pair)
    if digit is None:
        raise ValueError(f"Could not retrieve digits for pair: {pair}")
     
    bid_ask_df['real_spread'] = bid_ask_df['spread'] * (10 ** -digit)

    for col in ["open", "high", "low", "close"]:
        bid_ask_df[f"bid_{col[0]}"] = bid_ask_df[col]
        bid_ask_df[f"ask_{col[0]}"] = bid_ask_df[col] + bid_ask_df['real_spread']
    
    bid_ask_df.drop(columns=["open", "high", "low", "close"], inplace=True)

    return bid_ask_df