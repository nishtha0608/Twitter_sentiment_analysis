import os
import json
import time
import logging
from datetime import datetime, timezone
from kafka import KafkaConsumer
from pymongo import MongoClient
from transformers import pipeline

load_dotenv = None
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CONSUMER] %(message)s")

KAFKA_BROKER  = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC   = os.getenv("KAFKA_TOPIC", "tweets")
MONGO_URI     = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
MONGO_DB      = os.getenv("MONGO_DB", "sentiment_db")
MONGO_COL     = os.getenv("MONGO_COLLECTION", "tweets")
BERT_MODEL    = "cardiffnlp/twitter-roberta-base-sentiment-latest"

LABEL_MAP = {"negative": "Negative", "neutral": "Neutral", "positive": "Positive"}


def build_consumer() -> KafkaConsumer:
    for attempt in range(15):
        try:
            return KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BROKER,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                group_id="bert-sentiment-group",
            )
        except Exception as e:
            logging.warning(f"Kafka not ready ({e}), retry {attempt+1}/15 in 5s…")
            time.sleep(5)
    raise RuntimeError("Could not connect to Kafka")


def main():
    logging.info("Loading BERT model…")
    sentiment_pipe = pipeline(
        "sentiment-analysis",
        model=BERT_MODEL,
        top_k=None,
    )
    logging.info("BERT model loaded.")

    mongo  = MongoClient(MONGO_URI)
    col    = mongo[MONGO_DB][MONGO_COL]
    col.create_index("tweet_id", unique=True)

    consumer = build_consumer()
    logging.info(f"Consuming from topic '{KAFKA_TOPIC}'…")

    for message in consumer:
        tweet = message.value
        try:
            text    = tweet["text"][:512]
            results = sentiment_pipe(text)[0]

            best    = max(results, key=lambda x: x["score"])
            label   = LABEL_MAP.get(best["label"].lower(), best["label"])
            scores  = {LABEL_MAP.get(r["label"].lower(), r["label"]): round(r["score"], 4) for r in results}

            doc = {
                "tweet_id":   tweet["id"],
                "text":       tweet["text"],
                "author_id":  tweet.get("author_id"),
                "query":      tweet.get("query"),
                "created_at": tweet.get("created_at"),
                "sentiment":  label,
                "scores":     scores,
                "confidence": round(best["score"], 4),
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "metrics":    tweet.get("metrics", {}),
            }

            col.update_one({"tweet_id": doc["tweet_id"]}, {"$set": doc}, upsert=True)
            logging.info(f"[{label}] ({best['score']:.2f}) {text[:80]}…")

        except Exception as e:
            logging.error(f"Failed to process tweet: {e}")


if __name__ == "__main__":
    main()