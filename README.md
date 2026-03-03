# Content Pipeline

A modular, production-grade AI content generation pipeline that automatically discovers trending topics, scores and ranks ideas, generates 60-second video scripts via Claude, produces AI avatar videos using ElevenLabs and HeyGen, and publishes the final content to Instagram Reels and YouTube Shorts — all wired together as a clean, dependency-injected Python project.

## Prerequisites

- **Python 3.11+**
- **ffmpeg** binary installed and available on `PATH` (required for caption + music post-processing)
- **AWS credentials** configured (via env vars or `~/.aws/credentials`) with S3 read/write access
- API keys for: Reddit, Twitter/X, Anthropic, ElevenLabs, HeyGen, Instagram, YouTube

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd content-pipeline

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and fill in all required API keys and credentials
```

## Usage

```bash
# Full pipeline run (scrape → rank → script → video → publish)
python main.py --genre fitness

# Process top 3 ideas instead of the default 5
python main.py --genre tech --top-n 3

# Dry-run: scrape → rank → script only (no video production or publishing)
python main.py --genre personalfinance --top-n 2 --dry-run

# Other available genres
python main.py --genre food
python main.py --genre travel
```

## Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                     content-pipeline                            │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Stage 1  │    │ Stage 2  │    │ Stage 3  │                  │
│  │  Scrape  │───▶│   Rank   │───▶│ Generate │                  │
│  │          │    │          │    │  Script  │                  │
│  │ Reddit   │    │ Virality │    │          │                  │
│  │ Google   │    │ Novelty  │    │  Claude  │                  │
│  │ Twitter  │    │ Search   │    │  Sonnet  │                  │
│  └──────────┘    │ Hook     │    └────┬─────┘                  │
│                  └──────────┘         │                        │
│                                       ▼                        │
│                              ┌──────────────┐                  │
│                              │   Stage 4    │                  │
│                              │   Produce    │                  │
│                              │              │                  │
│                              │ ElevenLabs   │                  │
│                              │   TTS        │                  │
│                              │    +         │                  │
│                              │  HeyGen      │                  │
│                              │  Avatar      │                  │
│                              │    +         │                  │
│                              │  FFmpeg      │                  │
│                              └──────┬───────┘                  │
│                                     │                          │
│                                     ▼                          │
│                              ┌──────────────┐                  │
│                              │   Stage 5    │                  │
│                              │   Publish    │                  │
│                              │              │                  │
│                              │  Instagram   │                  │
│                              │   Reels      │                  │
│                              │    +         │                  │
│                              │   YouTube    │                  │
│                              │   Shorts     │                  │
│                              └──────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

## Module Reference

| Module | Description |
|---|---|
| `config.py` | Pydantic-settings nested config loaded from `.env` |
| `pipeline.py` | `ContentPipeline` — orchestrates all 5 stages |
| `main.py` | Click CLI entrypoint with Rich summary table |
| `models/` | Dataclasses: `TrendItem`, `RankedIdea`, `VideoScript`, `VideoAsset`, `PublishResult` |
| `scraper/` | Reddit (PRAW), Google Trends (pytrends), Twitter (Tweepy v2), Aggregator |
| `ranking/` | `NoveltyChecker` (difflib history), `Scorer` (weighted + Claude hook), `Ranker` |
| `generator/` | `PromptBuilder`, `ScriptValidator` (120–145 words), `ScriptWriter` with retry |
| `video/` | `TTSClient` (ElevenLabs), `AvatarClient` (HeyGen), `PostProcessor` (ffmpeg), `Producer` |
| `publisher/` | `InstagramPublisher` (Graph API v18), `YouTubePublisher` (Data API v3), `HashtagEngine`, `Scheduler` (Ayrshare) |
| `utils/` | `logger` (loguru), `http_client` (httpx), `retry` (exponential backoff), `storage` (S3) |

## Environment Variables

Copy `.env.example` to `.env` and fill in each value. Variables follow the `SERVICE__FIELD` pattern (double underscore as nested delimiter).

## Data Directory

The pipeline creates a `data/` directory to store `published_titles.json` — a novelty history used to avoid re-publishing duplicate topics.
