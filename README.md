# Twitter Real-Time Sentiment Analysis

A production-grade sentiment analysis pipeline that streams tweets in real time, classifies them using BERT, stores results in MongoDB, and displays live insights on an interactive dashboard.

---

## Architecture

```
Twitter API
    │
    ▼
┌─────────────┐      ┌───────────────┐      ┌──────────────┐
│   Producer  │─────▶│  Apache Kafka │─────▶│   Consumer   │
│  (Tweepy)   │      │  (tweets topic│      │ (BERT model) │
└─────────────┘      └───────────────┘      └──────┬───────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │    MongoDB       │
                                          │  (sentiment_db)  │
                                          └────────┬────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │   Dashboard      │
                                          │  (Streamlit +    │
                                          │   Plotly)        │
                                          └─────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Data ingestion | Python · Tweepy · Twitter API v2 |
| Message broker | Apache Kafka |
| NLP model | BERT (`twitter-roberta-base-sentiment`) |
| Database | MongoDB |
| Dashboard | Streamlit · Plotly |
| Containers | Docker · Docker Compose |
| Orchestration | Kubernetes |

---

## Project Structure

```
Sentiment Analysis/
├── producer/
│   ├── producer.py        # Fetch tweets → publish to Kafka
│   ├── requirements.txt
│   └── Dockerfile
├── consumer/
│   ├── consumer.py        # Kafka → BERT → MongoDB
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/
│   ├── app.py             # Streamlit + Plotly dashboard
│   ├── requirements.txt
│   └── Dockerfile
├── k8s/
│   ├── namespace.yaml
│   ├── secrets.yaml
│   ├── zookeeper.yaml
│   ├── kafka.yaml
│   ├── mongodb.yaml
│   ├── producer.yaml
│   ├── consumer.yaml
│   └── dashboard.yaml
├── docker-compose.yml
├── .env                   # API keys — never commit
└── .gitignore
```

---

## Quick Start (Docker)

### 1. Configure `.env`

```
TWITTER_API_KEY=your_consumer_key
TWITTER_API_SECRET=your_consumer_secret
TWITTER_BEARER_TOKEN=your_bearer_token   # optional — auto-fetched if blank
SEARCH_QUERY=AI
```

### 2. Build and run

```bash
docker compose up --build
```

Open [http://localhost:8501](http://localhost:8501)

### 3. Stop

```bash
docker compose down
```

---

## Kubernetes Deployment

### 1. Build images

```bash
docker build -t sentiment-producer:latest ./producer
docker build -t sentiment-consumer:latest ./consumer
docker build -t sentiment-dashboard:latest ./dashboard
```

### 2. Fill in secrets

Edit `k8s/secrets.yaml` with your Twitter API keys.

### 3. Deploy

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/zookeeper.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/mongodb.yaml
kubectl apply -f k8s/producer.yaml
kubectl apply -f k8s/consumer.yaml
kubectl apply -f k8s/dashboard.yaml
```

### 4. Access dashboard

```bash
kubectl port-forward svc/dashboard 8501:8501 -n sentiment
```

Open [http://localhost:8501](http://localhost:8501)

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SEARCH_QUERY` | `AI` | Keyword or hashtag to track |
| `POLL_INTERVAL_SECONDS` | `30` | How often to fetch new tweets |
| `MAX_RESULTS` | `50` | Tweets per poll (max 100 on free tier) |
| `KAFKA_TOPIC` | `tweets` | Kafka topic name |
| `MONGO_DB` | `sentiment_db` | MongoDB database name |

---

## Notes

- BERT model downloads automatically on first consumer startup (~500MB)
- Free Twitter API allows up to 500,000 tweets/month, last 7 days only
- Consumer runs 2 replicas in Kubernetes for parallel BERT inference
- `.env` is excluded from git — never commit API keys
