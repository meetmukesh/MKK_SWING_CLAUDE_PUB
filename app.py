import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Elite Swing Watchlist Dashboard",
    layout="wide",
    page_icon="📈"
)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_summary():
    with open("watchlist_summary.json") as f:
        return json.load(f)

@st.cache_data
def load_watchlist_json():
    with open("watchlist_data.json") as f:
        data = json.load(f)
    df = pd.json_normalize(data.values(), sep=".")
    return df

@st.cache_data
def load_watchlist_csv():
    return pd.read_csv("watchlist_data.csv")

summary = load_summary()
df = load_watchlist_json()

# ---------------- HEADER ----------------
st.title("📈 Elite Swing Watchlist Dashboard")
st.caption(f"Last Updated: {summary['last_updated']}")

# ---------------- KPI CARDS ----------------
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Tracked", summary["total_tracked"])
k2.metric("Qualified", summary["qualified_count"])
k3.metric("Close to Qualified", summary["close_to_qualified"])
k4.metric("Avg Days on Watchlist", summary["avg_days_on_watchlist"])
k5.metric("Scan Timestamp", summary["last_updated"].split(" ")[1])

st.divider()

# ---------------- STAGE FUNNEL ----------------
st.subheader("🔄 Stage Funnel")

stage_dist = summary["stage_distribution"]
funnel_df = pd.DataFrame({
    "Stage": [k.replace("_", " ").title() for k in stage_dist.keys()],
    "Count": list(stage_dist.values())
})

funnel_fig = go.Figure(go.Funnel(
    y=funnel_df["Stage"],
    x=funnel_df["Count"],
    textinfo="value+percent initial"
))
funnel_fig.update_layout(height=400)

st.plotly_chart(funnel_fig, use_container_width=True)

# ---------------- SECTOR HEATMAP ----------------
st.subheader("🔥 Sector Heatmap")

sector_df = (
    df.groupby("metadata.sector")
    .agg(
        Total=("ticker", "count"),
        Qualified=("metrics.status", lambda x: (x == "QUALIFIED").sum())
    )
    .reset_index()
)

heatmap_fig = px.imshow(
    sector_df[["Total", "Qualified"]],
    labels=dict(x="Metric", y="Sector", color="Count"),
    y=sector_df["metadata.sector"],
    x=["Total", "Qualified"],
    color_continuous_scale="YlOrRd"
)

st.plotly_chart(heatmap_fig, use_container_width=True)

# ---------------- MARKET CAP BREAKDOWN ----------------
st.subheader("🏦 Market Cap Distribution")

mc_fig = px.pie(
    pd.DataFrame.from_dict(summary["market_cap_distribution"], orient="index", columns=["Count"]).reset_index(),
    names="index",
    values="Count",
    hole=0.4
)
st.plotly_chart(mc_fig, use_container_width=True)

# ---------------- ALERT FEED ----------------
st.subheader("🚨 Alert Feed")

alerts = df[df["metrics.status"] == "QUALIFIED"]

if alerts.empty:
    st.info("No new qualified stocks in this scan.")
else:
    for _, row in alerts.iterrows():
        st.success(
            f"✅ {row['ticker']} | Entry: {row['metrics.details.potential_entry']} | "
            f"Stop: {row['metrics.details.suggested_stop']} | "
            f"R:R {row['metrics.details.reward_risk_ratio']}"
        )

# ---------------- WATCHLIST TABLE ----------------
st.subheader("📋 Watchlist Table")

display_cols = [
    "ticker",
    "metadata.company_name",
    "metadata.sector",
    "stage",
    "metrics.price",
    "metrics.price_change_1d",
    "metrics.price_change_5d",
    "metrics.price_change_1m",
    "metrics.distance_from_52w_high",
    "metrics.details.rsi",
    "metrics.details.vol_contraction",
    "metrics.status"
]

table_df = df[display_cols].copy()

table_df.columns = [
    "Ticker", "Company", "Sector", "Stage", "Price",
    "1D %", "5D %", "1M %", "From 52W High %",
    "RSI", "VCP Contraction", "Status"
]

st.dataframe(
    table_df.sort_values(by=["Stage", "RSI"], ascending=[False, True]),
    use_container_width=True,
    height=450
)

# ---------------- FOOTER ----------------
st.caption("Elite Swing Scanner • Professional Trading Dashboard • Streamlit Cloud Ready")

