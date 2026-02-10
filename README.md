# High-Throughput URL Shortener

A **read-optimized URL shortener** designed around real production bottlenecks seen in large-scale systems, not just basic CRUD APIs.

This project focuses on solving:
- Cache penetration from random requests
- Hot-key amplification during viral traffic
- Cold-start failures after service restarts
- Redis single-key bottlenecks

---

## Features

- **Bloom Filter–based existence check**
  - Prevents cache penetration
  - Rejects invalid short codes in O(1)
  - Memory-efficient probabilistic data structure

- **Multi-layer caching strategy**
  - Redis / Redis-compatible cache for fast reads
  - TTL-based eviction
  - In-process LRU cache as a fallback when Redis is unavailable

- **Hot-key detection**
  - Fixed time-window–based request counting
  - Prevents infinite counter growth
  - Identifies URLs experiencing burst traffic

- **Hot-key replication**
  - Replicates hot keys across multiple Redis keys
  - Randomized read distribution
  - Prevents single-key Redis bottlenecks
  - Supports horizontal read scaling

- **Cold-start safety**
  - Bloom Filter rebuilt from MongoDB on startup
  - Existing short URLs continue to work after restart

- **Persistent storage**
  - MongoDB as the source of truth
  - Collision-safe short code generation

- **Minimal Web UI**
  - Browser-based URL shortening
  - No terminal or API tools required

---

## Architecture Overview

Client
↓
FastAPI
↓
Bloom Filter (existence check)
↓
LRU Cache (in-process)
↓
Redis / Redis-compatible Cache
↓
MongoDB (source of truth)

For hot URLs, Redis reads are **replicated across multiple keys** to distribute load.

---

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Cache:** Redis / Memurai
- **In-memory Cache:** Custom LRU Cache
- **Probabilistic DS:** Bloom Filter
- **Frontend:** HTML + JavaScript
- **Load Testing:** Python (threading + requests)

---

## Run (Local)

### 1. Install dependencies
```bash
pip install -r requirements.txt
