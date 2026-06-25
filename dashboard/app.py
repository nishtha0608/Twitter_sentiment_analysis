import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MONGO_URI  = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
MONGO_DB   = os.getenv("MONGO_DB", "sentiment_db")
MONGO_COL  = os.getenv("MONGO_COLLECTION", "tweets")

COLORS = {"Positive": "#22c55e", "Neutral": "#94a3b8", "Negative": "#ef4444"}

st.set_page_config(page_title="Sentiment Dashboard", page_icon="📊", layout="wide")

@st.cache_resource
def get_collection():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB][MONGO_COL]

def load_data(query_filter: str, hours: int) -> pd.DataFrame:
    col   = get_collection()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    filt  = {"processed_at": {"$gte": since}}
    if query_filter != "All":
        filt["query"] = query_filter
    docs = list(col.find(filt, {"_id": 0}).sort("processed_at", -1).limit(2000))
    return pd.DataFrame(docs) if docs else pd.DataFrame()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Real-Time Twitter Sentiment Dashboard")
st.caption("Powered by BERT · Apache Kafka · MongoDB")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    col_obj  = get_collection()
    queries  = ["All"] + col_obj.distinct("query")
    topic    = st.selectbox("Topic", queries)
    hours    = st.slider("Time window (hours)", 1, 72, 24)
    auto_ref = st.toggle("Auto-refresh (30s)", value=True)
    if auto_ref:
        st.caption("Dashboard refreshes every 30 seconds")

if auto_ref:
    st.markdown(
        '<meta http-equiv="refresh" content="30">',
        unsafe_allow_html=True,
    )

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_data(topic, hours)

if df.empty:
    st.info("No data yet. The Kafka producer is fetching tweets — check back in a moment.")
    st.stop()

# ── KPI strip ─────────────────────────────────────────────────────────────────
counts   = df["sentiment"].value_counts()
pos_pct  = round(counts.get("Positive", 0) / len(df) * 100, 1)
neg_pct  = round(counts.get("Negative", 0) / len(df) * 100, 1)
avg_conf = round(df["confidence"].mean() * 100, 1)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Tweets",  len(df))
k2.metric("Positive",  counts.get("Positive", 0),  f"{pos_pct}%")
k3.metric("Neutral",   counts.get("Neutral", 0))
k4.metric("Negative",  counts.get("Negative", 0),  f"-{neg_pct}%")
k5.metric("Avg Confidence", f"{avg_conf}%")

st.divider()

# ── Row 1: Pie + Confidence bar ────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Sentiment Breakdown")
    pie = px.pie(
        df, names="sentiment",
        color="sentiment",
        color_discrete_map=COLORS,
        hole=0.45,
    )
    pie.update_traces(textinfo="percent+label")
    pie.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(pie, use_container_width=True)

with c2:
    st.subheader("Confidence Distribution by Sentiment")
    box = px.box(
        df, x="sentiment", y="confidence",
        color="sentiment",
        color_discrete_map=COLORS,
        labels={"confidence": "BERT Confidence", "sentiment": ""},
    )
    box.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(box, use_container_width=True)

# ── Row 2: Timeline ───────────────────────────────────────────────────────────
st.subheader("Sentiment Over Time")

if "processed_at" in df.columns:
    df["time"] = pd.to_datetime(df["processed_at"], errors="coerce", utc=True)
    timeline   = (
        df.dropna(subset=["time"])
        .set_index("time")
        .groupby([pd.Grouper(freq="1h"), "sentiment"])
        .size()
        .reset_index(name="count")
    )
    if not timeline.empty:
        line = px.line(
            timeline, x="time", y="count",
            color="sentiment",
            color_discrete_map=COLORS,
            markers=True,
            labels={"time": "Hour", "count": "Tweets", "sentiment": ""},
        )
        st.plotly_chart(line, use_container_width=True)

# ── Row 3: Tweet table ────────────────────────────────────────────────────────
st.subheader("Recent Tweets")
sent_filter = st.radio("Filter", ["All", "Positive", "Neutral", "Negative"], horizontal=True)
view = df if sent_filter == "All" else df[df["sentiment"] == sent_filter]

display = view[["text", "sentiment", "confidence", "query", "processed_at"]].head(100)
display.columns = ["Tweet", "Sentiment", "Confidence", "Topic", "Processed At"]

def highlight(row):
    c = COLORS.get(row["Sentiment"], "")
    return [f"color: {c}" if col == "Sentiment" else "" for col in row.index]

st.dataframe(display.style.apply(highlight, axis=1), use_container_width=True, height=400)

csv = view.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", csv, file_name="sentiment_results.csv", mime="text/csv")