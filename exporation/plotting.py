import datetime as dt
import plotly.graph_objects as go

class CandlePlot:

    def __init__(self, df, candles=True) -> None:
        self.df_plot = df.copy()
        self.candles = candles
        self.create_candle_fig()

    def create_candle_fig(self):
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
        for line in line_traces:
            self.fig.add_trace(go.Scatter(
                x=self.df_plot['time'],
                y=self.df_plot[line],
                line=dict(width=2),
                line_shape='spline',
                name=line
            ))

    def show_plot(self, width=1480, height=650, line_traces=[]):
        self.add_traces(line_traces)
        self.update_layout(width = width, height = height)
        self.fig.show()
