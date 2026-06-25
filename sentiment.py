import os
import base64
import requests
import tweepy
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

load_dotenv()

def _fetch_bearer_token(api_key: str, api_secret: str) -> str:
    credentials = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    resp = requests.post(
        "https://api.twitter.com/oauth2/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        data="grant_type=client_credentials",
    )
    if resp.status_code != 200:
        raise ValueError(f"Failed to get Bearer Token: {resp.status_code} {resp.text}")
    return resp.json()["access_token"]

def get_twitter_client():
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    if not api_key or not api_secret:
        raise ValueError("TWITTER_API_KEY and TWITTER_API_SECRET must be set in .env")

    if not bearer_token:
        bearer_token = _fetch_bearer_token(api_key, api_secret)

    return tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)

def fetch_tweets(query: str, max_results: int = 100):
    client = get_twitter_client()
    full_query = f"{query} -is:retweet lang:en"
    response = client.search_recent_tweets(
        query=full_query,
        max_results=min(max_results, 100),
        tweet_fields=["created_at", "text", "public_metrics"],
    )
    if not response.data:
        return []
    return response.data

def analyze_sentiment(tweets):
    analyzer = SentimentIntensityAnalyzer()
    results = []
    for tweet in tweets:
        score = analyzer.polarity_scores(tweet.text)
        compound = score["compound"]
        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"
        results.append({
            "text": tweet.text,
            "sentiment": label,
            "score": round(compound, 4),
            "positive": round(score["pos"], 4),
            "negative": round(score["neg"], 4),
            "neutral": round(score["neu"], 4),
            "created_at": tweet.created_at,
        })
    return pd.DataFrame(results)