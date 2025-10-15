import warnings

# Override showwarning to drop every warning
warnings.showwarning = lambda *args, **kwargs: None
import warnings
warnings.filterwarnings("ignore", "I don''t know how to infer vegalite type")
import warnings
warnings.filterwarnings("ignore", "I don''t know how to infer vegalite type")
import os
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
    path = "codex_ledger.json"
    # if file is missing or empty, return empty DataFrame
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        return pd.DataFrame(columns=["timestamp", "delta", "author"])
    try:
        # if your ledger is JSON lines, add lines=True
        return pd.read_json(path)
    except ValueError:
        return pd.DataFrame(columns=["timestamp", "delta", "author"])

df = load_ledger()

# Top-line metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Stones", len(df))
c2.metric("Average Δ", round(df["delta"].mean(), 2))
c3.metric("Unique Authors", df["author"].nunique())
c4.metric("Last Updated", df["timestamp"].max())

# Chain growth over time
st.subheader("Chain Growth")
growth = df.groupby("timestamp").size().cumsum().reset_index(name="count")
st.line_chart(
    growth.rename(columns={"timestamp": "index"}).set_index("index")["count"]
)

# Entries per hour histogram
st.subheader("Entries per Hour")
if "timestamp" in df.columns:
    df["hour"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.hour
    st.bar_chart(df["hour"].value_counts().sort_index())
else:
    st.write("No timestamp data to plot.")

# Author distribution pie chart
st.subheader("Author Distribution")
if not df.empty:
    fig = px.pie(df, names="author", title="Stones by Author")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("No stones yet.")

# Latest stones table
st.subheader("Latest 10 Stones")
if not df.empty:
    st.table(df.sort_values("timestamp", ascending=False).head(10))
else:
    st.write("Ledger is empty.")
