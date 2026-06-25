import os
import json
import time
import base64
import logging
import requests
import tweepy
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [PRODUCER] %(message)s")

KAFKA_BROKER   = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC    = os.getenv("KAFKA_TOPIC", "tweets")
SEARCH_QUERY   = os.getenv("SEARCH_QUERY", "AI")
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
MAX_RESULTS    = int(os.getenv("MAX_RESULTS", "50"))


def get_bearer_token() -> str:
    token = os.getenv("TWITTER_BEARER_TOKEN")
    if token:
        return token
    key    = os.getenv("TWITTER_API_KEY")
    secret = os.getenv("TWITTER_API_SECRET")
    creds  = base64.b64encode(f"{key}:{secret}".encode()).decode()
    resp   = requests.post(
        "https://api.twitter.com/oauth2/token",
        headers={"Authorization": f"Basic {creds}",
                 "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        data="grant_type=client_credentials",
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def build_producer() -> KafkaProducer:
    for attempt in range(10):
        try:
            return KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except Exception as e:
            logging.warning(f"Kafka not ready ({e}), retry {attempt+1}/10 in 5s…")
            time.sleep(5)
    raise RuntimeError("Could not connect to Kafka after 10 retries")


def fetch_and_publish(client: tweepy.Client, producer: KafkaProducer, seen_ids: set):
    query    = f"{SEARCH_QUERY} -is:retweet lang:en"
    response = client.search_recent_tweets(
        query=query,
        max_results=MAX_RESULTS,
        tweet_fields=["created_at", "text", "public_metrics", "author_id"],
    )
    if not response.data:
        logging.info("No new tweets found.")
        return

    new_count = 0
    for tweet in response.data:
        if tweet.id in seen_ids:
            continue
        seen_ids.add(tweet.id)
        payload = {
            "id":         str(tweet.id),
            "text":       tweet.text,
            "created_at": str(tweet.created_at),
            "author_id":  str(tweet.author_id),
            "metrics":    tweet.public_metrics,
            "query":      SEARCH_QUERY,
        }
        producer.send(KAFKA_TOPIC, value=payload)
        new_count += 1

    producer.flush()
    logging.info(f"Published {new_count} new tweets to topic '{KAFKA_TOPIC}'")


def main():
    bearer  = get_bearer_token()
    client  = tweepy.Client(bearer_token=bearer, wait_on_rate_limit=True)
    prod    = build_producer()
    seen    = set()

    logging.info(f"Streaming tweets for query: '{SEARCH_QUERY}'")
    while True:
        try:
            fetch_and_publish(client, prod, seen)
        except Exception as e:
            logging.error(f"Error fetching tweets: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()