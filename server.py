"""
XBot Brain Server v8.0 - MILLION VISITOR ENGINE
=================================================
Advanced AI Orchestrator for X.com Automation
- TIER 1 ONLY: High-CPM Languages (EN, DE, FR, NL, Nordic)
- Multi-Endpoint TMDB: now_playing, discover, popular, airing_today
- Sophisticated LLM: Context-aware, sentiment-matched, personalized replies
- Validated lang:XX search operators for precise targeting

Run: uvicorn server:app --reload --port 8000
"""

import os
import json
import sqlite3
import random
import requests
from datetime import datetime, timedelta, timezone
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

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TMDB_API_KEY = "61d95006877f80fb61358dbb78f153c3"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found in environment variables!")

GROQ_MODEL = "qwen/qwen3-32b"
DATABASE_PATH = "xbot_memory.db"
SITE_URL = "streamixapp.pages.dev"

# ============================================================================
# TIER 1 HIGH-CPM CONFIGURATION (Validated 2025-01-01)
# ============================================================================

# Language-specific search term templates (MAXIMUM COVERAGE for movie/TV lovers)
SEARCH_TEMPLATES = {
    "en": {
        "trending": [
            "where can I watch {title}",
            "how to watch {title} free",
            "{title} streaming",
            "watch {title} online",
        ],
        "viral_lists": [
            # === MOVIES 2025 & 2025 ===
            "top movies 2025", "top movies 2025",
            "best movies 2025", "best movies 2025",
            "best movies January 2025", "best movies December 2025",
            "upcoming movies 2025", "upcoming movies 2025",
            "most anticipated movies 2025", "most anticipated movies",
            "new movie releases 2025", "new movie releases",
            "movies coming out soon", "movies releasing this month",
            "top 10 movies 2025", "top 10 movies 2025",
            "biggest movies 2025", "box office 2025",
            
            # === TV SHOWS 2025 & 2025 ===
            "best tv shows 2025", "best tv shows 2025",
            "top tv shows 2025", "top tv shows 2025",
            "new series 2025", "new series 2025",
            "best new shows", "upcoming tv shows",
            "tv show recommendations", "shows to watch 2025",
            "must watch tv shows", "trending tv shows",
            
            # === AWARD SEASON (MASSIVE ENGAGEMENT!) ===
            "Oscar nominations 2025", "Oscar predictions",
            "best picture nominees", "Oscar winners",
            "Golden Globe nominations", "Golden Globe winners",
            "Emmy nominations 2025", "Emmy winners",
            "SAG awards", "BAFTA nominations",
            "award season movies", "Oscar worthy",
            
            # === GENRES (DEDICATED FAN BASES) ===
            # Horror
            "best horror movies 2025", "best horror movies 2025",
            "scary movies to watch", "horror movie recommendations",
            "new horror movies", "horror films",
            # Comedy
            "best comedy movies 2025", "funny movies to watch",
            "comedy movie recommendations", "hilarious movies",
            # Action
            "best action movies 2025", "action movies to watch",
            "new action movies", "action film recommendations",
            # Romance
            "best romantic movies", "romance movies to watch",
            "romantic comedies", "love story movies",
            # Thriller
            "best thriller movies 2025", "thriller recommendations",
            "suspense movies", "psychological thriller",
            # Sci-Fi
            "best sci-fi movies 2025", "science fiction movies",
            "space movies", "sci-fi recommendations",
            # Drama
            "best drama movies 2025", "drama recommendations",
            "emotional movies", "critically acclaimed movies",
            
            # === FRANCHISES (MARVEL, DC, STAR WARS = HUGE!) ===
            "Marvel movies 2025", "MCU phase 7",
            "Marvel upcoming movies", "Avengers movies",
            "DC movies 2025", "DC upcoming movies",
            "Batman movies", "Superman movies",
            "Star Wars streaming", "Star Wars movies",
            "Harry Potter series", "Wizarding World",
            "Lord of the Rings", "Dune movies",
            
            # === K-DRAMA / INTERNATIONAL (EXPLOSIVE GROWTH) ===
            "best kdrama 2025", "best kdrama 2025",
            "korean drama recommendations", "kdrama to watch",
            "new kdrama", "top kdrama",
            "spanish shows", "spanish movies",
            "foreign films to watch", "international movies",
            "bollywood movies 2025", "hindi movies",
            "japanese movies", "french films",
            
            # === ANIME ===
            "best anime 2025", "best anime 2025",
            "top anime 2025", "new anime 2025",
            "anime recommendations", "anime to watch",
            "where to watch anime", "anime streaming",
            "anime movies", "best anime movies",
            
            # === MOODS / EMOTIONS (HIGH INTENT!) ===
            "feel good movies", "comfort movies",
            "movies to watch when bored", "weekend movie",
            "date night movies", "rainy day movies",
            "sad movies to cry", "emotional movies to watch",
            "uplifting movies", "inspiring movies",
            "movies to watch alone", "late night movies",
            
            # === STREAMING NEWS (PERFECT TIMING!) ===
            "leaving netflix this month", "new on netflix",
            "new on disney plus", "coming to hbo max",
            "what's new on streaming", "streaming this week",
            "new releases streaming", "just added netflix",
            
            # === DOCUMENTARIES ===
            "best documentaries 2025", "best documentaries 2025",
            "documentary recommendations", "documentaries to watch",
            "true crime documentary", "nature documentary",
            "new documentaries", "must watch documentaries",
            
            # === FAMILY / KIDS ===
            "family movies to watch", "family movie night",
            "kids movies 2025", "movies for kids",
            "animated movies 2025", "best animated movies",
            "disney movies", "pixar movies",
            
            # === BINGE CULTURE ===
            "what to binge", "binge worthy shows",
            "shows to binge", "binge watch recommendations",
            "weekend binge", "what to marathon",
            "addictive tv shows", "shows you can't stop watching",
        ],
        "recommendation": [
            "what movie should I watch tonight",
            "recommend me something to watch",
            "I need a good movie to watch",
            "what are you watching tonight",
            "looking for something to binge",
            "any good shows to watch",
            "movie night suggestions",
            "what should I watch",
            "show recommendations",
            "movie recommendations",
            "suggest me a movie",
            "what to watch next",
        ],
        "frustration": [
            # Netflix
            "netflix is too expensive", "canceling my netflix subscription",
            "sick of paying for netflix", "netflix sucks",
            # Disney+
            "disney plus too expensive", "canceling disney plus",
            "disney plus not worth it", "disney plus sucks",
            # HBO Max
            "hbo max too expensive", "canceling hbo max",
            "hbo max not worth it", "max subscription",
            # Hulu
            "hulu too expensive", "canceling hulu",
            "hulu ads annoying", "hulu not worth it",
            # Amazon Prime
            "prime video not worth it", "amazon prime expensive",
            # Peacock
            "peacock not worth it", "peacock sucks",
            # Apple TV+
            "apple tv not worth it", "apple tv expensive",
            # General streaming frustration
            "tired of paying for streaming services",
            "streaming services are a rip off",
            "too many streaming subscriptions",
            "can't afford streaming anymore",
            "subscription fatigue", "streaming is getting expensive",
            "hate paying for streaming", "streaming bubble",
        ],
        "intent": [
            "where to stream movies for free",
            "free movie streaming sites",
            "watch movies without subscription",
            "free alternative to netflix",
            "sites like netflix but free",
            "how to watch movies for free",
            "best free streaming sites",
            "watch films online free",
            "free tv show streaming",
            "watch anime free",
            "free streaming no ads",
            "stream movies free online",
            "watch shows for free",
            "free 4k streaming",
        ],
    },
    "de": {
        "trending": [
            "{title} lang:de",
            "gerade gesehen {title} lang:de",
            "{title} Film lang:de",
        ],
        "recommendation": [
            "Film empfehlen lang:de",
            "was schauen lang:de",
            "was soll ich schauen lang:de",
        ],
        "frustration": [
            "Netflix teuer lang:de",
            "Netflix kündigen lang:de",
        ],
        "intent": [
            "kostenlos streamen lang:de",
            "kostenlos schauen lang:de",
            "gratis Film lang:de",
        ],
    },
    "fr": {
        "trending": [
            "{title} lang:fr",
            "regardé {title} lang:fr",
        ],
        "recommendation": [
            "quoi regarder lang:fr",
            "film recommander lang:fr",
            "conseiller film lang:fr",
        ],
        "frustration": [
            "Netflix cher lang:fr",
            "annuler Netflix lang:fr",
        ],
        "intent": [
            "regarder gratuit lang:fr",
            "streaming gratuit lang:fr",
        ],
    },
    "nl": {
        "trending": [
            "{title} lang:nl",
        ],
        "recommendation": [
            "wat kijken lang:nl",
            "film aanbevelen lang:nl",
        ],
        "frustration": [
            "Netflix duur lang:nl",
            "Netflix opzeggen lang:nl",
        ],
        "intent": [
            "gratis kijken lang:nl",
        ],
    },
    # Nordic languages - TITLE ONLY (low general volume, validated)
    "sv": {"trending": ["{title} lang:sv"]},
    "no": {"trending": ["{title} lang:no"]},
    "da": {"trending": ["{title} lang:da"]},
}

# Tier 1 High-CPM 24-Hour Schedule (70% English, 30% European)
# Prioritizes peak hours in each region for maximum engagement
DAILY_SCHEDULE = [
    # US Prime Time (Evening hours in US = High engagement)
    {"hour": 0, "region": "Los Angeles", "lang": "en", "location": "Los Angeles", "tmdb_region": "US"},
    {"hour": 1, "region": "Los Angeles", "lang": "en", "location": "Los Angeles", "tmdb_region": "US"},
    {"hour": 2, "region": "New York", "lang": "en", "location": "New York", "tmdb_region": "US"},
    {"hour": 3, "region": "New York", "lang": "en", "location": "New York", "tmdb_region": "US"},
    {"hour": 4, "region": "Toronto", "lang": "en", "location": "Toronto", "tmdb_region": "CA"},
    
    # Australia/NZ Morning
    {"hour": 5, "region": "Sydney", "lang": "en", "location": "Sydney", "tmdb_region": "AU"},
    {"hour": 6, "region": "Sydney", "lang": "en", "location": "Sydney", "tmdb_region": "AU"},
    
    # UK Morning
    {"hour": 7, "region": "London", "lang": "en", "location": "London", "tmdb_region": "GB"},
    {"hour": 8, "region": "London", "lang": "en", "location": "London", "tmdb_region": "GB"},
    
    # European Peak (Morning/Lunch in Europe)
    {"hour": 9, "region": "Berlin", "lang": "de", "location": "Berlin", "tmdb_region": "DE"},
    {"hour": 10, "region": "Berlin", "lang": "de", "location": "Berlin", "tmdb_region": "DE"},
    {"hour": 11, "region": "Paris", "lang": "fr", "location": "Paris", "tmdb_region": "FR"},
    {"hour": 12, "region": "Paris", "lang": "fr", "location": "Paris", "tmdb_region": "FR"},
    {"hour": 13, "region": "Amsterdam", "lang": "nl", "location": "Amsterdam", "tmdb_region": "NL"},
    
    # Nordic Slot (Title-only targeting)
    {"hour": 14, "region": "Stockholm", "lang": "sv", "location": "Stockholm", "tmdb_region": "SE"},
    
    # Back to European Evening
    {"hour": 15, "region": "Berlin", "lang": "de", "location": "Berlin", "tmdb_region": "DE"},
    {"hour": 16, "region": "Paris", "lang": "fr", "location": "Paris", "tmdb_region": "FR"},
    
    # UK Evening Prime Time
    {"hour": 17, "region": "London", "lang": "en", "location": "London", "tmdb_region": "GB"},
    {"hour": 18, "region": "London", "lang": "en", "location": "London", "tmdb_region": "GB"},
    {"hour": 19, "region": "Dublin", "lang": "en", "location": "Dublin", "tmdb_region": "IE"},
    
    # US Day/Afternoon
    {"hour": 20, "region": "New York", "lang": "en", "location": "New York", "tmdb_region": "US"},
    {"hour": 21, "region": "Chicago", "lang": "en", "location": "Chicago", "tmdb_region": "US"},
    {"hour": 22, "region": "Los Angeles", "lang": "en", "location": "Los Angeles", "tmdb_region": "US"},
    {"hour": 23, "region": "Los Angeles", "lang": "en", "location": "Los Angeles", "tmdb_region": "US"},
]

# Language display names
LANG_NAMES = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "nl": "Dutch",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
}

# Native language phrases for authentic replies
NATIVE_PHRASES = {
    "en": {
        "check_it": ["check out", "try", "use", "go to"],
        "good": ["fire", "solid", "clean", "goated", "legit"],
        "reaction": ["fr", "ngl", "tbh", "lowkey", "deadass"],
        "emoji": ["🔥", "💯", "👀", "🎬", "✨"],
    },
    "de": {
        "check_it": ["schau mal auf", "probier", "geh zu"],
        "good": ["mega", "geil", "krass", "nice"],
        "reaction": ["echt", "ehrlich", "safe"],
        "emoji": ["🔥", "💯", "👀", "🎬"],
    },
    "fr": {
        "check_it": ["regarde sur", "essaie", "va sur"],
        "good": ["trop bien", "génial", "ouf", "dingue"],
        "reaction": ["franchement", "sérieux", "grave"],
        "emoji": ["🔥", "💯", "👀", "🎬"],
    },
    "nl": {
        "check_it": ["kijk op", "probeer", "ga naar"],
        "good": ["vet", "chill", "top", "lekker"],
        "reaction": ["echt", "serieus"],
        "emoji": ["🔥", "💯", "👀", "🎬"],
    },
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
            reply_text TEXT,
            search_term TEXT,
            sentiment TEXT
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
    
    # Regional content cache (TMDB)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regional_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            lang_code TEXT,
            content_type TEXT,
            title TEXT,
            original_title TEXT,
            tmdb_id INTEGER,
            year TEXT,
            popularity REAL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(region, tmdb_id)
        )
    """)
    
    # Search term pool
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_term_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT,
            lang_code TEXT,
            category TEXT,
            title TEXT,
            tmdb_id INTEGER,
            popularity REAL,
            last_used_at TIMESTAMP,
            use_count INTEGER DEFAULT 0,
            reply_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(term, lang_code)
        )
    """)
    
    # TMDB cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tmdb_cache (
            endpoint TEXT PRIMARY KEY,
            data TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Session log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            replies_sent INTEGER DEFAULT 0,
            impressions_estimated INTEGER DEFAULT 0
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
# ADVANCED TMDB CLIENT (Multi-Endpoint Regional)
# ============================================================================

class TMDBClient:
    def __init__(self):
        self.api_key = TMDB_API_KEY
        self.base_url = TMDB_BASE_URL
        
    def _get(self, endpoint: str, params: Dict = None, cache_hours: int = 12) -> Optional[Dict]:
        """Make GET request to TMDB with caching."""
        cache_key = f"{endpoint}:{json.dumps(params, sort_keys=True)}" if params else endpoint
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data, fetched_at FROM tmdb_cache WHERE endpoint = ?", (cache_key,))
            row = cursor.fetchone()
            
            if row:
                fetched_at = datetime.fromisoformat(row["fetched_at"])
                # Handle both tz-aware and tz-naive datetimes
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - fetched_at < timedelta(hours=cache_hours):
                    return json.loads(row["data"])
        
        if not params:
            params = {}
        params["api_key"] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO tmdb_cache (endpoint, data, fetched_at) VALUES (?, ?, ?)",
                    (cache_key, json.dumps(data), datetime.now(timezone.utc).isoformat())
                )
                conn.commit()
            
            return data
        except Exception as e:
            print(f"TMDB API Error: {e}")
            return None

    def get_now_playing(self, region: str = "US") -> List[Dict]:
        """Get movies currently in theaters for a region."""
        data = self._get("/movie/now_playing", {"region": region, "language": "en-US"})
        return data.get("results", [])[:10] if data else []
    
    def get_native_content(self, lang_code: str) -> List[Dict]:
        """Get popular content in native language."""
        lang_map = {"de": "de", "fr": "fr", "nl": "nl", "sv": "sv", "no": "no", "da": "da"}
        original_lang = lang_map.get(lang_code)
        
        if not original_lang:
            return []
        
        data = self._get("/discover/movie", {
            "with_original_language": original_lang,
            "sort_by": "popularity.desc",
            "vote_count.gte": 10,
        })
        return data.get("results", [])[:10] if data else []
    
    def get_trending_global(self) -> List[Dict]:
        """Get globally trending movies."""
        data = self._get("/trending/movie/day")
        return data.get("results", [])[:15] if data else []
    
    def get_airing_today(self, lang_code: str = "en") -> List[Dict]:
        """Get TV shows airing today."""
        timezone_map = {
            "en": "America/New_York",
            "de": "Europe/Berlin",
            "fr": "Europe/Paris",
            "nl": "Europe/Amsterdam",
        }
        tz = timezone_map.get(lang_code, "America/New_York")
        data = self._get("/tv/airing_today", {"timezone": tz})
        return data.get("results", [])[:10] if data else []
    
    def get_regional_content(self, region: str, lang_code: str) -> List[Dict]:
        """Get comprehensive regional content (combines all endpoints)."""
        content = []
        
        # 1. Now Playing (theatrical releases - high intent)
        now_playing = self.get_now_playing(region)
        for m in now_playing:
            content.append({
                "title": m.get("title"),
                "tmdb_id": m.get("id"),
                "type": "movie",
                "source": "now_playing",
                "popularity": m.get("popularity", 0),
                "year": (m.get("release_date") or "")[:4],
            })
        
        # 2. Native language content (for non-English)
        if lang_code != "en":
            native = self.get_native_content(lang_code)
            for m in native:
                content.append({
                    "title": m.get("title"),
                    "original_title": m.get("original_title"),
                    "tmdb_id": m.get("id"),
                    "type": "movie",
                    "source": "native",
                    "popularity": m.get("popularity", 0),
                    "year": (m.get("release_date") or "")[:4],
                })
        
        # 3. Global trending
        trending = self.get_trending_global()
        for m in trending:
            content.append({
                "title": m.get("title"),
                "tmdb_id": m.get("id"),
                "type": "movie",
                "source": "trending",
                "popularity": m.get("popularity", 0),
                "year": (m.get("release_date") or "")[:4],
            })
        
        # 4. TV Airing today
        tv = self.get_airing_today(lang_code)
        for t in tv:
            content.append({
                "title": t.get("name"),
                "tmdb_id": t.get("id"),
                "type": "tv",
                "source": "airing",
                "popularity": t.get("popularity", 0),
                "year": (t.get("first_air_date") or "")[:4],
            })
        
        # Deduplicate by tmdb_id
        seen = set()
        unique_content = []
        for c in content:
            if c["tmdb_id"] not in seen:
                seen.add(c["tmdb_id"])
                unique_content.append(c)
        
        # Sort by popularity
        unique_content.sort(key=lambda x: x["popularity"], reverse=True)
        
        return unique_content

# ============================================================================
# SMART SEARCH v8.0 (Validated Search Terms)
# ============================================================================

class SmartSearch:
    def __init__(self):
        self.tmdb = TMDBClient()
        self.groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.ai_terms_cache = []
        self.last_ai_generation = None
    
    def generate_ai_search_terms(self) -> List[str]:
        """Hybrid: Comprehensive base terms + AI-generated variations."""
        
        # COMPREHENSIVE BASE TERMS - ALL contain movie/show/film/series keywords
        base_terms = [
            # === MOVIES - Underrated/Overlooked ===
            "underrated movie",
            "underrated movies",
            "most underrated movie",
            "criminally underrated movie",
            "overlooked movie",
            "overlooked movies",
            "hidden gem movie",
            
            # === MOVIES - Ratings ===
            "10/10 movie",
            "perfect movie",
            "best movie ever",
            "best movies ever",
            "greatest movies ever",
            
            # === MOVIES - Lists/Rankings ===
            "my top 10 movies",
            "my top movies",
            "movie tier list",
            "movie ranking",
            "best movies 2025",
            "best movies 2025 ranked",
            "top movies 2025",
            "movies of 2025 ranked",
            "must watch movies",
            "movies everyone should watch",
            
            # === MOVIES - Recommendations ===
            "movie recommendations",
            "recommend me a movie",
            "what movie to watch",
            "good movies to watch",
            
            # === TV SHOWS - Underrated/Overlooked ===
            "underrated show",
            "underrated shows",
            "underrated tv show",
            "most underrated show",
            "criminally underrated show",
            "overlooked show",
            "hidden gem show",
            
            # === TV SHOWS - Ratings ===
            "10/10 show",
            "perfect show",
            "best show ever",
            "best shows ever",
            "best tv shows",
            
            # === TV SHOWS - Lists/Rankings ===
            "my top 10 shows",
            "tv show tier list",
            "show tier list",
            "best shows 2025",
            "best tv shows 2025",
            "best shows 2025 ranked",
            "tv shows 2025 ranked",
            "must watch shows",
            "must watch series",
            "binge worthy shows",
            
            # === TV SHOWS - Recommendations ===
            "show recommendations",
            "tv show recommendations",
            "recommend me a show",
            "what show to watch",
            "series recommendations",
        ]
        
        # If no AI available, return base terms
        if not self.groq_client:
            return base_terms
        
        # Only regenerate AI variations every 30 minutes
        if self.last_ai_generation and (datetime.now(timezone.utc) - self.last_ai_generation).seconds < 1800:
            return base_terms + self.ai_terms_cache
        
        # Ask AI to generate MORE variations
        prompt = """Generate 30 SHORT search terms (2-4 words) for finding viral MOVIE and TV SHOW posts on Twitter.

STRICT RULE: Every term MUST contain one of these EXACT words:
- movie, movies, film, films (for movies)
- show, shows, series, tv (for TV)

❌ REJECT: "cinematic gem", "peak cinema", "banger" - missing required keyword!
✅ ACCEPT: "hidden gem movie", "peak cinema movie", "absolute banger show"

GENERATE 15 MOVIE TERMS + 15 TV SHOW TERMS:

MOVIE PATTERNS TO FOLLOW:
- "underrated movie" / "overlooked movies"
- "best movies 2025" / "top movies ranked"
- "movie tier list" / "movie recommendations"
- "10/10 movie" / "perfect movie"

TV SHOW PATTERNS TO FOLLOW:
- "underrated show" / "overlooked series"
- "best shows 2025" / "tv shows ranked"
- "show tier list" / "series recommendations"
- "binge worthy shows" / "must watch series"

RULES:
1. 2-4 words MAX
2. MUST contain: movie/movies/film OR show/shows/series/tv
3. NO emojis, NO hashtags, NO sentences

Return JSON array: ["term1", "term2", ...]"""

        try:
            response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=3000,
            )
            
            result = response.choices[0].message.content.strip()
            
            # Handle <think> block
            if "<think>" in result:
                import re
                think_match = re.search(r'<think>(.*?)</think>', result, re.DOTALL)
                if think_match:
                    thinking = think_match.group(1).strip()
                    print(f"\n🧠 [AI VARIATION THINKING]:\n{thinking[:400]}...\n")
                result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
            
            # Parse JSON
            import json
            if "[" in result and "]" in result:
                start = result.index("[")
                end = result.rindex("]") + 1
                raw_variations = json.loads(result[start:end])
                
                # VALIDATE: Filter out terms without required keywords
                required_keywords = ['movie', 'movies', 'film', 'films', 'show', 'shows', 'series', 'tv']
                variations = [
                    term for term in raw_variations 
                    if any(kw in term.lower() for kw in required_keywords)
                ]
                
                rejected = len(raw_variations) - len(variations)
                if rejected > 0:
                    print(f"[AI Search] Filtered out {rejected} terms missing keywords")
                
                self.ai_terms_cache = variations
                self.last_ai_generation = datetime.now(timezone.utc)
                
                # Deduplicate: combine and keep unique terms
                all_terms = list(dict.fromkeys(base_terms + variations))
                print(f"[AI Search] {len(all_terms)} unique honeypot terms ready")
                return all_terms
        except Exception as e:
            print(f"[AI Search] Error: {e}")
        
        return base_terms
        
    def generate_search_terms(self, lang_code: str, region: str) -> int:
        """Generate validated search terms for a specific language."""
        templates = SEARCH_TEMPLATES.get(lang_code, SEARCH_TEMPLATES["en"])
        content = self.tmdb.get_regional_content(region, lang_code)
        
        new_terms = 0
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 1. Generate trending title terms
            if "trending" in templates:
                for item in content[:15]:  # Top 15 content
                    title = item.get("title")
                    if not title:
                        continue
                    
                    for template in templates["trending"]:
                        term = template.format(title=title)
                        try:
                            cursor.execute("""
                                INSERT INTO search_term_pool 
                                (term, lang_code, category, title, tmdb_id, popularity)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (term, lang_code, "trending", title, item["tmdb_id"], item["popularity"]))
                            new_terms += 1
                        except sqlite3.IntegrityError:
                            pass
            
            # 2. Generate recommendation terms
            if "recommendation" in templates:
                for template in templates["recommendation"]:
                    try:
                        cursor.execute("""
                            INSERT INTO search_term_pool 
                            (term, lang_code, category, title, tmdb_id, popularity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (template, lang_code, "recommendation", "Generic", 0, 80))
                        new_terms += 1
                    except sqlite3.IntegrityError:
                        pass
            
            # 3. Generate frustration terms (high intent!)
            if "frustration" in templates:
                for template in templates["frustration"]:
                    try:
                        cursor.execute("""
                            INSERT INTO search_term_pool 
                            (term, lang_code, category, title, tmdb_id, popularity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (template, lang_code, "frustration", "Generic", 0, 95))  # High priority
                        new_terms += 1
                    except sqlite3.IntegrityError:
                        pass
            
            # 4. Generate intent terms
            if "intent" in templates:
                for template in templates["intent"]:
                    try:
                        cursor.execute("""
                            INSERT INTO search_term_pool 
                            (term, lang_code, category, title, tmdb_id, popularity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (template, lang_code, "intent", "Generic", 0, 90))
                        new_terms += 1
                    except sqlite3.IntegrityError:
                        pass
            
            # 5. Generate viral list terms (HIGH ENGAGEMENT posts!)
            if "viral_lists" in templates:
                for template in templates["viral_lists"]:
                    try:
                        cursor.execute("""
                            INSERT INTO search_term_pool 
                            (term, lang_code, category, title, tmdb_id, popularity)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (template, lang_code, "viral_lists", "ViralList", 0, 100))  # Highest priority!
                        new_terms += 1
                    except sqlite3.IntegrityError:
                        pass
            
            conn.commit()
        
        print(f"[SmartSearch] Generated {new_terms} search terms for lang:{lang_code}")
        return new_terms
    
    def get_next_term(self, lang_code: str, region: str) -> Dict[str, Any]:
        """Get the next best search term for current language."""
        import random
        
        # 60% chance: Use AI-generated creative terms (highest value!)
        if random.random() < 0.6:
            ai_terms = self.generate_ai_search_terms()
            if ai_terms:
                term = random.choice(ai_terms)
                print(f"[AI Search] Using AI-generated term: {term}")
                return {
                    "search_term": term,
                    "title": "AI-Generated",
                    "category": "ai_creative",
                    "tmdb_id": 0,
                    "lang_code": lang_code,
                }
        
        # v9.0: ALWAYS use AI-generated list-based terms (not TMDB specific titles)
        # The AI prompt is designed for honeypot terms like "top 50 movies", "my movie tier list"
        ai_terms = self.generate_ai_search_terms()
        if ai_terms:
            import random
            term = random.choice(ai_terms)
            print(f"[AI Search v9.0] Using list-based term: {term}")
            return {
                "search_term": term,
                "title": "AI-Generated",
                "category": "ai_list",
                "tmdb_id": 0,
                "lang_code": lang_code,
            }
        
        # Ultimate fallback - still use list-based terms, not movie titles
        # Fallback terms covering all 6 viral categories
        fallback_list_terms = [
            # Category 1: Rating Posts (highest viral potential)
            "10/10 movie", "10/10 🍿", "perfect movie", "masterpiece movie",
            # Category 2: Hot Takes & Controversy
            "underrated movie", "overhated movie", "slept on movie", "unpopular opinion movie",
            # Category 3: Top/Best Lists
            "top 50 movies", "best movies of all time", "my movie tier list", "movies everyone should watch",
            # Category 4: Genre-Specific
            "best horror movies", "best crime shows", "top thriller movies",
            # Category 5: Polls & Comparisons
            "choose wisely movie", "pick one movie",
            # Category 6: Watch Intent
            "what should I watch", "movie recommendations", "binge worthy shows", "recommend me a movie"
        ]
        import random
        return {
            "search_term": random.choice(fallback_list_terms),
            "title": "Fallback",
            "category": "list_fallback",
            "tmdb_id": 0,
            "lang_code": lang_code,
        }

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TweetAnalysisRequest(BaseModel):
    tweet_id: str
    tweet_text: str
    user_handle: str
    parent_text: Optional[str] = None
    thread_replies: Optional[List[str]] = None  # NEW: Existing replies in thread
    user_bio: Optional[str] = None              # NEW: User profile bio
    movie_title: Optional[str] = None
    search_category: Optional[str] = None       # NEW: frustration, intent, trending, etc.
    search_lang: Optional[str] = None

class TweetAnalysisResponse(BaseModel):
    action: str
    reason: str
    draft: Optional[str] = None
    language: str
    trend_injected: Optional[str] = None
    sentiment: Optional[str] = None  # NEW: detected sentiment

class TrendUpdateRequest(BaseModel):
    region: str
    trends: List[str]

class ScheduleResponse(BaseModel):
    region: str
    location: str
    language: str
    lang_code: str
    tmdb_region: str
    current_trends: List[str]

class SmartSearchResponse(BaseModel):
    search_term: str
    title: str
    category: str
    tmdb_id: int
    lang_code: str

# ============================================================================
# ADVANCED LLM CLIENT (Sophisticated AI Orchestrator)
# ============================================================================

class LLMClient:
    def __init__(self):
        if not GROQ_API_KEY:
            print("WARNING: GROQ_API_KEY not set. LLM calls will fail.")
        self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    
    def _detect_sentiment(self, tweet_text: str, category: str) -> str:
        """Detect the emotional sentiment of the tweet."""
        tweet_lower = tweet_text.lower()
        
        # Frustration indicators
        frustration_words = ["hate", "can't", "won't", "expensive", "sucks", "terrible", "annoyed", "frustrated", "ugh", "tired of", "teuer", "cher", "duur"]
        if any(word in tweet_lower for word in frustration_words) or category == "frustration":
            return "frustrated"
        
        # Excitement indicators
        excitement_words = ["amazing", "love", "best", "incredible", "wow", "omg", "can't wait", "excited", "geil", "génial", "vet"]
        if any(word in tweet_lower for word in excitement_words):
            return "excited"
        
        # Seeking indicators
        seeking_words = ["where", "how to", "looking for", "need", "anyone know", "recommend", "suggestion", "wo", "où", "waar"]
        if any(word in tweet_lower for word in seeking_words) or category in ["intent", "recommendation"]:
            return "seeking"
        
        # Neutral/discussing
        return "neutral"
    
    def analyze_and_draft(
        self,
        tweet_text: str,
        lang_code: str,
        region: str,
        trends: List[str],
        movie_title: str = None,
        search_category: str = None,
        parent_text: Optional[str] = None,
        thread_replies: Optional[List[str]] = None,
        user_bio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sophisticated analysis with context awareness and sentiment matching."""
        
        sentiment = self._detect_sentiment(tweet_text, search_category or "")
        
        if not self.client:
            return {
                "action": "REPLY",
                "reason": "MOCK: Intent detected",
                "draft": f"[MOCK] Check out {SITE_URL}!",
                "trend": trends[0] if trends else None,
                "sentiment": sentiment
            }
        
        lang_name = LANG_NAMES.get(lang_code, "English")
        
        # Build context blocks
        context_blocks = []
        
        if movie_title:
            context_blocks.append(f"SEARCH CONTEXT: User searched for '{movie_title}'")
        
        if search_category:
            category_hints = {
                "frustration": "User seems FRUSTRATED with streaming services - empathize and offer solution",
                "intent": "User is ACTIVELY SEEKING where to watch - direct recommendation",
                "recommendation": "User wants RECOMMENDATIONS - be helpful and suggest the site",
                "trending": "User is DISCUSSING a trending title - join naturally",
            }
            context_blocks.append(f"INTENT: {category_hints.get(search_category, 'General discussion')}")
        
        if sentiment:
            sentiment_instructions = {
                "frustrated": "Match their frustration, validate their feelings, then offer the solution as relief",
                "excited": "Match their excitement! Be enthusiastic about the content too",
                "seeking": "Be helpful and direct - they want an answer, give them one",
                "neutral": "Be casual and friendly, like a friend sharing a tip",
            }
            context_blocks.append(f"SENTIMENT: {sentiment_instructions.get(sentiment, '')}")
        
        if thread_replies:
            context_blocks.append(f"EXISTING REPLIES ({len(thread_replies)}): The thread already has replies. Make yours unique and add value.")
        
        if user_bio:
            context_blocks.append(f"USER BIO: '{user_bio[:100]}' - Reference their interests if relevant")
        
        context_section = "\n".join(context_blocks) if context_blocks else "No additional context."
        
        system_prompt = f"""You are a conversion optimization expert AND genuine movie lover. Your goal is to get people to CLICK on streamixapp.pages.dev.

=== YOUR MISSION ===
Craft a reply that makes someone WANT to visit streamixapp.pages.dev. Not just mention it - make them genuinely curious to click.

=== THE TWEET ===
"{tweet_text}"

=== THINK BEFORE YOU REPLY ===
Before writing, reason through these questions:

1. **WHO is this person?**
   - Are they a casual viewer or cinephile?
   - Are they frustrated, excited, seeking recommendations?
   - What would resonate with THEM specifically?

2. **WHAT problem can I solve?**
   - Can't find where to watch something? → I have the answer
   - Tired of expensive subscriptions? → I have a free alternative
   - Looking for quality? → I can confirm it's 4K
   - Want no-hassle streaming? → No signup required

3. **HOW do I make them CLICK?**
   - Build rapport FIRST (agree, validate, relate)
   - THEN naturally mention the solution
   - Make it sound like insider knowledge, not an ad
   - Create curiosity or urgency

4. **What would make ME click this reply?**
   - Genuine enthusiasm is contagious
   - Specific details are more convincing than generic claims  
   - Solving their exact problem > listing random features

=== CONVERSION PSYCHOLOGY ===

❌ LOW CONVERSION (sounds like an ad):
"Check out streamixapp.pages.dev for free movies in 4K!"

✅ HIGH CONVERSION (sounds like a friend):
"yo I literally watched this last night on streamixapp.pages.dev - 4K and no account needed, wild that it's free"

The difference:
- Personal experience ("I watched")
- Specific timing ("last night")
- Genuine surprise ("wild that it's free")
- Natural language ("yo", "literally")

=== CONTEXT ===
{context_section}

=== HARD RULES (DO NOT BREAK) ===
1. MAX 280 characters (USE this space wisely - more words = more persuasion)
2. Include streamixapp.pages.dev EXACTLY ONCE
3. ZERO hashtags
4. Only reference movies EXPLICITLY in the tweet (never guess)
5. If no movie named, use "this" or "it" - NEVER invent a title
6. Sound human, not promotional

=== USE YOUR 280 CHARACTERS WISELY ===
You have 280 chars - that's enough to:
- Build genuine rapport (agree, empathize, relate)
- Share a personal experience ("I watched this last week...")
- Explain WHY the site is good ("no account needed, just clicked and it played")
- Add social proof ("been using it for months")
- Create curiosity ("wild that it's actually free")

Short replies look like bots. Longer, natural replies get clicks.

=== SKIP IF ===
❌ Sports, gaming, music, politics → SKIP
❌ Brand/corporate accounts → SKIP
❌ Not movie/TV related → SKIP

=== EXAMPLES OF PERSUASIVE REPLIES (USE FULL 280 CHARS) ===

Tweet: "I need something good to watch tonight"
🧠 Thinking: "Active seeker = highest intent. Be helpful, give the solution, add credibility."
Reply: "honestly streamixapp.pages.dev has been my go-to lately. everything's free, no account needed, and the quality is actually really good. found so many hidden gems there that I never would've paid for on Netflix"

Tweet: "The Aviator is Scorsese's most underrated film"
🧠 Thinking: "Cinephile making a take. Validate first, add personal experience, then mention the site naturally."
Reply: "100% agree, it's criminally overlooked. Leo's performance in this is insane. just rewatched it on streamixapp.pages.dev in 4K - no ads, no signup, just hit play. the way Scorsese captures Hughes' mania is unmatched"

Tweet: "Netflix just raised prices AGAIN 😤"
🧠 Thinking: "Frustration = opportunity. Deep empathy, share my story, offer relief naturally."
Reply: "felt this SO hard. I cancelled mine last month after they raised it again. switched to streamixapp.pages.dev and honestly? it works better. everything's free, no popups, and the 4K quality is legit. wish I'd switched sooner"

Tweet: "My top 5 movies of 2024: 1. Dune Part Two 2. Civil War..."
🧠 Thinking: "Movie list = engaged audience. Join the conversation, pick popular movie, share experience."
Reply: "Dune Part Two in 4K was a whole experience. watched it on streamixapp.pages.dev - no signup, just clicked and it started playing immediately. the visuals on a big screen with that quality... insane. solid list btw"

Tweet: "what's a movie that genuinely changed your perspective on life?"
🧠 Thinking: "Deep question = thoughtful response. Be genuine, share something personal, mention site naturally."
Reply: "Eternal Sunshine honestly hit different. the way it explores memory and love messed me up for days. rewatched it recently on streamixapp.pages.dev (free, no account) and it hit even harder the second time"

=== OUTPUT (STRICT JSON) ===
Movie/TV: {{"action": "REPLY", "reason": "2-5 words", "draft": "your persuasive 280-char reply"}}
Skip: {{"action": "SKIP", "reason": "why skipping", "draft": null}}

IMPORTANT: URL MUST BE LOWERCASE: streamixapp.pages.dev
"""


        user_message = f"Tweet: {tweet_text}"
        if parent_text:
            user_message += f"\n\nParent Tweet (context): {parent_text}"
        if thread_replies:
            user_message += f"\n\nExisting replies in thread: {'; '.join(thread_replies[:3])}"

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,  # Slightly higher for more natural variation
                max_tokens=2000  # Increased for reasoning models (think block + JSON)
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract and log "Thinking" process (DeepSeek/Qwen Reasoning)
            if "<think>" in result_text:
                import re
                think_match = re.search(r'<think>(.*?)</think>', result_text, re.DOTALL)
                if think_match:
                    thinking_content = think_match.group(1).strip()
                    print(f"\n🧠 [AI THOUGHT PROCESS]:\n{thinking_content}\n")
                    # Remove the thinking block to get pure JSON
                    result_text = re.sub(r'<think>.*?</think>', '', result_text, flags=re.DOTALL).strip()

            # Clean up markdown if present (more robustly)
            import re
            
            # 1. Remove code blocks
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if code_block_match:
                result_text = code_block_match.group(1)
            else:
                # 2. Fallback: Find first { and last }
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
            
            result = json.loads(result_text)
            
            # POST-PROCESSING: Fix formatting issues
            if result.get("draft"):
                draft = result["draft"]
                
                # 1. Force lowercase URL
                draft = draft.replace("Streamixapp.pages.dev", "streamixapp.pages.dev")
                draft = draft.replace("STREAMIXAPP.PAGES.DEV", "streamixapp.pages.dev")
                
                # 2. Fix missing space before hyphen (e.g., "dev-4K" -> "dev - 4K")
                # This catches "streamixapp.pages.dev-4K" or "dev-free"
                draft = re.sub(r'(streamixapp\.pages\.dev)-([a-zA-Z0-9])', r'\1 - \2', draft)
                
                result["draft"] = draft

            result["sentiment"] = sentiment
            return result
            
        except json.JSONDecodeError as e:
            print(f"LLM JSON Parse Error: {e}")
            print(f"Raw response: {result_text[:200] if 'result_text' in dir() else 'N/A'}")
            return {"action": "SKIP", "reason": f"JSON parse error", "draft": None, "sentiment": sentiment}
        except Exception as e:
            print(f"LLM Error: {e}")
            return {"action": "SKIP", "reason": f"Error: {e}", "draft": None, "sentiment": sentiment}

# ============================================================================
# CORE LOGIC
# ============================================================================

def get_current_schedule() -> Dict[str, Any]:
    """Get the current target based on UTC hour."""
    now = datetime.now(timezone.utc)
    hour = now.hour
    slot = DAILY_SCHEDULE[hour]
    return {
        "region": slot["region"],
        "location": slot["location"],
        "lang_code": slot["lang"],
        "language": LANG_NAMES.get(slot["lang"], "English"),
        "tmdb_region": slot["tmdb_region"],
    }

def check_duplicate(tweet_id: str, user_handle: str) -> tuple:
    """Check if we should skip this tweet."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM replied_tweets WHERE tweet_id = ?", (tweet_id,))
        if cursor.fetchone(): 
            return True, "Already replied"
        
        cursor.execute("SELECT 1 FROM scanned_tweets WHERE tweet_id = ?", (tweet_id,))
        if cursor.fetchone(): 
            return True, "Already scanned"
        
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        cursor.execute("SELECT COUNT(*) FROM replied_tweets WHERE user_handle = ? AND timestamp > ?", 
                      (user_handle, yesterday.isoformat()))
        if cursor.fetchone()[0] >= 2: 
            return True, "User cooldown"
    
    return False, ""

def log_reply(tweet_id: str, user_handle: str, region: str, language: str, reply_text: str, search_term: str = None, sentiment: str = None):
    """Log a successful reply."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO replied_tweets (tweet_id, user_handle, region, language, reply_text, search_term, sentiment) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (tweet_id, user_handle, region, language, reply_text, search_term, sentiment)
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
                    return trends[:10]  # Top 10 only
            except Exception:
                pass
    
    # Fallback trends
    return ["#Streaming", "#Movies", "#WatchOnline", "#Cinema", "#Film"]

def update_trend_cache(region: str, trends: List[str]):
    """Update trend cache for a region."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO trend_cache (region, trends, harvested_at) VALUES (?, ?, ?)",
            (region, json.dumps(trends), datetime.now(timezone.utc).isoformat())
        )
        conn.commit()

def get_stats() -> Dict[str, Any]:
    """Get bot statistics."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM replied_tweets")
        total = cursor.fetchone()[0]
        
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute("SELECT COUNT(*) FROM replied_tweets WHERE timestamp > ?", (today.isoformat(),))
        today_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT user_handle) FROM replied_tweets")
        unique = cursor.fetchone()[0]
        
        cursor.execute("SELECT language, COUNT(*) FROM replied_tweets GROUP BY language")
        langs = dict(cursor.fetchall())
        
        cursor.execute("SELECT sentiment, COUNT(*) FROM replied_tweets WHERE sentiment IS NOT NULL GROUP BY sentiment")
        sentiments = dict(cursor.fetchall())
        
    return {
        "total_replies": total, 
        "replies_today": today_count, 
        "unique_users": unique, 
        "by_language": langs,
        "by_sentiment": sentiments,
        "estimated_impressions": today_count * 150,  # X Premium boost estimate
    }

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="XBot Brain v8.0", version="8.0.0", description="Million Visitor Engine")

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
    return {
        "status": "online", 
        "service": "XBot Brain v8.0 (Million Visitor Engine)",
        "tier1_languages": list(LANG_NAMES.keys()),
        "features": ["TMDB Regional", "Sentiment Analysis", "Native Phrases", "Thread Context"]
    }

@app.get("/schedule", response_model=ScheduleResponse)
def get_schedule():
    """Get current schedule with regional targeting."""
    schedule = get_current_schedule()
    trends = get_cached_trends(schedule["region"])
    return ScheduleResponse(
        region=schedule["region"],
        location=schedule["location"],
        language=schedule["language"],
        lang_code=schedule["lang_code"],
        tmdb_region=schedule["tmdb_region"],
        current_trends=trends
    )

@app.get("/smart-search", response_model=SmartSearchResponse)
def get_search_term():
    """Get the next best validated search term."""
    schedule = get_current_schedule()
    lang_code = schedule["lang_code"]
    region = schedule["tmdb_region"]
    
    term_data = smart_search.get_next_term(lang_code, region)
    
    return SmartSearchResponse(
        search_term=term_data["search_term"],
        title=term_data["title"],
        category=term_data["category"],
        tmdb_id=term_data["tmdb_id"],
        lang_code=term_data["lang_code"]
    )

@app.post("/analyze", response_model=TweetAnalysisResponse)
def analyze_tweet(request: TweetAnalysisRequest):
    """Analyze tweet with sophisticated AI orchestration."""
    is_duplicate, reason = check_duplicate(request.tweet_id, request.user_handle)
    if is_duplicate:
        return TweetAnalysisResponse(action="SKIP", reason=reason, draft=None, language="", trend_injected=None)
    
    schedule = get_current_schedule()
    trends = get_cached_trends(schedule["region"])
    
    reply_lang = request.search_lang if request.search_lang else schedule["lang_code"]
    
    result = llm_client.analyze_and_draft(
        tweet_text=request.tweet_text,
        lang_code=reply_lang,
        region=schedule["region"],
        trends=trends,
        movie_title=request.movie_title,
        search_category=request.search_category,
        parent_text=request.parent_text,
        thread_replies=request.thread_replies,
        user_bio=request.user_bio,
    )
    
    if result["action"] == "SKIP":
        log_scanned(request.tweet_id, result.get("reason", "Skipped by LLM"))
    
    return TweetAnalysisResponse(
        action=result["action"],
        reason=result["reason"],
        draft=result.get("draft"),
        language=schedule["language"],
        trend_injected=result.get("trend"),
        sentiment=result.get("sentiment")
    )

class LogReplyRequest(BaseModel):
    tweet_id: str
    user_handle: str
    reply_text: str
    search_term: Optional[str] = None
    sentiment: Optional[str] = None

@app.post("/log-reply")
def log_successful_reply(request: LogReplyRequest):
    """Log a successful reply with analytics."""
    schedule = get_current_schedule()
    log_reply(
        tweet_id=request.tweet_id,
        user_handle=request.user_handle,
        region=schedule["region"],
        language=schedule["lang_code"],
        reply_text=request.reply_text,
        search_term=request.search_term,
        sentiment=request.sentiment
    )
    return {"status": "logged", "estimated_reach": 150}

class LocationSelectRequest(BaseModel):
    target_location: str
    options: List[str]

@app.post("/select-location")
def select_location(request: LocationSelectRequest):
    """Select the best location match from available options."""
    target = request.target_location.lower()
    options = request.options
    
    best_index = -1
    best_score = 0
    
    for i, opt in enumerate(options):
        opt_lower = opt.lower()
        
        # Exact match
        if target == opt_lower:
            return {"index": i, "selected": opt, "match_type": "exact"}
        
        # Target is contained in option (e.g., "London" in "London, UK")
        if target in opt_lower:
            score = len(target) / len(opt_lower)
            if score > best_score:
                best_score = score
                best_index = i
        
        # Option starts with target
        elif opt_lower.startswith(target):
            score = 0.9
            if score > best_score:
                best_score = score
                best_index = i
        
        # First word matches
        elif opt_lower.split(",")[0].strip() == target or opt_lower.split(" ")[0] == target:
            score = 0.8
            if score > best_score:
                best_score = score
                best_index = i
    
    if best_index >= 0:
        return {"index": best_index, "selected": options[best_index], "match_type": "fuzzy", "score": best_score}
    
    return {"index": -1, "selected": None, "match_type": "none"}

@app.post("/update-trends")
def update_trends(request: TrendUpdateRequest):
    """Update trend cache for a region."""
    update_trend_cache(request.region, request.trends)
    return {"status": "updated", "region": request.region, "trends_count": len(request.trends)}

@app.get("/stats")
def get_statistics_endpoint():
    """Get comprehensive statistics."""
    return get_stats()

@app.get("/regional-content")
def get_regional_content():
    """Get current regional trending content."""
    schedule = get_current_schedule()
    tmdb = TMDBClient()
    content = tmdb.get_regional_content(schedule["tmdb_region"], schedule["lang_code"])
    return {
        "region": schedule["region"],
        "lang_code": schedule["lang_code"],
        "content_count": len(content),
        "content": content[:20]
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    stats = get_stats()
    schedule = get_current_schedule()
    return {
        "status": "healthy",
        "version": "8.0.0",
        "current_region": schedule["region"],
        "current_lang": schedule["lang_code"],
        "replies_today": stats["replies_today"],
        "estimated_daily_reach": stats["replies_today"] * 150
    }
