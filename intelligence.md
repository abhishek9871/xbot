# X.com Automation Protocol (XAP) v17.0 (Tier 1 High-CPM Focus)
> **Target System:** X.com (Twitter)
> **Goal:** Maximum Ad Revenue Per View (Tier 1 Countries Only)
> **Architecture:** Hybrid Browser-Native (Userscript + Python Brain)
> **Last Verified:** 2025-12-31

---

## 🎯 TIER 1 STRATEGY (CPM-Optimized)

### Ad Revenue Research (Dec 31, 2025)
**OTT/CTV Streaming Website CPM Rates:**

| Priority | Language | Countries | CPM (USD) | Focus % |
|----------|----------|-----------|-----------|---------|
| 🥇 | **English** | USA, UK, Australia, Canada, NZ | **$25-40** | 70% |
| 🥈 | **German** | Germany, Switzerland, Austria | **$20-30** | 10% |
| 🥉 | **French** | France, Belgium, Switzerland | **$18-25** | 8% |
| 4 | **Dutch** | Netherlands, Belgium | **$20-25** | 6% |
| 5 | **Nordic** | Norway, Sweden, Denmark | **$18-25** | 6% |

**Excluded (Low CPM):** Korean ($10-15), Japanese ($15-20), Spanish ($8-12), Portuguese ($5-8), Indonesian ($2-5)

### TMDB Regional Trending Integration
**Strategy:** Use TMDB API to fetch trending movies/TV shows by region + language, then generate high-intent localized search terms.

**Example:**
- **Korea** → TMDB returns "흑백요리사" (Culinary Class Wars) → Search: `흑백요리사 무료 시청` → Found 5-20 high-intent users
- **France** → TMDB returns "Miraculous Ladybug" → Search: `Miraculous regarder gratuit` → Found 5-20 high-intent users

**Validation:** ✅ Tested and confirmed for France and Korea (Dec 31, 2025)

---

## 1. Tier 1 Optimized 24-Hour Rotation
*70% English (Highest CPM), 30% European Tier 1*

### The 24-Hour Cycle (Tier 1 Only)
| Slot | UTC | Region | Language | CPM | Prime Time |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 00:00-01:00 | **Los Angeles** | English | $30-40 | Evening |
| 2 | 01:00-02:00 | **Los Angeles** | English | $30-40 | Evening |
| 3 | 02:00-03:00 | **New York** | English | $30-40 | Night |
| 4 | 03:00-04:00 | **New York** | English | $30-40 | Night |
| 5 | 04:00-05:00 | **London** | English | $22-28 | Morning |
| 6 | 05:00-06:00 | **London** | English | $22-28 | Morning |
| 7 | 06:00-07:00 | **Sydney** | English | $25-30 | Evening |
| 8 | 07:00-08:00 | **Sydney** | English | $25-30 | Evening |
| 9 | 08:00-09:00 | **Paris** | French | $18-25 | Afternoon |
| 10 | 09:00-10:00 | **Berlin** | German | $20-26 | Afternoon |
| 11 | 10:00-11:00 | **Amsterdam** | Dutch | $20-25 | Afternoon |
| 12 | 11:00-12:00 | **Oslo** | Norwegian | $25-32 | Afternoon |
| 13 | 12:00-13:00 | **Stockholm** | Swedish | $18-24 | Afternoon |
| 14 | 13:00-14:00 | **Copenhagen** | Danish | $18-24 | Afternoon |
| 15 | 14:00-15:00 | **Berlin** | German | $20-26 | Evening |
| 16 | 15:00-16:00 | **Paris** | French | $18-25 | Evening |
| 17 | 16:00-17:00 | **London** | English | $22-28 | Evening |
| 18 | 17:00-18:00 | **London** | English | $22-28 | Evening |
| 19 | 18:00-19:00 | **New York** | English | $30-40 | Afternoon |
| 20 | 19:00-20:00 | **New York** | English | $30-40 | Evening |
| 21 | 20:00-21:00 | **Chicago** | English | $30-40 | Evening |
| 22 | 21:00-22:00 | **Toronto** | English | $24-28 | Evening |
| 23 | 22:00-23:00 | **Los Angeles** | English | $30-40 | Evening |
| 24 | 23:00-24:00 | **Los Angeles** | English | $30-40 | Evening |

**Distribution:** 17 slots English (70%), 7 slots European Tier 1 (30%)

---

## 2. Each Slot: The Complete Cycle

### What Happens in Every 1-Hour Slot:
```
SLOT START (e.g., 13:00 UTC = Paris):
1. SWITCH LOCATION:
   - Navigate: Settings > Explore > Location
   - Search: "Paris"
   - Select: Paris, France

2. HARVEST LOCAL TRENDS:
   - Navigate: /explore
   - Scrape: Top 5 trends for Paris
   - Cache: current_trends = ["#Cannes", "#Ligue1", "#CinémaFrançais"]

3. SEARCH WITH NATIVE KEYWORDS:
   - Query 1: "où regarder film gratuit"
   - Query 2: "site streaming gratuit"
   - Query 3: "netflix trop cher"
   (ALL in French)

4. FOR EACH CANDIDATE TWEET:
   - De-Dup Check (skip if already replied)
   - Intent Check (MOVIE/TV only)
   - Draft Reply in FRENCH
   - INJECT LOCAL TREND: "...streamixapp.pages.dev #Cannes"

5. EXECUTE:
   - Type reply (human speed)
   - Post
   - Log to DB

6. REPEAT until slot ends (3-6 replies per slot)
```

---

## 3. Tier 1 Region-Language-TMDB Binding

| Region | Language | TMDB Source | High-Intent Keywords | Trends Source |
| :--- | :--- | :--- | :--- | :--- |
| **USA/UK/AU/CA** | `en` | English trending | `watch free`, `streaming`, `where to watch` | Local trends |
| **Germany/Switzerland/Austria** | `de` | German trending | `kostenlos schauen`, `wo schauen`, `gratis streaming` | Local trends |
| **France/Belgium** | `fr` | French trending | `regarder gratuit`, `où regarder`, `streaming gratuit` | Local trends |
| **Netherlands** | `nl` | Dutch trending | `gratis kijken`, `waar kijken`, `gratis streaming` | Local trends |
| **Norway** | `no` | Norwegian trending | `se gratis`, `hvor se`, `gratis streaming` | Local trends |
| **Sweden** | `sv` | Swedish trending | `titta gratis`, `var titta`, `gratis streaming` | Local trends |
| **Denmark** | `da` | Danish trending | `se gratis`, `hvor se`, `gratis streaming` | Local trends |

### TMDB Integration Flow:
```
1. Get current region from schedule (e.g., Berlin at 10:00 UTC)
2. Fetch TMDB trending for German language:
   - /discover/movie?with_original_language=de&sort_by=popularity.desc
   - /discover/tv?with_original_language=de&sort_by=popularity.desc
3. Generate search terms:
   - "Dark kostenlos schauen"
   - "Babylon Berlin wo schauen"
   - "gratis streaming" (generic)
4. Search X.com with these localized terms
5. Reply in German with local trending hashtags
```

---

## 4. Keyword Sets (Tier 1 Only)

| Lang | High-Intent Examples | TMDB-Enhanced |
| :--- | :--- | :--- |
| `en` | `watch free`, `where to watch`, `streaming` | `[Movie Title] watch free` |
| `de` | `kostenlos schauen`, `wo schauen`, `gratis streaming` | `[Movie Title] kostenlos schauen` |
| `fr` | `regarder gratuit`, `où regarder`, `streaming gratuit` | `[Movie Title] regarder gratuit` |
| `nl` | `gratis kijken`, `waar kijken`, `gratis streaming` | `[Movie Title] gratis kijken` |
| `no` | `se gratis`, `hvor se`, `gratis streaming` | `[Movie Title] se gratis` |
| `sv` | `titta gratis`, `var titta`, `gratis streaming` | `[Movie Title] titta gratis` |
| `da` | `se gratis`, `hvor se`, `gratis streaming` | `[Movie Title] se gratis` |

---

## 5. Trend Injection Protocol (Top 10 Hashtags)
*Every reply includes a LOCAL TRENDING HASHTAG from the top 10.*

### Per Slot:
```
1. After switching location, HARVEST top 10 trends.
2. Store: current_trends = ["#Trend1", "#Trend2", ..., "#Trend10"]
3. When drafting reply:
   - Randomly select from top 10 trends
   - Inject into reply for maximum visibility
```

### Example:
*   **Slot 9 (Paris):** User asks for free movies.
*   **Top 10 Trends:** `["#Cannes", "#Netflix", "#Cinéma", "#Paris", ...]`
*   **Reply:** "J'utilise streamixapp.pages.dev - qualité 4K, zéro pub. #Cannes"

---

## 6. LLM Protocol
```text
CURRENT REGION: {region}
CURRENT LANGUAGE: {lang}
LOCAL TRENDS: {trends}

Reply in {lang} ONLY. Inject one trend hashtag from {trends}.
Sound like a native speaker.
```

---

## 7. Persistence & De-Duplication

### SQLite: `xbot_memory.db`
*   `replied_tweets`: Prevent duplicate replies.
*   `scanned_tweets`: Track seen tweets.
*   `trend_cache`: Store regional trends.
*   `session_log`: Resume on restart.

---

## 8. Operational Parameters

| Action | Value |
| :--- | :--- |
| Slot Duration | 1 Hour |
| Replies Per Slot | 3-6 (rate limited) |
| Reply Cooldown | 45-90s |
| Max Replies/Day | ~100-150 |
| Sentinel Check | Every 6 Hours |

---

## 9. Selectors

| Component | Selector |
| :--- | :--- |
| Search | `[data-testid="SearchBox_Search_Input"]` |
| Explore | `a[href="/explore"]` |
| Trend | `[data-testid="trend"]` |
| Settings | `a[aria-label="Settings"][href="/settings/explore"]` |
| Location Search | `input[placeholder="Search locations"]` |
| Location Result | `button[role="button"]` |
| Tweet | `article[data-testid="tweet"]` |
| Reply | `[data-testid="reply"]` |
| Post | `[data-testid="tweetButton"]` |
| Text Area | `[data-testid="tweetTextarea_0"]` |

---

## 10. Content Policy
*   **YES:** Movies, TV Shows, Anime, KDrama.
*   **NO:** Live Sports, Politics, Crypto, Adult.
