"""
Reusable Plotly chart components for the CFL Sales Dashboard.
All charts follow a consistent style using config constants.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config import (
    LIFECYCLE_COLORS,
    SEGMENT_COLORS,
    TEAM_COLORS,
    PLOTLY_TEMPLATE,
    PLOTLY_FONT,
    PLOTLY_MARGIN,
)


def _base_layout(fig, title: str = "", height: int = 450):
    """Apply consistent layout to all charts."""
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        font=PLOTLY_FONT,
        title=dict(text=title, font=dict(size=16, color="#1a1a2e")),
        margin=dict(l=50, r=40, t=55, b=100),
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=10),
            itemwidth=30,
        ),
    )
    return fig


# ─── LINE CHARTS ─────────────────────────────────────────────

def line_chart_multi_product(df: pd.DataFrame, products: list, quarter_col: str = "Quarter",
                             value_col: str = "Units", product_col: str = "Product",
                             title: str = "Quarterly Trend", height: int = 420) -> go.Figure:
    """
    Multi-line chart for product trends over quarters.
    df should be in long format: Product, Quarter, Units
    """
    filtered = df[df[product_col].isin(products)].copy()
    # Truncate long product names for readable legends
    filtered["_legend"] = filtered[product_col].apply(lambda x: x[:28] + "…" if len(str(x)) > 28 else x)
    fig = px.line(
        filtered,
        x=quarter_col,
        y=value_col,
        color="_legend",
        markers=True,
        title=title,
        labels={"_legend": "Product"},
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
    fig.update_layout(xaxis=dict(tickangle=-30, tickfont=dict(size=10)))
    return _base_layout(fig, title, height)


def line_chart_segments(df: pd.DataFrame, product: str, title: str = "Segment Trends",
                        height: int = 420) -> go.Figure:
    """Line chart with one line per segment for a selected product."""
    filtered = df[df["Product"] == product]
    fig = px.line(
        filtered,
        x="Quarter",
        y="Units",
        color="Segment",
        markers=True,
        color_discrete_map=SEGMENT_COLORS,
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=5))
    return _base_layout(fig, title, height)


# ─── BAR CHARTS ──────────────────────────────────────────────

def horizontal_bar_lifecycle(df: pd.DataFrame, value_col: str, title: str = "Top Products",
                             top_n: int = 10, height: int = 420) -> go.Figure:
    """
    Horizontal bar chart of top products, color-coded by lifecycle.
    df must have columns: Product, Lifecycle, and <value_col>.
    """
    top = df.nlargest(top_n, value_col).copy()
    # Truncate long product names for y-axis readability
    top["Product_Short"] = top["Product"].apply(lambda x: x[:25] + "…" if len(str(x)) > 25 else x)
    fig = px.bar(
        top.sort_values(value_col),
        x=value_col,
        y="Product_Short",
        orientation="h",
        color="Lifecycle",
        color_discrete_map=LIFECYCLE_COLORS,
        title=title,
        labels={"Product_Short": "Product"},
    )
    fig.update_layout(
        yaxis=dict(tickfont=dict(size=9)),
        margin=dict(l=160, r=40, t=55, b=80),
    )
    return _base_layout(fig, title, height)


def grouped_bar_accuracy(df: pd.DataFrame, quarter: str = "FY26 Q1",
                         title: str = "Forecast Accuracy by Team",
                         height: int = 520) -> go.Figure:
    """
    Grouped bar chart: x = products, bars = teams, y = accuracy.
    df in long format: Product, Team, Quarter, Accuracy
    """
    filtered = df[df["Quarter"] == quarter].copy()
    # Abbreviate product names so they don't overlap on x-axis
    filtered["Product_Short"] = filtered["Product"].apply(
        lambda x: x[:15] + "…" if len(str(x)) > 15 else x
    )
    fig = px.bar(
        filtered,
        x="Product_Short",
        y="Accuracy",
        color="Team",
        barmode="group",
        color_discrete_map=TEAM_COLORS,
        title=title,
        labels={"Product_Short": "Product"},
    )
    fig.update_layout(
        xaxis=dict(tickangle=-45, tickfont=dict(size=8)),
        margin=dict(l=50, r=40, t=55, b=130),
    )
    fig.update_yaxes(range=[0, 1])
    return _base_layout(fig, title, height)


def stacked_bar_segments(df: pd.DataFrame, product: str,
                         title: str = "Units by Segment",
                         height: int = 420) -> go.Figure:
    """Stacked bar chart of segment breakdown per quarter for a product."""
    filtered = df[df["Product"] == product]
    fig = px.bar(
        filtered,
        x="Quarter",
        y="Units",
        color="Segment",
        barmode="stack",
        color_discrete_map=SEGMENT_COLORS,
        title=title,
    )
    fig.update_layout(xaxis=dict(tickangle=-30, tickfont=dict(size=10)))
    return _base_layout(fig, title, height)


def stacked_bar_100_pct(df: pd.DataFrame, product: str,
                        title: str = "Segment Share %",
                        height: int = 420) -> go.Figure:
    """100% stacked bar showing segment share percentage per quarter."""
    filtered = df[df["Product"] == product].copy()
    # Calculate share per quarter
    totals = filtered.groupby("Quarter")["Units"].transform("sum")
    filtered["Share"] = (filtered["Units"] / totals.replace(0, 1) * 100).round(1)

    fig = px.bar(
        filtered,
        x="Quarter",
        y="Share",
        color="Segment",
        barmode="stack",
        color_discrete_map=SEGMENT_COLORS,
        title=title,
    )
    fig.update_layout(xaxis=dict(tickangle=-30, tickfont=dict(size=10)))
    fig.update_yaxes(range=[0, 100], title="Share (%)")
    return _base_layout(fig, title, height)


def grouped_bar_big_deals(df: pd.DataFrame, product: str, n_quarters: int = 4,
                          title: str = "Big Deals vs Avg Deals",
                          height: int = 420) -> go.Figure:
    """Grouped bar for big deals vs avg deals for a product over recent quarters."""
    filtered = df[df["Product"] == product].tail(n_quarters)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=filtered["Quarter"], y=filtered["Big_Deals"],
        name="Big Deals", marker_color="#D85A30",
    ))
    fig.add_trace(go.Bar(
        x=filtered["Quarter"], y=filtered["Avg_Deals"],
        name="Avg Deals", marker_color="#378ADD",
    ))
    fig.update_layout(barmode="group")
    return _base_layout(fig, title, height)


# ─── DONUT / PIE CHARTS ─────────────────────────────────────

def donut_chart(labels: list, values: list, colors: dict = None,
                title: str = "Distribution", height: int = 380) -> go.Figure:
    """Donut chart with optional color mapping."""
    color_list = [colors.get(l, "#888780") for l in labels] if colors else None
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=color_list) if color_list else {},
        textinfo="percent",
        textposition="inside",
        textfont=dict(size=10, color="white"),
        insidetextorientation="horizontal",
        hoverinfo="label+percent+value",
    ))
    fig.update_layout(
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
        ),
        margin=dict(l=20, r=100, t=55, b=20),
    )
    return _base_layout(fig, title, height)


# ─── HEATMAP ─────────────────────────────────────────────────

def bias_heatmap(df: pd.DataFrame, title: str = "Forecast Bias Heatmap",
                 height: int = 700) -> go.Figure:
    """
    Heatmap: rows = products, columns = team × quarter, values = bias.
    df in long format: Product, Team, Quarter, Bias
    """
    df_copy = df.copy()
    # Shorten column labels: "Demand Planners — FY26 Q1" → "DP FY26Q1"
    team_abbrev = {
        "Demand Planners":    "DP",
        "Marketing Team":     "MKT",
        "Data Science Team":  "DS",
    }
    df_copy["Team_Quarter"] = (
        df_copy["Team"].map(team_abbrev).fillna(df_copy["Team"])
        + " " + df_copy["Quarter"].str.replace(" ", "")
    )
    # Truncate product names on y-axis
    df_copy["Product_Short"] = df_copy["Product"].apply(
        lambda x: x[:22] + "…" if len(str(x)) > 22 else x
    )
    pivot = df_copy.pivot_table(
        index="Product_Short", columns="Team_Quarter", values="Bias", aggfunc="first"
    )

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, "#E24B4A"],
            [0.5, "#FFFFFF"],
            [1.0, "#1D9E75"],
        ],
        zmid=0,
        text=pivot.values.round(3),
        texttemplate="%{text:.3f}",
        textfont=dict(size=9),
        colorbar=dict(title="Bias", tickformat=".2f"),
    ))
    fig.update_layout(
        xaxis=dict(tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=9), autorange="reversed"),
        margin=dict(l=190, r=60, t=55, b=80),
    )
    return _base_layout(fig, title, height)


# ─── SCATTER / BUBBLE ────────────────────────────────────────

def scatter_accuracy_volume(accuracy_df: pd.DataFrame, actuals_df: pd.DataFrame,
                            quarter: str = "FY26 Q1",
                            title: str = "Accuracy vs Volume",
                            height: int = 450) -> go.Figure:
    """
    Scatter: x = actual units, y = accuracy, size = abs(bias), color = team.
    """
    acc = accuracy_df[accuracy_df["Quarter"] == quarter].copy()
    # Map FY quarter to latest actual column
    if not actuals_df.empty and quarter in actuals_df.columns:
        units_map = actuals_df.set_index("Product")[quarter].to_dict()
    else:
        # Try the last column
        last_col = [c for c in actuals_df.columns if c != "Product"][-1] if len(actuals_df.columns) > 1 else None
        units_map = actuals_df.set_index("Product")[last_col].to_dict() if last_col else {}

    acc["Actual_Units"] = acc["Product"].map(units_map).fillna(0)
    acc["Abs_Bias"] = acc["Bias"].abs() * 100 + 5  # Scale for bubble size

    fig = px.scatter(
        acc,
        x="Actual_Units",
        y="Accuracy",
        size="Abs_Bias",
        color="Team",
        color_discrete_map=TEAM_COLORS,
        hover_name="Product",
        title=title,
        size_max=30,
    )
    fig.update_yaxes(range=[0, 1.05])
    return _base_layout(fig, title, height)


# ─── TREEMAP ─────────────────────────────────────────────────

def treemap_verticals(df: pd.DataFrame, product: str, quarter: str,
                      title: str = "Vertical Distribution",
                      height: int = 500) -> go.Figure:
    """Treemap of verticals for a product in a specific quarter."""
    filtered = df[(df["Product"] == product) & (df["Quarter"] == quarter) & (df["Units"] > 0)]
    if filtered.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return _base_layout(fig, title, height)

    fig = px.treemap(
        filtered,
        path=["Vertical"],
        values="Units",
        color="Units",
        color_continuous_scale="Tealgrn",
        title=title,
    )
    fig.update_traces(textinfo="label+value+percent root", textfont=dict(size=12))
    return _base_layout(fig, title, height)


# ─── BIG DEAL SPECIFIC ──────────────────────────────────────

def big_deal_pct_line(df: pd.DataFrame, products: list = None,
                      title: str = "Big Deal % of Total Bookings",
                      height: int = 420) -> go.Figure:
    """Line chart showing big deal percentage of total over time."""
    df_copy = df.copy()
    total = df_copy["MFG_Units"].replace(0, 1)
    df_copy["Big_Deal_Pct"] = (df_copy["Big_Deals"] / total * 100).round(1)

    if products:
        df_copy = df_copy[df_copy["Product"].isin(products)]

    # Truncate long product names for readable legends
    df_copy["_legend"] = df_copy["Product"].apply(lambda x: x[:25] + "…" if len(str(x)) > 25 else x)
    fig = px.line(
        df_copy,
        x="Quarter",
        y="Big_Deal_Pct",
        color="_legend",
        markers=True,
        title=title,
        labels={"_legend": "Product"},
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=5))
    fig.update_yaxes(title="Big Deal %")
    fig.update_layout(xaxis=dict(tickangle=-30, tickfont=dict(size=10)))
    return _base_layout(fig, title, height)


def big_deal_dependency_bar(df: pd.DataFrame, title: str = "Big Deal Dependency",
                            height: int = 450) -> go.Figure:
    """Stacked bar showing big vs avg deal split, highlighting dependent products."""
    # Aggregate across quarters
    agg = df.groupby("Product")[["Big_Deals", "Avg_Deals"]].sum().reset_index()
    agg["Total"] = agg["Big_Deals"] + agg["Avg_Deals"]
    agg["Big_Pct"] = (agg["Big_Deals"] / agg["Total"].replace(0, 1) * 100).round(1)
    agg = agg.sort_values("Big_Pct", ascending=True)
    # Truncate long product names
    agg["Product_Short"] = agg["Product"].apply(lambda x: x[:25] + "…" if len(str(x)) > 25 else x)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=agg["Product_Short"], x=agg["Big_Deals"], name="Big Deals",
        orientation="h", marker_color="#D85A30",
    ))
    fig.add_trace(go.Bar(
        y=agg["Product_Short"], x=agg["Avg_Deals"], name="Avg Deals",
        orientation="h", marker_color="#378ADD",
    ))
    fig.update_layout(
        barmode="stack",
        yaxis=dict(tickfont=dict(size=9)),
        margin=dict(l=160, r=40, t=55, b=80),
    )

    # Add threshold line at 15%
    for i, row in agg.iterrows():
        if row["Big_Pct"] > 15:
            fig.add_annotation(
                x=row["Total"], y=row["Product_Short"],
                text=f"⚠️ {row['Big_Pct']:.0f}%",
                showarrow=False, xanchor="left", font=dict(size=9, color="#E24B4A"),
            )

    return _base_layout(fig, title, height)
