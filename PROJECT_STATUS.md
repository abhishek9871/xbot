# XBot Project - Complete Handover Documentation

**Last Updated:** January 4, 2026  
**Version:** v8.0 (Million Visitor Engine)  
**Primary Goal:** Drive 1M+ unique visitors to `streamixapp.pages.dev` by targeting movie/TV show lovers on X.com (Twitter).

---

## 🎯 Project Overview

XBot is an autonomous X.com (Twitter) bot that:
1. Searches for tweets from people discussing movies, TV shows, and streaming
2. Generates curiosity-driven replies that mention `streamixapp.pages.dev`
3. Uses AI to create varied, high-value search terms
4. Replies with question-based messages to encourage clicks

**Target Audience:** Movie lovers, TV show enthusiasts, anime fans, K-drama watchers, people frustrated with streaming costs.

---

## 🏗️ Architecture (Hybrid Brain-Body)

### 1. The Brain (Server) - `server.py`
- **Stack:** Python 3.13, FastAPI, Uvicorn, SQLite, Groq Cloud API (LLM)
- **Port:** `http://localhost:8000`
- **Key Features:**
  - AI-powered search term generation using Groq LLM
  - LLM-based tweet analysis and reply drafting
  - SQLite database for tracking replied tweets and search terms
  - TMDB integration for trending movie data

### 2. The Body (Client) - `xbot_client.js`
- **Stack:** JavaScript (Tampermonkey Userscript)
- **Key Features:**
  - DOM manipulation on X.com (scroll, click, type)
  - Tweet scanning and candidate filtering
  - Reply posting with human-like delays
  - Exhaustion-based search term rotation

---

## ✅ Implemented Features (What We Built)

### 1. AI-Powered Search Term Generator
**Location:** `server.py` → `SmartSearch.generate_ai_search_terms()`

The AI generates **50 unique search terms** every 30 minutes covering:

| Category | Examples |
|----------|----------|
| Movies 2025 | "best movies 2025", "top movies 2025" |
| TV Shows 2025 | "best tv shows 2025", "new series 2025" |
| Award Season | "Oscar nominations", "Golden Globe winners" |
| Genres | "best horror movies 2025", "top thriller movies" |
| Franchises | "Marvel movies", "Star Wars movies", "Harry Potter series" |
| K-Drama/International | "best kdrama 2025", "korean drama recommendations" |
| Anime | "best anime 2025", "anime recommendations" |
| Moods/Emotions | "feel good movies", "date night movies" |
| Streaming News | "new on Netflix", "leaving Netflix this month" |
| Documentaries | "best documentaries 2025", "true crime documentaries" |
| Family/Kids | "family movies", "animated movies 2025" |
| Binge Culture | "shows to binge", "binge worthy shows" |
| Actors | "best Tom Holland movies", "Zendaya movies" |
| Directors | "Christopher Nolan movies", "Tarantino best films" |
| Decades | "best 90s movies", "80s horror movies" |

**IMPORTANT DECISION:** We removed 2026 terms because 2026 just started and has limited content. Focus is on **2025 and timeless queries**.

**Priority System:**
- 60% chance: AI-generated creative terms
- 40% chance: Fallback to hardcoded viral_lists/trending from database

### 2. Question-Based Reply Strategy
**Location:** `server.py` → `LLMClient.analyze_and_draft()`

Replies are now **question-based** to create curiosity:

```
✅ GOOD: "does streamixapp.pages.dev have Barbie in 4K? no ads supposedly 🤔"
✅ GOOD: "wait does streamixapp.pages.dev have all these? free + HD 👀"
❌ BAD: "Check out streamixapp.pages.dev for free movies!"
```

**Reply Rules:**
- Under 140 characters
- ALWAYS include `streamixapp.pages.dev`
- ALWAYS include ONE trending hashtag
- Use question format (wondering, curious, asking)
- Include 1-2 benefits: 4K, no ads, no popups, free, no signup
- Sound like a REAL person, NOT a marketer

### 3. Inclusive Pre-Filtering
**Location:** `xbot_client.js` → `isLikelyStreamingRelated()`

The pre-filter is now **more inclusive** to avoid false negatives:

**Hard Skip (NEVER relevant):**
- Sports: goal, touchdown, NFL, NBA, FIFA
- Politics: Trump, Biden, election, Congress
- Package delivery: tracking number, warehouse
- Music-only: Spotify, concert tickets

**Pass to LLM (potentially relevant):**
- "streaming", "watch", "movie", "film", "show", "series"
- "Netflix", "Hulu", "Disney", "HBO", "Prime Video"
- "where to", "how to", "recommend", "want to watch"
- "expensive", "cancel", "subscription", "free"
- "4K", "HD", "buffering", "no ads"

### 4. Exhaustion-Based Search Term Rotation
**Location:** `xbot_client.js` → Main loop

**How it works:**
- Bot stays on the SAME search term until it finds 0 new candidates
- After **3 consecutive empty scans**, it rotates to a new term
- This ensures we fully exhaust each search term before moving on

**State Variables:**
- `STATE.consecutiveEmptyScans` - Counter for empty scans
- `STATE.shouldRotateKeyword` - Flag to trigger rotation
- `CONFIG.EMPTY_SCANS_BEFORE_ROTATE = 3`

### 5. Aggressive Configuration
**Location:** `xbot_client.js` → `CONFIG`

```javascript
MAIN_LOOP_INTERVAL: 15000,    // 15 seconds between loops
REPLY_COOLDOWN: 3000,         // 3 seconds between replies
MAX_REPLIES_PER_HOUR: 60,     // 60 replies/hour max
MAX_REPLIES_PER_SCAN: 100,    // Process up to 100 candidates
EMPTY_SCANS_BEFORE_ROTATE: 3  // Rotate after 3 empty scans
```

---

## 🚧 CRITICAL ISSUES TO FIX (Next Steps)

### Issue 1: Bot Uses "Latest" Tab Instead of "Top"
**Problem:** The bot currently scans the "Latest" tab which shows low-quality, chronological posts.
**Solution:** Switch to the "Top" tab which shows high-engagement, viral posts.
**Where to Fix:** `xbot_client.js` - Look for URL construction or tab clicking logic.
**How:** Either:
- Remove `&f=live` from search URL (makes it default to "Top")
- OR click the "Top" tab after searching

### Issue 2: Bot Replies to Old Posts (2024 and earlier)
**Problem:** When searching "Top", old viral posts from 2024/2023 appear and bot replies to them.
**Solution:** Add date filtering to skip posts older than 2025.
**Where to Fix:** `xbot_client.js` - In the tweet parsing/scanning logic.
**How:** 
```javascript
const timeEl = tweet.querySelector('time');
if (timeEl) {
    const dateTime = timeEl.getAttribute('datetime');
    const year = new Date(dateTime).getFullYear();
    if (year < 2025) continue; // Skip old posts
}
```

### Issue 3: Some Search Terms Too Niche
**Problem:** Terms like "Margot Robbie performances" have low volume.
**Solution:** AI generator already handles this, but ensure variety in actor/director terms.
**Note:** The AI generates varied terms. This is less of an issue now.

---

## 📂 Key Files & Their Purposes

| File | Purpose |
|------|---------|
| `server.py` | Backend brain - AI search terms, LLM replies, TMDB integration |
| `xbot_client.js` | Frontend body - DOM interactions, scanning, posting |
| `xbot_memory.db` | SQLite database - replied tweets, search term pool |
| `PROJECT_STATUS.md` | This file - complete project documentation |

---

## 🛠️ How to Run

### Step 1: Start the Brain (Server)
```bash
cd c:\Users\VASU\Desktop\xbot\active
py -m uvicorn server:app --reload --port 8000
```

### Step 2: Start the Body (Client)
1. Open Tampermonkey in your browser
2. Find script: `XBot-v8.0-Million-Visitor-Engine.user.js`
3. Copy content from `c:\Users\VASU\Desktop\xbot\active\xbot_client.js`
4. Paste into Tampermonkey and save (Ctrl+S)
5. Go to `https://x.com`
6. Click "Start Engine" on the overlay UI

### Step 3: Verify Operation
- Check console logs for `[XBot]` messages
- Verify "ai_creative" category in search terms
- Confirm replies are question-based

---

## 🔑 API Keys & Configuration

**Groq API Key:** Stored in `server.py` as `GROQ_API_KEY`
**TMDB API Key:** Stored in `server.py` as `TMDB_API_KEY`
**Target Site:** `streamixapp.pages.dev`

---

## 📊 Database Tables

### `search_term_pool`
- `term` - The search query
- `lang_code` - Language (en, de, fr, etc.)
- `category` - Type (viral_lists, trending, ai_creative)
- `popularity` - Priority score
- `last_used_at` - Timestamp of last use
- `use_count` - How many times used

### `replied_tweets`
- `tweet_id` - Unique tweet identifier
- `user_handle` - Twitter handle
- `reply_text` - What we replied
- `timestamp` - When we replied
- `sentiment` - User's sentiment

### `scanned_tweets`
- `tweet_id` - Tweets we've seen (to avoid duplicates)

---

## 🎯 Strategy Summary

1. **Search Strategy:** AI generates 50 diverse terms targeting movie/TV lovers
2. **Tab Strategy:** Should use "Top" tab for high-engagement posts (NEEDS FIX)
3. **Date Strategy:** Only reply to 2025+ posts (NEEDS FIX)
4. **Reply Strategy:** Question-based, curiosity-driven messages
5. **Rotation Strategy:** Exhaust each search term before rotating
6. **Filtering Strategy:** Inclusive pre-filter, let LLM decide relevance

---

## 🧪 Testing Commands

### Test AI Search Terms
```powershell
1..10 | ForEach-Object { $r = Invoke-RestMethod -Uri "http://localhost:8000/smart-search"; Write-Host "$($r.category): $($r.search_term)" }
```

### Clear Search Term Pool
```powershell
py -c "import sqlite3; conn = sqlite3.connect('xbot_memory.db'); conn.execute('DELETE FROM search_term_pool'); conn.commit(); print('Pool cleared!')"
```

### Check Database Stats
```powershell
py -c "import sqlite3; conn = sqlite3.connect('xbot_memory.db'); c = conn.cursor(); c.execute('SELECT category, COUNT(*) FROM search_term_pool GROUP BY category'); [print(f'{row[0]}: {row[1]} terms') for row in c.fetchall()]"
```

---

## ⚠️ Important Decisions Made

1. **2026 Removed:** All references to 2026 removed from search terms - too early, limited content
2. **Frustration Terms Deprioritized:** "netflix expensive" type terms yield old posts with zero engagement
3. **Question Format Enforced:** All replies must be questions to drive curiosity
4. **AI-First Approach:** 60% of terms are AI-generated, not hardcoded
5. **Exhaustion > Time:** Rotate based on empty results, not time intervals

---

## 🔄 For the Next Agent

**Your immediate tasks:**
1. Fix the "Top" tab issue in `xbot_client.js`
2. Add date filtering (>= 2025) in the scanning logic
3. Test with DRY_RUN mode first
4. Then enable live replies

**Key functions to examine:**
- `xbot_client.js`: Look for `handleScanning`, `parseTweet`, URL construction
- `server.py`: Already optimized, no changes needed

**Good luck!**
