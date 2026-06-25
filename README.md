# Twitter Sentiment Analyzer

A web app that fetches real-time tweets and analyzes their sentiment using VADER NLP. Built with Python, Tweepy, and Streamlit.

---

## Features

- Search any keyword or hashtag on X (Twitter)
- Classifies tweets as Positive, Neutral, or Negative
- Interactive pie chart and score distribution histogram
- Filter tweets by sentiment
- Download results as CSV

---

## Project Structure

```
Sentiment Analysis/
├── app.py              # Streamlit web app
├── sentiment.py        # Tweet fetching + sentiment logic
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Docker Compose config
├── .env                # API keys (never commit this)
└── .gitignore
```

---

## Setup

### 1. Get Twitter API Keys

1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Create an app and get your **Consumer Key**, **Consumer Secret**, and **Bearer Token**

### 2. Configure `.env`

```
TWITTER_API_KEY=your_consumer_key
TWITTER_API_SECRET=your_consumer_secret
TWITTER_BEARER_TOKEN=your_bearer_token
```

---

## Running Locally

```bash
pip3 install -r requirements.txt
python3 -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

---

## Running with Docker

### Build and start

```bash
docker compose up --build
```

### Stop

```bash
docker compose down
```

Open [http://localhost:8501](http://localhost:8501)

> Make sure Docker Desktop is running before executing these commands.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| [Tweepy](https://www.tweepy.org/) | Twitter API client |
| [VADER](https://github.com/cjhutto/vaderSentiment) | Sentiment analysis |
| [Streamlit](https://streamlit.io/) | Web UI |
| [Plotly](https://plotly.com/) | Interactive charts |
| [pandas](https://pandas.pydata.org/) | Data handling |

---

## Notes

- Free Twitter API tier allows up to **500,000 tweets/month**
- Only **recent tweets (last 7 days)** are available on the free tier
- Never commit your `.env` file — it contains secret API keys