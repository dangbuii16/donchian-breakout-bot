import numpy as np
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots
from metrics.metrics import drawdown_stats, trade_returns

# Default chart layout
def apply_default_layout(fig, *, width=1300, height=700, showlegend=True):
    """ 
    Apply default layout to Plotly figure.
    """
    fig.update_layout(
        height=height, width=width,
        margin=dict(l=40, r=30, t=40, b=30),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(size=12, color="#0c0d11"),
        showlegend=showlegend
    )
    fig.update_xaxes(gridcolor='#f0f0f0')
    fig.update_yaxes(gridcolor='#f0f0f0')
    
    return fig

# Balance & Drawdown chart
def plot_equity_and_dd(balance_daily: pd.Series, dd_pct: pd.Series, title_equity="Account Balance (Daily)", title_dd="Drawdown (%)"):
    """ Plot equity curve and drawdown % chart.

    Arguments:
        balance_daily (pd.Series): Daily account balance.
        dd_pct (pd.Series): Daily drawdown percentage (<=0).
        title_equity (str): Title for equity chart.
        title_dd (str): Title for drawdown chart.
    Returns:
        fig (go.Figure): Plotly figure with subplots.
    """

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.10,
        row_heights=[0.6, 0.4],
        subplot_titles=(title_equity, title_dd)
    )
    fig.add_trace(go.Scatter(x=balance_daily.index, y=balance_daily.values, mode='lines', name='Balance'),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=dd_pct.index, y=dd_pct.values, mode='lines', name='Drawdown %', fill='tozeroy'),
                  row=2, col=1)

    fig.update_yaxes(title_text="USD", row=1, col=1, gridcolor="#f0f0f0")
    fig.update_yaxes(title_text="% (<=0)", row=2, col=1, gridcolor="#f0f0f0")
    return apply_default_layout(fig)


# Distribution of trade returns & Gross/Net by side
def plot_trade_distribution_and_side_pnl(trades):
    """ 
    Plot distribution of trade returns (%) and gross/net profit by side (Long/Short).
    
    Arguments:
        trades (pd.DataFrame): DataFrame containing trade data with 'side' and 'profit_ac' columns.
    """

    tr_ret_pct = trade_returns(trades, mode="pct")  # % per trade

    long_mask  = trades['side'].eq('BUY')
    short_mask = trades['side'].eq('SELL')

    gross_profit_long = float(trades.loc[ long_mask & (trades['profit_ac'] > 0), 'profit_ac'].sum())
    gross_loss_long   = float(trades.loc[ long_mask & (trades['profit_ac'] < 0), 'profit_ac'].sum())  # âm
    net_profit_long   = float(trades.loc[ long_mask, 'profit_ac'].sum())

    gross_profit_short = float(trades.loc[ short_mask & (trades['profit_ac'] > 0), 'profit_ac'].sum())
    gross_loss_short   = float(trades.loc[ short_mask & (trades['profit_ac'] < 0), 'profit_ac'].sum()) # âm
    net_profit_short   = float(trades.loc[ short_mask, 'profit_ac'].sum())

    cats = ['Long', 'Short']
    gp = [gross_profit_long, gross_profit_short]
    gl = [gross_loss_long,   gross_loss_short]   # giữ nguyên dấu âm
    npf= [net_profit_long,   net_profit_short]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Distribution of Trade Returns (%)", "Gross / Net Profit by Side"),
        column_widths=[0.55, 0.45]
    )

    # Left: histogram
    if not tr_ret_pct.empty:
        fig.add_trace(
            go.Histogram(
                x=tr_ret_pct.values, nbinsx=50, name="Trade % returns",
                marker_color="#00438F",
                hovertemplate="Return: %{x:.2f}%<br>Count: %{y}<extra></extra>"
            ),
            row=1, col=1
        )
        fig.add_vline(x=0, line_width=1, line_dash="dash", opacity=0.7, row=1, col=1)
        fig.add_vline(x=float(tr_ret_pct.mean()), line_width=2, line_dash="dot", opacity=0.8, row=1, col=1)
    else:
        fig.add_trace(go.Histogram(x=[]), row=1, col=1)

    # Right: bars
    fig.add_trace(go.Bar(x=cats, y=gp, name="Gross Profit",
                         marker_color="#24A06B",
                         hovertemplate="%{x}<br>$%{y:.2f}<extra></extra>"), row=1, col=2)
    fig.add_trace(go.Bar(x=cats, y=gl, name="Gross Loss",
                         marker_color="#CC2E3C",  
                         hovertemplate="%{x}<br>$%{y:.2f}<extra></extra>"), row=1, col=2)
    fig.add_trace(go.Bar(x=cats, y=npf, name="Net Profit",
                         marker_color="#FFA733",
                         hovertemplate="%{x}<br>$%{y:.2f}<extra></extra>"), row=1, col=2)

    fig.update_layout(barmode='group')
    fig.update_xaxes(gridcolor='#f0f0f0', row=1, col=1, title_text="Return per trade (%)")
    fig.update_yaxes(gridcolor='#f0f0f0', row=1, col=1, title_text="Frequency")
    fig.update_xaxes(gridcolor='#f0f0f0', row=1, col=2, title_text="Side")
    fig.update_yaxes(gridcolor='#f0f0f0', row=1, col=2, title_text="USD")

    return apply_default_layout(fig, height=520)
