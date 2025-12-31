"""
XBot Brain Server v1.0
======================
The Python "Brain" for the X.com Automation Bot.
Implements: Groq LLM, SQLite Persistence, Region Rotation, Language Binding.

Run: uvicorn server:app --reload --port 8000
"""

import os
import json
import sqlite3
import random
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables
load_dotenv()

# --- Configurations ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TMDB_API_KEY = "61d95006877f80fb61358dbb78f153c3"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found in environment variables!")

GROQ_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
DATABASE_PATH = "xbot_memory.db"
SITE_URL = "streamixapp.pages.dev"

# ============================================================================
# REGION-LANGUAGE CONFIGURATION (From intelligence.md v16.0)
# ============================================================================

# 24-Hour Daily Rotation Schedule (UTC)
DAILY_SCHEDULE = [
    {"hour": 0, "region": "Los Angeles", "lang": "en", "location": "Los Angeles"},
    {"hour": 1, "region": "Mexico City", "lang": "es", "location": "Mexico City"},
    {"hour": 2, "region": "Lima", "lang": "es", "location": "Lima"},
    {"hour": 3, "region": "Buenos Aires", "lang": "es", "location": "Buenos Aires"},
    {"hour": 4, "region": "São Paulo", "lang": "pt", "location": "São Paulo"},
    {"hour": 5, "region": "Rio de Janeiro", "lang": "pt", "location": "Rio de Janeiro"},
    {"hour": 6, "region": "Sydney", "lang": "en", "location": "Sydney"},
    {"hour": 7, "region": "Melbourne", "lang": "en", "location": "Melbourne"},
    {"hour": 8, "region": "Tokyo", "lang": "ja", "location": "Tokyo"},
    {"hour": 9, "region": "Seoul", "lang": "ko", "location": "Seoul"},
    {"hour": 10, "region": "Jakarta", "lang": "id", "location": "Jakarta"},
    {"hour": 11, "region": "Singapore", "lang": "en", "location": "Singapore"},
    {"hour": 12, "region": "Paris", "lang": "fr", "location": "Paris"},
    {"hour": 13, "region": "Amsterdam", "lang": "nl", "location": "Amsterdam"},
    {"hour": 14, "region": "Berlin", "lang": "de", "location": "Berlin"},
    {"hour": 15, "region": "Warsaw", "lang": "pl", "location": "Warsaw"},
    {"hour": 16, "region": "Rome", "lang": "it", "location": "Rome"},
    {"hour": 17, "region": "Madrid", "lang": "es", "location": "Madrid"},
    {"hour": 18, "region": "Lisbon", "lang": "pt", "location": "Lisbon"},
    {"hour": 19, "region": "London", "lang": "en", "location": "London"},
    {"hour": 20, "region": "Dublin", "lang": "en", "location": "Dublin"},
    {"hour": 21, "region": "Toronto", "lang": "en", "location": "Toronto"},
    {"hour": 22, "region": "New York", "lang": "en", "location": "New York"},
    {"hour": 23, "region": "Chicago", "lang": "en", "location": "Chicago"},
]

# Native Language Keywords
KEYWORDS = {
    "en": ['"where to watch" free', '"best free streaming" site', '"netflix separate" free', '"streaming site" no ads'],
    "fr": ['"où regarder" film gratuit', '"site streaming gratuit"', '"alternative netflix gratuit"'],
    "de": ['"wo kann ich schauen" kostenlos', '"streaming seite kostenlos"'],
    "es": ['"dónde ver" películas gratis', '"sitio streaming gratis"'],
    "pt": ['"onde assistir" filme grátis', '"site streaming grátis"'],
    "it": ['"dove guardare" film gratis', '"sito streaming gratuito"'],
    "nl": ['"waar kijken" gratis', '"gratis streaming site"'],
    "pl": ['"gdzie oglądać" za darmo', '"darmowy streaming"'],
    "ja": ["映画 無料 視聴", "無料 ストリーミング サイト"],
    "ko": ["영화 무료 보기", "무료 스트리밍 사이트"],
    "id": ["nonton film gratis", "situs streaming gratis"],
}

# Language Names for LLM
LANG_NAMES = {
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "ja": "Japanese",
    "ko": "Korean",
    "id": "Indonesian",
}

# ============================================================================
# DATABASE
# ============================================================================

def init_database():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Replied tweets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS replied_tweets (
            tweet_id TEXT PRIMARY KEY,
            user_handle TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            region TEXT,
            language TEXT,
            reply_text TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_handle ON replied_tweets(user_handle)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON replied_tweets(timestamp)")
    
    # Scanned tweets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scanned_tweets (
            tweet_id TEXT PRIMARY KEY,
            scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            skip_reason TEXT
        )
    """)
    
    # Trend cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trend_cache (
            region TEXT PRIMARY KEY,
            trends TEXT,
            harvested_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Session log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_region TEXT,
            last_keyword_index INTEGER DEFAULT 0,
            replies_sent INTEGER DEFAULT 0,
            status TEXT DEFAULT 'RUNNING'
        )
    """)

    # --- NEW TABLES FOR SMART SEARCH ---
    
    # Search Term Pool (Stores generated high-intent terms)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_term_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT UNIQUE,
            tmdb_id INTEGER,
            content_type TEXT,
            title TEXT,
            year TEXT,
            popularity REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            use_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0
        )
    """)
    
    # TMDB Cache (Stores raw TMDB results to save API calls)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tmdb_cache (
            endpoint TEXT PRIMARY KEY,
            data TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# ============================================================================
# TMDB CLIENT
# ============================================================================

class TMDBClient:
    def __init__(self):
        self.api_key = TMDB_API_KEY
        self.base_url = TMDB_BASE_URL
        
    def _get(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make GET request to TMDB with caching."""
        # Check cache first
        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True)}" if params else endpoint
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data, fetched_at FROM tmdb_cache WHERE endpoint = ?", (cache_key,))
            row = cursor.fetchone()
            
            if row:
                fetched_at = datetime.fromisoformat(row["fetched_at"])
                # Cache valid for 24 hours
                if datetime.utcnow() - fetched_at < timedelta(hours=24):
                    return json.loads(row["data"])
        
        # Fetch from API
        if not params:
            params = {}
        params["api_key"] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO tmdb_cache (endpoint, data, fetched_at) VALUES (?, ?, ?)",
                    (cache_key, json.dumps(data), datetime.utcnow().isoformat())
                )
                conn.commit()
            
            return data
        except Exception as e:
            print(f"TMDB API Error: {e}")
            return None

    def get_trending_movies(self) -> List[Dict]:
        data = self._get("/trending/movie/day")
        return data.get("results", []) if data else []

    def get_trending_tv(self) -> List[Dict]:
        data = self._get("/trending/tv/day")
        return data.get("results", []) if data else []

    def get_popular_movies(self) -> List[Dict]:
        data = self._get("/movie/popular")
        return data.get("results", []) if data else []

# ============================================================================
# SMART SEARCH LOGIC
# ============================================================================

class SmartSearch:
    def __init__(self):
        self.tmdb = TMDBClient()
        
    def generate_search_terms(self):
        """Fetch trending content and populate search term pool."""
        movies = self.tmdb.get_trending_movies()
        tv_shows = self.tmdb.get_trending_tv()
        
        new_terms = 0
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Process Movies - EXPANDED CATEGORIES
            for m in movies:
                title = m.get("title")
                year = m.get("release_date", "")[:4]
                if not title: continue
                
                # Category 1: Direct Intent (High conversion)
                direct_intent = [
                    f'"{title}" watch free',
                    f'"{title}" streaming',
                    f'where to watch "{title}"',
                    f'"{title}" online free',
                    f'"{title}" {year} stream',
                    f'"{title}" full movie',
                ]
                
                # Category 2: Movie Discussion (High volume)
                discussion = [
                    f'just watched {title}',
                    f'{title} was amazing',
                    f'{title} movie',
                    f'watching {title}',
                ]
                
                # Category 3: Frustration (High intent)
                frustration = [
                    f"can't find {title}",
                    f'{title} not on netflix',
                    f'{title} removed',
                ]
                
                # Category 4: Recommendations
                recommendations = [
                    f'{title} recommend',
                    f'should I watch {title}',
                ]
                
                all_queries = direct_intent + discussion + frustration + recommendations
                
                for q in all_queries:
                    try:
                        cursor.execute("""
                            INSERT INTO search_term_pool (term, tmdb_id, content_type, title, year, popularity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (q, m["id"], "movie", title, year, m["popularity"]))
                        new_terms += 1
                    except sqlite3.IntegrityError:
                        pass # Already exists
            
            # Process TV Shows - EXPANDED CATEGORIES
            for t in tv_shows:
                name = t.get("name")
                year = t.get("first_air_date", "")[:4]
                if not name: continue
                
                # Category 1: Direct Intent
                direct_intent = [
                    f'"{name}" watch free',
                    f'"{name}" streaming',
                    f'where to watch "{name}"',
                    f'"{name}" free episodes',
                    f'"{name}" online free',
                    f'"{name}" all seasons',
                ]
                
                # Category 2: Discussion
                discussion = [
                    f'binging {name}',
                    f'{name} is so good',
                    f'{name} season',
                    f'watching {name}',
                ]
                
                # Category 3: Frustration
                frustration = [
                    f"can't find {name}",
                    f'{name} removed',
                    f'{name} not available',
                ]
                
                all_queries = direct_intent + discussion + frustration
                
                for q in all_queries:
                    try:
                        cursor.execute("""
                            INSERT INTO search_term_pool (term, tmdb_id, content_type, title, year, popularity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (q, t["id"], "tv", name, year, t["popularity"]))
                        new_terms += 1
                    except sqlite3.IntegrityError:
                        pass
            
            # Category 5: Generic High-Volume (Not content-specific)
            generic_terms = [
                ("free movies online", 0, "generic", "Free Movies", "", 50),
                ("free streaming site", 0, "generic", "Free Streaming", "", 50),
                ("watch movies free", 0, "generic", "Free Movies", "", 50),
                ("no ads streaming", 0, "generic", "No Ads", "", 50),
                ("movie recommendations", 0, "generic", "Recommendations", "", 40),
                ("what to watch tonight", 0, "generic", "What to Watch", "", 40),
                ("best free streaming", 0, "generic", "Best Free", "", 45),
                ("streaming without ads", 0, "generic", "No Ads", "", 45),
                ("where to watch movies free", 0, "generic", "Watch Free", "", 50),
            ]
            
            for term, tmdb_id, content_type, title, year, popularity in generic_terms:
                try:
                    cursor.execute("""
                        INSERT INTO search_term_pool (term, tmdb_id, content_type, title, year, popularity)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (term, tmdb_id, content_type, title, year, popularity))
                    new_terms += 1
                except sqlite3.IntegrityError:
                    pass
            
            conn.commit()
        
        print(f"Generated {new_terms} new high-intent search terms (10x expanded categories).")

    def get_next_term(self) -> Dict[str, Any]:
        """Get the best unused search term."""
        # Ensure pool is populated
        self.generate_search_terms()
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Select a term that hasn't been used in 24 hours, prioritizing popularity
            yesterday = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            cursor.execute("""
                SELECT * FROM search_term_pool 
                WHERE last_used_at IS NULL OR last_used_at < ?
                ORDER BY popularity DESC, random()
                LIMIT 1
            """, (yesterday,))
            
            row = cursor.fetchone()
            
            if row:
                # Update usage stats
                cursor.execute("""
                    UPDATE search_term_pool 
                    SET last_used_at = ?, use_count = use_count + 1
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), row["id"]))
                conn.commit()
                
                return {
                    "search_term": row["term"],
                    "title": row["title"],
                    "year": row["year"],
                    "tmdb_id": row["tmdb_id"],
                    "content_type": row["content_type"]
                }
            
            # Fallback if all terms used recently (unlikely)
            return {
                "search_term": '"where to watch" free',
                "title": "Generic",
                "year": "",
                "tmdb_id": 0,
                "content_type": "generic"
            }

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TweetAnalysisRequest(BaseModel):
    tweet_id: str
    tweet_text: str
    user_handle: str
    parent_text: Optional[str] = None
    # Context from Smart Search
    movie_title: Optional[str] = None
    movie_year: Optional[str] = None

class TweetAnalysisResponse(BaseModel):
    action: str  # "REPLY" or "SKIP"
    reason: str
    draft: Optional[str] = None
    language: str
    trend_injected: Optional[str] = None

class TrendUpdateRequest(BaseModel):
    region: str
    trends: List[str]

class ScheduleResponse(BaseModel):
    region: str
    location: str
    language: str
    lang_code: str
    current_trends: List[str]
    keywords: List[str]

class SmartSearchResponse(BaseModel):
    search_term: str
    title: str
    year: str
    tmdb_id: int
    content_type: str

# ============================================================================
# GROQ LLM CLIENT
# ============================================================================

class LLMClient:
    def __init__(self):
        if not GROQ_API_KEY:
            print("WARNING: GROQ_API_KEY not set. LLM calls will fail.")
        self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    
    def analyze_and_draft(
        self,
        tweet_text: str,
        lang_code: str,
        region: str,
        trends: List[str],
        movie_title: str = None, # NEW: Context
        movie_year: str = None,  # NEW: Context
        parent_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze tweet intent and draft a reply."""
        
        if not self.client:
            return {
                "action": "REPLY",
                "reason": "MOCK: Intent detected",
                "draft": f"[MOCK] Check out {SITE_URL}!",
                "trend": trends[0] if trends else None
            }
        
        lang_name = LANG_NAMES.get(lang_code, "English")
        trends_str = ", ".join(trends[:5]) if trends else "#Movies, #Streaming, #WatchOnline"
        
        # Contextual Prompt
        context_block = ""
        if movie_title:
            context_block = f"""
CONTEXT: User searched for "{movie_title}" ({movie_year}). Verify tweet is about this content.
"""

        system_prompt = f"""You are a genuine movie fan on X (Twitter) who discovered an amazing streaming site.
You speak {lang_name} natively. You're helpful, casual, and sound like a real person - NOT a marketer.

{context_block}

=== ABSOLUTE RULES (VIOLATING ANY = FAILURE) ===

RULE 1 - CHARACTER LIMIT: Your reply MUST be under 200 characters total. Twitter has limits.

RULE 2 - MANDATORY SITE: You MUST include "streamixapp.pages.dev" in EVERY reply.
   This is the ONLY site you recommend. Period.

RULE 3 - BANNED WORDS: NEVER mention these competitors:
   Netflix, Hulu, Amazon, Disney+, HBO, Sflix, Fmovies, 123movies, Soap2day, or ANY other streaming site.
   If the tweet mentions these, just say our site is better without naming them.

RULE 4 - TRENDING HASHTAG: Include ONE hashtag from: {trends_str}

RULE 5 - AUTHENTIC VOICE: Sound like these real examples:
   - "yo check streamixapp.pages.dev for that, no ads fr 🔥 #Movies"
   - "been using streamixapp.pages.dev lately, way cleaner #Streaming"
   - "streamixapp.pages.dev has it, zero popups 💯 #WatchOnline"
   - "found it on streamixapp.pages.dev ngl pretty solid #Cinema"

RULE 6 - REPLY OR SKIP:
   REPLY if: User is looking for where to watch, asking for recommendations, frustrated about finding content
   SKIP if: Just discussing plot, reviewing, already has a solution, is a bot/brand, off-topic

RULE 7 - LANGUAGE: Reply in {lang_name} only.

=== OUTPUT (JSON ONLY, NO MARKDOWN) ===
{{"action": "REPLY" or "SKIP", "reason": "brief why", "draft": "your reply under 200 chars", "trend": "#UsedHashtag"}}
"""

        user_message = f"Tweet: {tweet_text}"
        if parent_text:
            user_message += f"\nParent Tweet: {parent_text}"

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.strip().startswith("json"):
                    result_text = result_text.strip()[4:]
            
            return json.loads(result_text)
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return {"action": "SKIP", "reason": f"Error: {e}", "draft": None}

# ============================================================================
# CORE LOGIC
# ============================================================================

def get_current_schedule() -> Dict[str, Any]:
    """Get the current target based on UTC hour."""
    now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
    hour = now.hour
    slot = DAILY_SCHEDULE[hour]
    return {
        "region": slot["region"],
        "location": slot["location"],
        "lang_code": slot["lang"],
        "language": LANG_NAMES.get(slot["lang"], "English"),
        "keywords": KEYWORDS.get(slot["lang"], KEYWORDS["en"])
    }

def check_duplicate(tweet_id: str, user_handle: str) -> tuple[bool, str]:
    """Check if we should skip this tweet."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM replied_tweets WHERE tweet_id = ?", (tweet_id,))
        if cursor.fetchone(): return True, "Already replied"
        
        cursor.execute("SELECT 1 FROM scanned_tweets WHERE tweet_id = ?", (tweet_id,))
        if cursor.fetchone(): return True, "Already scanned"
        
        yesterday = datetime.utcnow() - timedelta(hours=24)
        cursor.execute("SELECT COUNT(*) FROM replied_tweets WHERE user_handle = ? AND timestamp > ?", (user_handle, yesterday.isoformat()))
        if cursor.fetchone()[0] >= 2: return True, "User cooldown"
    
    return False, ""

def log_reply(tweet_id: str, user_handle: str, region: str, language: str, reply_text: str):
    """Log a successful reply."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO replied_tweets (tweet_id, user_handle, region, language, reply_text) VALUES (?, ?, ?, ?, ?)",
            (tweet_id, user_handle, region, language, reply_text)
        )
        conn.commit()

def log_scanned(tweet_id: str, skip_reason: str):
    """Log a scanned tweet."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO scanned_tweets (tweet_id, skip_reason) VALUES (?, ?)",
            (tweet_id, skip_reason)
        )
        conn.commit()

def get_cached_trends(region: str) -> List[str]:
    """Get cached trends for a region."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT trends FROM trend_cache WHERE region = ?", (region,))
        row = cursor.fetchone()
        
        if row:
            try:
                trends = json.loads(row["trends"])
                if trends and len(trends) > 0:
                    return trends
            except:
                pass
                
    # Fallback if cache empty or invalid
    return ["#Streaming", "#Movies", "#WatchOnline", "#Cinema", "#WhatToWatch"]

def update_trend_cache(region: str, trends: List[str]):
    """Update trend cache for a region."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO trend_cache (region, trends, harvested_at) VALUES (?, ?, ?)",
            (region, json.dumps(trends), datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat())
        )
        conn.commit()

def get_stats() -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM replied_tweets")
        total = cursor.fetchone()[0]
        # Fix datetime deprecation
        now = datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute("SELECT COUNT(*) FROM replied_tweets WHERE timestamp > ?", (today.isoformat(),))
        today_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT user_handle) FROM replied_tweets")
        unique = cursor.fetchone()[0]
        cursor.execute("SELECT language, COUNT(*) FROM replied_tweets GROUP BY language")
        langs = dict(cursor.fetchall())
    return {"total_replies": total, "replies_today": today_count, "unique_users": unique, "by_language": langs}

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="XBot Brain", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Components
llm_client = LLMClient()
smart_search = SmartSearch()
init_database()

@app.get("/")
def root():
    return {"status": "online", "service": "XBot Brain v2.0 (TMDB Enabled)"}

@app.get("/schedule", response_model=ScheduleResponse)
def get_schedule():
    schedule = get_current_schedule()
    trends = get_cached_trends(schedule["region"])
    return ScheduleResponse(
        region=schedule["region"],
        location=schedule["location"],
        language=schedule["language"],
        lang_code=schedule["lang_code"],
        current_trends=trends,
        keywords=schedule["keywords"]
    )

@app.get("/smart-search", response_model=SmartSearchResponse)
def get_search_term():
    """Get the next best high-intent search term."""
    return smart_search.get_next_term()

@app.post("/analyze", response_model=TweetAnalysisResponse)
def analyze_tweet(request: TweetAnalysisRequest):
    is_duplicate, reason = check_duplicate(request.tweet_id, request.user_handle)
    if is_duplicate:
        return TweetAnalysisResponse(action="SKIP", reason=reason, draft=None, language="", trend_injected=None)
    
    schedule = get_current_schedule()
    trends = get_cached_trends(schedule["region"])
    
    result = llm_client.analyze_and_draft(
        tweet_text=request.tweet_text,
        lang_code=schedule["lang_code"],
        region=schedule["region"],
        trends=trends,
        movie_title=request.movie_title, # Pass context
        movie_year=request.movie_year,   # Pass context
        parent_text=request.parent_text
    )
    
    if result["action"] == "SKIP":
        log_scanned(request.tweet_id, result.get("reason", "Skipped by LLM"))
    
    return TweetAnalysisResponse(
        action=result["action"],
        reason=result["reason"],
        draft=result.get("draft"),
        language=schedule["language"],
        trend_injected=result.get("trend")
    )

class LogReplyRequest(BaseModel):
    tweet_id: str
    user_handle: str
    reply_text: str

@app.post("/log-reply")
def log_successful_reply(request: LogReplyRequest):
    schedule = get_current_schedule()
    log_reply(
        tweet_id=request.tweet_id,
        user_handle=request.user_handle,
        region=schedule["region"],
        language=schedule["lang_code"],
        reply_text=request.reply_text
    )
    return {"status": "logged"}

@app.post("/update-trends")
def update_trends(request: TrendUpdateRequest):
    update_trend_cache(request.region, request.trends)
    return {"status": "updated", "region": request.region, "trends_count": len(request.trends)}

@app.get("/stats")
def get_statistics_endpoint():
    return get_stats()

@app.get("/check-health")
def check_health():
    stats = get_stats()
    warnings = []
    if stats["replies_today"] >= 150: warnings.append("Daily limit approaching")
    return {"status": "HEALTHY" if not warnings else "WARNING", "warnings": warnings, "stats": stats}

class LocationSelectRequest(BaseModel):
    target_location: str
    options: List[str]

@app.post("/select-location")
def select_location(request: LocationSelectRequest):
    target = request.target_location.lower()
    target_parts = target.replace(',', ' ').split()
    best_match = -1
    best_score = 0
    
    for i, option in enumerate(request.options):
        option_lower = option.lower()
        score = 0
        if target in option_lower: score += 10
        for part in target_parts:
            if part in option_lower: score += 2
        if score > 0: score += max(0, 10 - len(option) // 5)
        if score > best_score:
            best_score = score
            best_match = i
            
    if best_match >= 0:
        return {"index": best_match, "selected": request.options[best_match], "confidence": best_score}
    else:
        return {"index": 0, "selected": request.options[0] if request.options else None, "confidence": 0}

if __name__ == "__main__":
    import uvicorn
    print("Starting XBot Brain Server v2.0 (TMDB Enabled)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
