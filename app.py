import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sentiment import fetch_tweets, analyze_sentiment

st.set_page_config(
    page_title="Twitter Sentiment Analyzer",
    page_icon="🐦",
    layout="wide"
)

st.title("🐦 Twitter Sentiment Analyzer")
st.markdown("Analyze public sentiment on any topic using recent tweets.")

# --- Sidebar ---
with st.sidebar:
    st.header("Search Settings")
    query = st.text_input("Enter keyword or hashtag", placeholder="e.g. iPhone, AI, Tesla")
    num_tweets = st.slider("Number of tweets", min_value=10, max_value=100, value=50, step=10)
    search_btn = st.button("Analyze", use_container_width=True)

# --- Main ---
if search_btn and query:
    with st.spinner(f'Fetching tweets about "{query}"...'):
        try:
            tweets = fetch_tweets(query, max_results=num_tweets)
            if not tweets:
                st.warning("No tweets found. Try a different keyword.")
                st.stop()

            df = analyze_sentiment(tweets)

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            counts = df["sentiment"].value_counts()
            col1.metric("Total Tweets", len(df))
            col2.metric("Positive", counts.get("Positive", 0), delta=None)
            col3.metric("Neutral", counts.get("Neutral", 0), delta=None)
            col4.metric("Negative", counts.get("Negative", 0), delta=None)

            st.divider()

            # Charts
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.subheader("Sentiment Distribution")
                pie = px.pie(
                    df,
                    names="sentiment",
                    color="sentiment",
                    color_discrete_map={
                        "Positive": "#22c55e",
                        "Neutral": "#94a3b8",
                        "Negative": "#ef4444"
                    },
                    hole=0.4
                )
                pie.update_layout(margin=dict(t=0, b=0))
                st.plotly_chart(pie, use_container_width=True)

            with chart_col2:
                st.subheader("Sentiment Score Distribution")
                hist = px.histogram(
                    df,
                    x="score",
                    nbins=20,
                    color_discrete_sequence=["#6366f1"],
                    labels={"score": "Compound Score"}
                )
                hist.add_vline(x=0.05, line_dash="dash", line_color="green", annotation_text="Positive threshold")
                hist.add_vline(x=-0.05, line_dash="dash", line_color="red", annotation_text="Negative threshold")
                st.plotly_chart(hist, use_container_width=True)

            st.divider()

            # Tweet table
            st.subheader("Tweet Details")
            filter_col, _ = st.columns([1, 3])
            with filter_col:
                sentiment_filter = st.selectbox(
                    "Filter by sentiment",
                    ["All", "Positive", "Neutral", "Negative"]
                )

            display_df = df if sentiment_filter == "All" else df[df["sentiment"] == sentiment_filter]

            def color_sentiment(val):
                colors = {"Positive": "color: #22c55e", "Negative": "color: #ef4444", "Neutral": "color: #94a3b8"}
                return colors.get(val, "")

            styled = display_df[["text", "sentiment", "score"]].style.applymap(
                color_sentiment, subset=["sentiment"]
            )
            st.dataframe(styled, use_container_width=True, height=400)

            # Download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name=f"sentiment_{query.replace(' ', '_')}.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Error: {str(e)}")
            if "401" in str(e):
                st.info("Authentication failed. Please check your API keys in the .env file.")
            elif "403" in str(e):
                st.info("Access denied. Make sure your Twitter app has the correct permissions.")

elif search_btn and not query:
    st.warning("Please enter a keyword to search.")
else:
    st.info("Enter a keyword in the sidebar and click **Analyze** to get started.")
