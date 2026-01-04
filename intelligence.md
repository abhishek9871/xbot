# XBot v8.0 Intelligence Protocol
## Million Visitor Engine - Tier 1 High-CPM Strategy

---

## 🎯 EXECUTIVE SUMMARY

XBot v8.0 is an advanced AI orchestration system designed to drive 1 million visitors to `streamixapp.pages.dev` through intelligent engagement on X.com. The system focuses exclusively on Tier 1 high-CPM markets (English, German, French, Dutch, Nordic) and uses sophisticated content targeting, sentiment matching, and native-language personalization.

---

## 📊 VALIDATED MARKET DATA (December 2024)

### Language Volume Testing Results

| Language | Code | Daily Volume | Validated Queries |
|----------|------|--------------|-------------------|
| **English** | `en` | 1000+ | `recommend me a movie`, `just watched {title}`, `netflix too expensive` |
| **German** | `de` | 300+ | `Film empfehlen lang:de`, `was schauen lang:de`, `Netflix teuer lang:de` |
| **French** | `fr` | 200+ | `quoi regarder lang:fr`, `Avatar lang:fr`, `Netflix cher lang:fr` |
| **Dutch** | `nl` | 150+ | `wat kijken lang:nl`, `Avatar lang:nl`, `Netflix duur lang:nl` |
| **Nordic** | `sv/no/da` | 20-50 | `{title} lang:sv/no/da` (title-only) |

### High-Intent Query Categories

1. **Frustration (Highest Conversion)**
   - `Netflix too expensive`, `Netflix teuer lang:de`, `Netflix cher lang:fr`
   - Users actively seeking alternatives to paid services
   
2. **Intent (Direct Need)**
   - `where to watch`, `kostenlos streamen lang:de`, `regarder gratuit lang:fr`
   - Users looking for streaming solutions

3. **Recommendation (High Volume)**
   - `recommend me a movie`, `Film empfehlen lang:de`, `quoi regarder lang:fr`
   - Users open to suggestions

4. **Trending (Maximum Reach)**
   - `{TMDB_TITLE}`, `just watched {title}`, `Avatar lang:de`
   - High-volume discussions, great for visibility

---

## 🕐 24-HOUR TIER 1 ROTATION SCHEDULE (UTC)

```
Hour | Region          | Lang | TMDB Region | Priority
-----|-----------------|------|-------------|----------
00   | Los Angeles     | en   | US          | HIGH
01   | Los Angeles     | en   | US          | HIGH
02   | New York        | en   | US          | HIGH
03   | New York        | en   | US          | HIGH
04   | Toronto         | en   | CA          | MEDIUM
05   | Sydney          | en   | AU          | MEDIUM
06   | Sydney          | en   | AU          | MEDIUM
07   | London          | en   | GB          | HIGH
08   | London          | en   | GB          | HIGH
09   | Berlin          | de   | DE          | HIGH
10   | Berlin          | de   | DE          | HIGH
11   | Paris           | fr   | FR          | HIGH
12   | Paris           | fr   | FR          | HIGH
13   | Amsterdam       | nl   | NL          | MEDIUM
14   | Stockholm       | sv   | SE          | LOW (title-only)
15   | Berlin          | de   | DE          | HIGH
16   | Paris           | fr   | FR          | HIGH
17   | London          | en   | GB          | HIGH
18   | London          | en   | GB          | HIGH
19   | Dublin          | en   | IE          | MEDIUM
20   | New York        | en   | US          | HIGH
21   | Chicago         | en   | US          | HIGH
22   | Los Angeles     | en   | US          | HIGH
23   | Los Angeles     | en   | US          | HIGH
```

**Split: 70% English-speaking, 30% European languages**

---

## 🔍 SEARCH TERM TEMPLATES

### English (en)
```javascript
trending: [
    "{title}",
    "just watched {title}",
    "{title} review",
    "watching {title}",
    "{title} was amazing",
]
recommendation: [
    "recommend me a movie",
    "what should I watch tonight",
    "movie recommendations",
    "what to watch",
    "need something to watch",
]
frustration: [
    "netflix too expensive",
    "cancel netflix",
    "netflix sucks",
    "tired of paying for streaming",
]
intent: [
    "where to watch",
    "free streaming",
    "watch movies free",
]
```

### German (de) - All with `lang:de`
```javascript
trending: ["{title} lang:de", "gerade gesehen {title} lang:de"]
recommendation: ["Film empfehlen lang:de", "was schauen lang:de"]
frustration: ["Netflix teuer lang:de", "Netflix kündigen lang:de"]
intent: ["kostenlos streamen lang:de", "kostenlos schauen lang:de"]
```

### French (fr) - All with `lang:fr`
```javascript
trending: ["{title} lang:fr"]
recommendation: ["quoi regarder lang:fr", "film recommander lang:fr"]
frustration: ["Netflix cher lang:fr"]
intent: ["regarder gratuit lang:fr", "streaming gratuit lang:fr"]
```

### Dutch (nl) - All with `lang:nl`
```javascript
trending: ["{title} lang:nl"]
recommendation: ["wat kijken lang:nl", "film aanbevelen lang:nl"]
frustration: ["Netflix duur lang:nl"]
intent: ["gratis kijken lang:nl"]
```

### Nordic (sv/no/da) - Title Only
```javascript
// Low general volume - only use for specific trending titles
trending: ["{title} lang:sv", "{title} lang:no", "{title} lang:da"]
```

---

## 🎬 TMDB CONTENT DISCOVERY

### Multi-Endpoint Strategy

1. **`/movie/now_playing?region=XX`** - Theatrical releases (high intent)
2. **`/discover/movie?with_original_language=XX`** - Native content
3. **`/movie/popular`** - Global buzz
4. **`/tv/airing_today`** - Current TV discussions

### Content Priority
1. Now Playing (people want to watch without cinema ticket cost)
2. Native Language (local audience preference)
3. Trending Global (maximum reach)
4. TV Airing (real-time conversations)

---

## 🧠 AI ORCHESTRATOR PROTOCOL

### Sentiment Detection & Matching

| Detected Sentiment | Bot Response Strategy |
|-------------------|----------------------|
| **Frustrated** | Empathize first, then offer solution |
| **Excited** | Match energy, join enthusiasm |
| **Seeking** | Be helpful and direct |
| **Neutral** | Casual and friendly |

### Context Analysis Inputs
- Tweet text
- Parent tweet (if reply)
- Thread replies (up to 3)
- User bio (interests)
- Search category (frustration/intent/recommendation/trending)

### Reply Rules
1. MAX 180 characters
2. ALWAYS include `streamixapp.pages.dev`
3. NEVER mention competitor names
4. Include ONE trending hashtag
5. Use native language slang/phrases
6. Match tweet sentiment

### Native Language Phrases

**English:**
- Check: "check out", "try", "use"
- Good: "fire", "solid", "goated", "legit"
- React: "fr", "ngl", "tbh", "lowkey"

**German:**
- Check: "schau mal auf", "probier"
- Good: "mega", "geil", "krass", "nice"
- React: "echt", "safe"

**French:**
- Check: "regarde sur", "essaie"
- Good: "trop bien", "génial", "ouf"
- React: "franchement", "grave"

**Dutch:**
- Check: "kijk op", "probeer"
- Good: "vet", "chill", "top"
- React: "echt", "serieus"

---

## 📈 CONVERSION FUNNEL (WITH X PREMIUM)

```
Daily Targetable Posts:     1,700
├── Bot replies to:         800/day (quality focus)
│   ├── Impressions/reply:  150-200 (Premium boost)
│   │   └── Daily Impressions: 120,000 - 160,000
│   │       ├── CTR (AI personalized): 5-10%
│   │       │   └── Daily Clicks: 6,000 - 16,000
│   │       │       └── MONTHLY: 180,000 - 480,000
```

### Path to 1 Million

| Accounts | Monthly Visitors | Time to 1M |
|----------|-----------------|------------|
| 1 Premium | 300,000 | 4 months |
| 2 Premium | 600,000 | 2 months |
| 3 Premium | 900,000 | 5-6 weeks |

---

## ⚙️ OPERATIONAL PARAMETERS

```javascript
CONFIG = {
    MAIN_LOOP_INTERVAL: 45000,      // 45 seconds between scans
    REPLY_COOLDOWN: 75000,          // 75 seconds between replies
    KEYWORD_ROTATE_INTERVAL: 300000, // 5 minutes
    TREND_HARVEST_INTERVAL: 1800000, // 30 minutes
    LOCATION_SWITCH_COOLDOWN: 3600000, // 1 hour
    MAX_REPLIES_PER_HOUR: 6,
    MAX_REPLIES_PER_DAY: 100,
}
```

---

## 🚀 DEPLOYMENT

### Start Server
```bash
cd c:\Users\VASU\Desktop\xbot\active
uvicorn server:app --reload --port 8000
```

### Install Client
1. Install Tampermonkey browser extension
2. Create new script
3. Copy contents of `xbot_client.js`
4. Save and enable

### Endpoints
- `GET /` - Health check
- `GET /schedule` - Current region/language
- `GET /smart-search` - Get next search term
- `POST /analyze` - Analyze tweet & get reply
- `POST /update-trends` - Store harvested trends
- `GET /stats` - Performance statistics
- `GET /regional-content` - Current TMDB trending

---

## 📊 VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 8.0 | 2024-12-31 | Million Visitor Engine, Tier 1 focus, validated lang: operators, sentiment matching, thread context |
| 7.1 | 2024-12-30 | Language-aware targeting, lang: filter fix |
| 7.0 | 2024-12-29 | TMDB integration, smart search |

---

*Last Updated: December 31, 2024*
