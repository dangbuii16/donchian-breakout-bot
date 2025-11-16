import datetime as dt
import plotly.graph_objects as go
import pandas as pd

class CandlePlot:

    def __init__(self, df, candles=True) -> None:
        self.df_plot = df.copy()
        self.candles = candles
        self.create_candle_fig()

    def create_candle_fig(self):
        """ 
        Creat candle chart from price data
        """
        self.fig = go.Figure()
        if self.candles == True:
            self.fig.add_trace(go.Candlestick(
                            x=self.df_plot['time'],
                            open=self.df_plot['bid_o'],
                            high=self.df_plot['bid_h'],
                            low=self.df_plot['bid_l'],
                            close=self.df_plot['bid_c'],
                            line= dict(width = 1), opacity = 1,
                            increasing_line_color= '#24A06B',
                            decreasing_line_color= '#CC2E3C',
                            increasing_fillcolor= '#24A06B',
                            decreasing_fillcolor= '#CC2E3C',
                            ))
        
        self.fig.update_yaxes(
            gridcolor="#f0f0f0"
        )

        self.fig.update_xaxes(
            gridcolor='#f0f0f0',
            rangeslider_visible=True
        )
    
    def update_layout(self, width=1480, height=650):
        
        self.fig.update_yaxes(
            gridcolor="#f0f0f0"
        )

        self.fig.update_xaxes(
            gridcolor='#f0f0f0',
            rangeslider_visible=True
        )

        self.fig.update_layout(
            width = width,
            height = height,
            margin=dict(l=40, r=30, t=40, b=30),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff", 
            font=dict(size=12, color='#2c303c')
        )

    def add_traces(self, line_traces):
        """ 
        Add line traces to chart (EMA, SMA, Donchian high/low, .etc)
        """
        for line in line_traces:
            self.fig.add_trace(go.Scatter(
                x=self.df_plot['time'],
                y=self.df_plot[line],
                line=dict(width=2),
                line_shape='spline',
                name=line
            ))

    def add_trade_markers(self, trades_df, show_entry=True, show_exit=True):
        """
        Add trade entry/exit markers on top of the candlestick chart.
        """
        if trades_df is None or len(trades_df) == 0:
            return

        
        trades = trades_df.copy()
        trades['entry_time'] = pd.to_datetime(trades['entry_time'])
        trades['exit_time']  = pd.to_datetime(trades['exit_time'])

        buy_trades  = trades[trades['side'] == "BUY"]
        sell_trades = trades[trades['side'] == "SELL"]

        # Entry markers 
        if show_entry:
            # BUY entry:
            if not buy_trades.empty:
                self.fig.add_trace(
                    go.Scatter(
                        x=buy_trades['entry_time'],
                        y=buy_trades['entry_price'],
                        mode='markers',
                        name='Buy Entry',
                        marker=dict(
                            symbol='triangle-up',
                            size=10,
                            color='#24A06B',
                            line=dict(width=1, color='#1b5136')
                        ),
                        hovertemplate=(
                            "Buy Entry<br>"
                            "Time: %{x}<br>"
                            "Price: %{y:.5f}<extra></extra>"
                        )
                    )
                )
            # SELL entry:
            if not sell_trades.empty:
                self.fig.add_trace(
                    go.Scatter(
                        x=sell_trades['entry_time'],
                        y=sell_trades['entry_price'],
                        mode='markers',
                        name='Sell Entry',
                        marker=dict(
                            symbol='triangle-down',
                            size=10,
                            color='#CC2E3C',
                            line=dict(width=1, color='#6d1b23')
                        ),
                        hovertemplate=(
                            "Sell Entry<br>"
                            "Time: %{x}<br>"
                            "Price: %{y:.5f}<extra></extra>"
                        )
                    )
                )

        # Exit markers
        if show_exit:
            if not buy_trades.empty:
                self.fig.add_trace(
                    go.Scatter(
                        x=buy_trades['exit_time'],
                        y=buy_trades['exit_price'],
                        mode='markers',
                        name='Buy Exit',
                        marker=dict(
                            symbol='circle',
                            size=8,
                            color='#7fd8a9',
                            line=dict(width=1, color='#1b5136')
                        ),
                        hovertemplate=(
                            "Buy Exit<br>"
                            "Time: %{x}<br>"
                            "Price: %{y:.5f}<br>"
                            "PnL: %{customdata:.2f}$<extra></extra>"
                        ),
                        customdata=buy_trades['profit_ac']
                    )
                )
            if not sell_trades.empty:
                self.fig.add_trace(
                    go.Scatter(
                        x=sell_trades['exit_time'],
                        y=sell_trades['exit_price'],
                        mode='markers',
                        name='Sell Exit',
                        marker=dict(
                            symbol='circle',
                            size=8,
                            color='#f29ca6',
                            line=dict(width=1, color='#6d1b23')
                        ),
                        hovertemplate=(
                            "Sell Exit<br>"
                            "Time: %{x}<br>"
                            "Price: %{y:.5f}<br>"
                            "PnL: %{customdata:.2f}$<extra></extra>"
                        ),
                        customdata=sell_trades['profit_ac']
                    )
                )

    def show_plot(self, width=1480, height=650, line_traces=[]):
        self.add_traces(line_traces)
        self.update_layout(width = width, height = height)
        self.fig.show()
