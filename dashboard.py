import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# Auto‐refresh every 5 seconds
st_autorefresh(interval=5000, key="refresh")

st.set_page_config(page_title="Codex Dashboard", layout="wide")
st.title("🔮 Codex Web Real-Time Dashboard")

@st.cache_data
def load_ledger():
    return pd.read_json("codex_ledger.json")

df = load_ledger()

# Top-line metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stones", len(df))
col2.metric("Average Δ", round(df["delta"].mean(), 2))
col3.metric("Unique Authors", df["author"].nunique())
col4.metric("Last Updated", df["timestamp"].max())

# Chain growth over time
st.subheader("Chain Growth")
growth = df.groupby("timestamp").size().cumsum().reset_index(name="count")
st.line_chart(
    growth
    .rename(columns={"timestamp": "index"})
    .set_index("index")["count"]
)

# Entry frequency histogram
st.subheader("Entries per Hour")
df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
st.bar_chart(df["hour"].value_counts().sort_index())

# Author distribution pie chart
st.subheader("Author Distribution")
fig = px.pie(df, names="author", title="Stones by Author")
st.plotly_chart(fig, use_container_width=True)

# Latest 10 stones table
st.subheader("Latest 10 Stones")
st.table(
    df
    .sort_values("timestamp", ascending=False)
    .head(10)
)
