import pandas as pd
from datetime import datetime
from typing import Iterable, Dict, Tuple, Union, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from backtest.runner_v2 import run_backtest_for_symbol as run_backtest_for_symbol_v2
from exporation.plotting_utils import apply_default_layout

def grind_search_parameters(
    pairs: Union[str, Iterable[str]],
    timeframe,
    start_date: datetime,
    end_date: datetime,
    lookbacks: Iterable[int],
    initial_capital: float,
    risk_per_trade: float = 0.01,
    risk_mode: str = "FIXED_AMOUNT",
    commission_per_lot: float = 0.0,
    backtest_fn = run_backtest_for_symbol_v2,
    plot_charts: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, go.Figure]]:
    
    """ 
    Grind search for optimal Donchian lookback parameters across multiple trading pairs.
    """

    if isinstance(pairs, str):
        pairs = [pairs]
    pairs = list(pairs)

    def extract_metrics(report_df: pd.DataFrame):
        """Get Sharpe / PF / Max DD (%) an toàn theo tên cột."""
        sharpe = float(report_df["Sharpe ratio"].iloc[0])
        pf     = float(report_df["Profit factor"].iloc[0])
        dd     = float(report_df["Max DD (%)"].iloc[0]) / 100.0

        return sharpe, pf, dd
    
    grind_research = []
    for pair in pairs:
        for lb in lookbacks:
            res = backtest_fn(
                pair=pair,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                risk_per_trade=risk_per_trade,
                risk_mode=risk_mode,
                commission_per_lot=commission_per_lot,
                lookback=lb
            )
            rpt = res["report_df"]
            sharpe, pf, dd = extract_metrics(rpt)
            grind_research.append({
                "pair": pair, "lookback": lb,
                "sharpe": sharpe, "profit_factor": pf, "max_dd_pct": dd
            })

    grind_df = pd.DataFrame(grind_research).set_index(["pair", "lookback"]).sort_index()

    figs: Dict[str, go.Figure] = {}
    if plot_charts:
        for pair in pairs:
            df_plot = grind_df.loc[pair].copy()
            if df_plot[["profit_factor", "sharpe", "max_dd_pct"]].isna().all(axis=None):
                continue

            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.12,
                row_heights=[0.6, 0.4],
                specs=[[{"secondary_y": True}],
                       [{"secondary_y": False}]]
            )

            # Row 1: PF (left) + Sharpe (right)
            if df_plot["profit_factor"].notna().any():
                fig.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot["profit_factor"],
                               mode="lines+markers", name="Profit Factor"),
                    row=1, col=1, secondary_y=False
                )
                fig.add_hline(y=1.0, line_width=1, line_color="#000000", opacity=0.6, row=1, col=1)

            if df_plot["sharpe"].notna().any():
                fig.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot["sharpe"],
                               mode="lines+markers", name="Sharpe"),
                    row=1, col=1, secondary_y=True
                )
            
            # Row 2: Max DD (%)
            if df_plot["max_dd_pct"].notna().any():
                fig.add_trace(
                    go.Bar(x=df_plot.index, y=df_plot["max_dd_pct"],
                           name="Max DD (%)", opacity=0.85),
                    row=2, col=1
                )
                fig.add_hline(y=0.0, line_width=1, line_color="#999999", opacity=0.6, row=2, col=1)

            # Axes & layout
            fig.update_xaxes(title_text="Lookback", gridcolor="#f0f0f0", row=2, col=1)
            fig.update_yaxes(title_text="Profit Factor", tickformat=".2f", row=1, col=1, gridcolor="#f0f0f0",secondary_y=False)
            fig.update_yaxes(title_text="Sharpe", tickformat=".2f", row=1, col=1, gridcolor="#f0f0f0", secondary_y=True)
            fig.update_yaxes(title_text="Max DD (%)", tickformat=".0%", row=2, col=1, gridcolor="#f0f0f0")

            fig.update_layout(
                title=f"Donchian Breakout Lookback optimization - {pair}",
                barmode="relative",
                showlegend=True
            )

            fig = apply_default_layout(fig)
            figs[pair] = fig

    return grind_df, figs