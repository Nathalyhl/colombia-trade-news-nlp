"""Plot actual monthly observations, including isolated points and missingness."""
import math
from datetime import date, timedelta
import plotly.graph_objects as go

from .bank_method import trailing_quarterly_mean


def available(value):
    return value is not None and math.isfinite(value)


def index_chart(frame, column, title, bounds=None, focus_observed=False):
    records = frame.to_dict("records") if hasattr(frame, "to_dict") else frame
    values = [r.get(column) if available(r.get(column)) else None for r in records]
    months = [r["month"] for r in records]
    valid = [r["month"] for r, value in zip(records, values) if value is not None]
    clean_records = [{**r, column: value} for r, value in zip(records, values)]
    smooth = trailing_quarterly_mean(clean_records, column)
    fig = go.Figure()
    if valid:
        fig.add_trace(go.Scatter(x=months, y=values, mode="lines+markers", name="Monthly index value",
            line={"color": "#8a9ba8", "width": 1}, marker={"color": "#1e465e", "size": 8 if focus_observed else 4},
            connectgaps=False, customdata=[[r["articles"], r["publishers"], r["positive_count"], r["negative_count"], r["processed_tokens"]] for r in records],
            hovertemplate="%{x}<br>Index: %{y:.3f}<br>Articles: %{customdata[0]} · Sources: %{customdata[1]}<br>P: %{customdata[2]} · N: %{customdata[3]} · Words: %{customdata[4]}<extra></extra>"))
    else:
        fig.add_annotation(text="No monthly index values are available for this selection.", x=.5, y=.5,
                           xref="paper", yref="paper", showarrow=False)
    if any(available(v) for v in smooth):
        fig.add_trace(go.Scatter(x=months, y=smooth, mode="lines+markers", name="3-month moving average",
            line={"color": "#142330", "width": 2.5}, marker={"size": 4}, connectgaps=False))
    fig.update_layout(title=title, xaxis_title="Publication month", yaxis_title="Lexical balance" if column == "sentiment" else "Uncertainty words per 1,000",
        height=390, template="plotly_white", font={"family": "Georgia, serif", "color": "#182631"},
        paper_bgcolor="white", plot_bgcolor="white", legend={"orientation": "h", "y": -.30},
        margin={"l": 40, "r": 20, "t": 55, "b": 85})
    fig.update_xaxes(type="date", dtick="M3" if focus_observed else "M12", tickformat="%b %Y", showgrid=False)
    fig.update_yaxes(zeroline=False)
    if bounds:
        fig.update_yaxes(range=bounds)
    if focus_observed and valid:
        first, last = date.fromisoformat(min(valid)+"-01"), date.fromisoformat(max(valid)+"-01")
        fig.update_xaxes(range=[(first-timedelta(days=25)).isoformat(), (last+timedelta(days=40)).isoformat()])
    return fig
