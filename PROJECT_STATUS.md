# XBot Project Status & Handover Documentation

**Date:** December 30, 2024
**Current Version:** v6.2 (Strict Location Filtering)
**Goal:** Autonomous X.com bot to drive traffic to `streamixapp.pages.dev` by engaging with users looking for movies/TV shows.

---

## 🏗️ Architecture

The system uses a **Hybrid Brain-Body Architecture**:

1.  **The Brain (Server)**:
    *   **Stack:** Python, FastAPI, Uvicorn, SQLite, Groq Cloud API (LLM).
    *   **File:** `server.py`
    *   **Role:** Handles logic, LLM processing, scheduling, database persistence, and smart decision making. Hosted locally at `http://localhost:8000`.

2.  **The Body (Client)**:
    *   **Stack:** JavaScript (Tampermonkey Userscript).
    *   **File:** `xbot_client.js`
    *   **Role:** Runs in the browser, interacts with the DOM (click, type, scroll), captures data, and executes Brain commands.

---

## ✅ Completed Features

### 1. Autonomous Loop
The bot runs a 24/7 continuous loop:
1.  **Location Switch**: Changes X.com location settings to target specific regions (based on a schedule).
2.  **Trend Harvest**: Scrapes the top 5 trends from the region's "Trending" tab.
3.  **Smart Search**: Searches for potential targets (currently using keywords, moving to TMDB).
4.  **Scan & Reply**: Analyzes tweets, filters garbage, and replies using LLM-generated text.

### 2. Robust Location Switching (Optimization Journey)
We faced significant challenges here and solved them:
*   **Challenge**: React inputs wouldn't update with simple `value = 'Dublin'`.
    *   **Fix**: Used `nativeInputValueSetter.call(input, value)` + `dispatchEvent` to trigger React state updates.
*   **Challenge**: Bot would get stuck in a loop trying to switch location.
    *   **Fix**: Implemented a strict State Machine (`NAVIGATE` -> `TYPE` -> `SELECT` -> `DONE`) with persistence.
*   **Challenge**: Selecting the wrong button (e.g., clicking "Back" instead of "Dublin").
    *   **Fix**: Implemented `findLocationResults()` with **Strict Filtering** (ignores buttons with @handles, numbers, "Follow", etc.).
*   **Challenge**: X.com auto-redirects to `/home` after selection, killing the script.
    *   **Fix**: The bot now marks the step as `SUCCESS` *before* the redirect happens and auto-resumes correctly after the reload.

### 3. Safety & Stealth
*   **Filters**: Ignored accounts (Netflix, Prime, verified brands), blocked keywords (India-specific context), and low-quality tweets.
*   **Rate Limits**:
    *   6 replies/hour
    *   100 replies/day
    *   Cooldowns between actions.
*   **Human-like Delays**: Random sleeps between typing and clicking.

---

## 🚧 Current State & Next Steps

**Current Status:**
*   The bot successfully switches locations (e.g., to Toronto).
*   It successfully navigates to the Trending tab.
*   It harvests trends (e.g., #Merino, #Iran).
*   It searches and finds candidates.

**Immediate Next Step: High-Intent Search (TMDB Integration)**
The current search keywords (e.g., `"where to watch" free`) are too vague. We are moving to a **TMDB-Powered** approach.

**The Plan (Ready to Execute):**
1.  Integrate **TMDB API** into `server.py`.
2.  Fetch trending movies/shows daily.
3.  Generate precise search queries: `"{Movie Name}" streaming`, `where to watch "{Movie Name}"`.
4.  Store these terms in SQLite to avoid duplication.
5.  Feed these high-intent terms to the bot.

See `implementation_plan.md` for the detailed technical spec.

---

## 🛠️ How to Run

1.  **Start the Brain:**
    ```bash
    cd c:\Users\VASU\Desktop\xbot\active
    py server.py
    ```
2.  **Start the Body:**
    *   Install `xbot_client.js` in Tampermonkey.
    *   Go to `https://x.com`.
    *   Click "Start Bot" on the UI overlay.

## 📂 Key Files
*   `active/server.py`: Main backend logic.
*   `active/xbot_client.js`: Browser automation script.
*   `active/xbot.db`: SQLite database (auto-created).
*   `.gemini/antigravity/.../implementation_plan.md`: The blueprint for the next phase.
