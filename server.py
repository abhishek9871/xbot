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
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv # Added for environment variable loading

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables
load_dotenv()

# --- Configurations ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
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
    "en": [
        '"where to watch" free',
        '"best free streaming" site',
        '"netflix alternative" free',
        '"netflix too expensive"',
        '"streaming site" no ads',
    ],
    "fr": [
        '"où regarder" film gratuit',
        '"site streaming gratuit"',
        '"alternative netflix gratuit"',
        '"netflix trop cher"',
    ],
    "de": [
        '"wo kann ich schauen" kostenlos',
        '"streaming seite kostenlos"',
        '"netflix alternative kostenlos"',
        '"netflix zu teuer"',
    ],
    "es": [
        '"dónde ver" películas gratis',
        '"sitio streaming gratis"',
        '"alternativa netflix gratis"',
        '"netflix muy caro"',
    ],
    "pt": [
        '"onde assistir" filme grátis',
        '"site streaming grátis"',
        '"alternativa netflix grátis"',
        '"netflix muito caro"',
    ],
    "it": [
        '"dove guardare" film gratis',
        '"sito streaming gratuito"',
        '"alternativa netflix gratis"',
    ],
    "nl": [
        '"waar kijken" gratis',
        '"gratis streaming site"',
        '"netflix alternatief gratis"',
    ],
    "pl": [
        '"gdzie oglądać" za darmo',
        '"darmowy streaming"',
        '"alternatywa netflix"',
    ],
    "ja": [
        "映画 無料 視聴",
        "無料 ストリーミング サイト",
        "Netflix 代替 無料",
        "どこで見れる 映画",
        "無料で映画を見る方法",
    ],
    "ko": [
        "영화 무료 보기",
        "무료 스트리밍 사이트",
        "넷플릭스 대안 무료",
        "어디서 볼 수 있어",
        "드라마 무료 시청",
    ],
    "id": [
        "nonton film gratis",
        "situs streaming gratis",
        "alternatif netflix gratis",
        "dimana nonton film",
    ],
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
# PYDANTIC MODELS
# ============================================================================

class TweetAnalysisRequest(BaseModel):
    tweet_id: str
    tweet_text: str
    user_handle: str
    parent_text: Optional[str] = None

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
    keywords: List[str]
    current_trends: List[str]

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
        parent_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze tweet intent and draft a reply."""
        
        if not self.client:
            # Mock response for testing without API key
            return {
                "action": "REPLY",
                "reason": "Movie/TV intent detected",
                "draft": f"[MOCK] Check out {SITE_URL} for free streaming!",
                "trend": trends[0] if trends else None
            }
        
        lang_name = LANG_NAMES.get(lang_code, "English")
        trends_str = ", ".join(trends[:5]) if trends else "None"
        
        # Get a random reply template for variation
        reply_templates = [
            "I use {site} for this - works great!",
            "Been using {site} for months, no complaints",
            "{site} has it, saved me so much time",
            "Try {site} - that's what I use",
            "Found it on {site} last week",
            "Someone recommended {site} to me, solid choice",
            "{site} is underrated for this",
            "My friends use {site}, works well",
        ]
        import random
        template_hint = random.choice(reply_templates)
        
        system_prompt = f"""You are a NATIVE {lang_name} speaker and movie enthusiast on X (Twitter).
You are located in {region}. You speak ONLY {lang_name}.

=== CRITICAL RULES ===

RULE 1 - LANGUAGE: Your ENTIRE reply MUST be in {lang_name}. 
- If {lang_name} is French, write ENTIRELY in French
- If {lang_name} is Japanese, write ENTIRELY in 日本語
- If {lang_name} is Korean, write ENTIRELY in 한국어
- If {lang_name} is Spanish, write ENTIRELY in Spanish
- ZERO English words allowed in non-English replies (except the URL)

RULE 2 - TREND INJECTION: You MUST include a hashtag from these local trends:
LOCAL TRENDS: {trends_str}
Pick ONE that relates to movies/entertainment if possible. If none provided, skip hashtag.

RULE 3 - REPLY VARIATION: Each reply must be UNIQUE. Use different phrasings.
Example variation style: "{template_hint}"
DO NOT always say "My go-to is..." - vary your responses!

RULE 4 - NATURAL TONE: Sound like a real person, not a bot or ad.
- Be casual and conversational
- Reference the specific movie/show they mentioned
- Don't be overly enthusiastic or promotional

=== YOUR TASK ===

1. CLASSIFY the tweet:
   - MOVIE_INTENT: Wants to watch movies/TV shows/anime/drama
   - SPORT_INTENT: Wants live sports (skip these)
   - OTHER: Not about streaming (skip these)

2. IF MOVIE_INTENT:
   - Write a short, casual reply in {lang_name}
   - Mention the specific content they asked about
   - Include link: {SITE_URL}
   - Include ONE hashtag from the trends
   - Keep it under 200 characters

3. IF SPORT_INTENT or OTHER:
   - action = "SKIP"

=== EXAMPLES ===

English example: "Just watched it on streamixapp.pages.dev - solid quality! #Netflix"
French example: "Je l'ai trouvé sur streamixapp.pages.dev, ça marche bien #Cinéma"
Japanese example: "streamixapp.pages.dev で見れるよ！画質もいい #映画"
Spanish example: "Yo la vi en streamixapp.pages.dev, sin problemas #Netflix"

=== OUTPUT FORMAT ===
JSON only, no markdown:
{{"action": "REPLY" or "SKIP", "reason": "brief explanation", "draft": "your {lang_name} reply with hashtag" or null, "trend": "hashtag you used" or null}}
"""

        user_message = f"Tweet: {tweet_text}"
        if parent_text:
            user_message += f"\nContext (parent tweet): {parent_text}"

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
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "action": "SKIP",
                "reason": f"LLM error: {str(e)}",
                "draft": None,
                "trend": None
            }

# ============================================================================
# CORE LOGIC
# ============================================================================

def get_current_schedule() -> Dict[str, Any]:
    """Get the current target based on UTC hour."""
    now = datetime.utcnow()
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
        
        # Check if tweet already replied
        cursor.execute("SELECT 1 FROM replied_tweets WHERE tweet_id = ?", (tweet_id,))
        if cursor.fetchone():
            return True, "Already replied to this tweet"
        
        # Check if tweet already scanned
        cursor.execute("SELECT 1 FROM scanned_tweets WHERE tweet_id = ?", (tweet_id,))
        if cursor.fetchone():
            return True, "Already scanned this tweet"
        
        # Check user cooldown (max 2 replies per user per 24h)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        cursor.execute(
            "SELECT COUNT(*) FROM replied_tweets WHERE user_handle = ? AND timestamp > ?",
            (user_handle, yesterday.isoformat())
        )
        count = cursor.fetchone()[0]
        if count >= 2:
            return True, "User cooldown (max 2 replies per 24h)"
    
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
    """Log a scanned tweet (even if skipped)."""
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
            return json.loads(row["trends"])
    return []

def update_trend_cache(region: str, trends: List[str]):
    """Update trend cache for a region."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO trend_cache (region, trends, harvested_at) VALUES (?, ?, ?)",
            (region, json.dumps(trends), datetime.utcnow().isoformat())
        )
        conn.commit()

def get_stats() -> Dict[str, Any]:
    """Get bot statistics."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total replies
        cursor.execute("SELECT COUNT(*) FROM replied_tweets")
        total_replies = cursor.fetchone()[0]
        
        # Replies today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0)
        cursor.execute("SELECT COUNT(*) FROM replied_tweets WHERE timestamp > ?", (today.isoformat(),))
        replies_today = cursor.fetchone()[0]
        
        # Unique users
        cursor.execute("SELECT COUNT(DISTINCT user_handle) FROM replied_tweets")
        unique_users = cursor.fetchone()[0]
        
        # By language
        cursor.execute("SELECT language, COUNT(*) FROM replied_tweets GROUP BY language")
        by_language = dict(cursor.fetchall())
        
    return {
        "total_replies": total_replies,
        "replies_today": replies_today,
        "unique_users": unique_users,
        "by_language": by_language
    }

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="XBot Brain", version="1.0.0")

# CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
llm_client = LLMClient()
init_database()

@app.get("/")
def root():
    """Health check."""
    return {"status": "online", "service": "XBot Brain v1.0"}

@app.get("/schedule", response_model=ScheduleResponse)
def get_schedule():
    """Get current target region, language, and keywords."""
    schedule = get_current_schedule()
    trends = get_cached_trends(schedule["region"])
    
    return ScheduleResponse(
        region=schedule["region"],
        location=schedule["location"],
        language=schedule["language"],
        lang_code=schedule["lang_code"],
        keywords=schedule["keywords"],
        current_trends=trends
    )

@app.post("/analyze", response_model=TweetAnalysisResponse)
def analyze_tweet(request: TweetAnalysisRequest):
    """Analyze a tweet and generate a reply if appropriate."""
    
    # De-duplication check
    is_duplicate, reason = check_duplicate(request.tweet_id, request.user_handle)
    if is_duplicate:
        return TweetAnalysisResponse(
            action="SKIP",
            reason=reason,
            draft=None,
            language="",
            trend_injected=None
        )
    
    # Get current schedule
    schedule = get_current_schedule()
    trends = get_cached_trends(schedule["region"])
    
    # LLM analysis
    result = llm_client.analyze_and_draft(
        tweet_text=request.tweet_text,
        lang_code=schedule["lang_code"],
        region=schedule["region"],
        trends=trends,
        parent_text=request.parent_text
    )
    
    # Log the scan
    if result["action"] == "SKIP":
        log_scanned(request.tweet_id, result["reason"])
    
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
    """Log a successfully posted reply."""
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
    """Update trend cache for a region."""
    update_trend_cache(request.region, request.trends)
    return {"status": "updated", "region": request.region, "trends_count": len(request.trends)}

@app.get("/stats")
def get_statistics():
    """Get bot statistics."""
    return get_stats()

@app.get("/check-health")
def check_health():
    """Check if bot should continue or pause (Sentinel)."""
    stats = get_stats()
    
    # Basic health checks
    warnings = []
    
    if stats["replies_today"] >= 150:
        warnings.append("Daily limit approaching (150)")
    
    return {
        "status": "HEALTHY" if not warnings else "WARNING",
        "warnings": warnings,
        "stats": stats
    }

class LocationSelectRequest(BaseModel):
    target_location: str
    options: List[str]

@app.post("/select-location")
def select_location(request: LocationSelectRequest):
    """Given a list of location options, return which index to click."""
    target = request.target_location.lower()
    target_parts = target.replace(',', ' ').split()
    
    best_match = -1
    best_score = 0
    
    for i, option in enumerate(request.options):
        option_lower = option.lower()
        score = 0
        
        # Exact match
        if target in option_lower:
            score += 10
        
        # Check each part of target
        for part in target_parts:
            if part in option_lower:
                score += 2
        
        # Prefer shorter matches (more specific)
        if score > 0:
            score += max(0, 10 - len(option) // 5)
        
        if score > best_score:
            best_score = score
            best_match = i
    
    if best_match >= 0:
        return {
            "index": best_match,
            "selected": request.options[best_match],
            "confidence": best_score
        }
    else:
        return {
            "index": 0,  # Default to first option
            "selected": request.options[0] if request.options else None,
            "confidence": 0
        }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("Starting XBot Brain Server...")
    print(f"Database: {DATABASE_PATH}")
    print(f"Groq API Key: {'SET' if GROQ_API_KEY else 'NOT SET'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
