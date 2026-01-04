// ==UserScript==
// @name         XBot v8.0 (Million Visitor Engine)
// @namespace    http://tampermonkey.net/
// @version      8.0
// @description  X.com Bot - Advanced AI Orchestrator with Tier 1 High-CPM Targeting
// @author       XBot
// @match        https://x.com/*
// @match        https://twitter.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_notification
// @grant        GM_setClipboard
// @grant        GM_setValue
// @grant        GM_getValue
// @connect      localhost
// @run-at       document-idle
// ==/UserScript==

(function () {
    'use strict';

    // ========================================================================
    // CONFIG
    // ========================================================================

    const CONFIG = {
        BRAIN_URL: 'http://localhost:8000',
        MAIN_LOOP_INTERVAL: 15000,      // 15s between scans
        REPLY_COOLDOWN: 3000,           // 3 seconds between replies
        EMPTY_SCANS_BEFORE_ROTATE: 3,   // Rotate after 3 empty scans (exhausted)
        TREND_HARVEST_INTERVAL: 1800000,
        LOCATION_SWITCH_COOLDOWN: 3600000,
        MAX_REPLIES_PER_HOUR: 60,       // Aggressive
        MAX_REPLIES_PER_SCAN: 100,      // Process ALL candidates
        MAX_REPLIES_PER_DAY: 500,       // High daily limit
        DRY_RUN: true,
        DEBUG: true
    };

    // ========================================================================
    // BLOCKED CONTENT
    // ========================================================================

    const BLOCKED_ACCOUNTS = new Set([
        'netflix', 'netflixindia', 'primevideo', 'disneyplus', 'hulu',
        'hbomax', 'peacock', 'paramountplus', 'appletv', 'amazonprime',
        'spotify', 'youtube', 'twitter', 'x', 'google', 'microsoft'
    ]);

    const INDIA_KEYWORDS = [
        'india', 'indian', 'bollywood', 'hindi', 'desi', 'bharat',
        'mumbai', 'delhi', 'bangalore', 'hyderabad', 'chennai', 'kolkata',
        'ipl', 'cricket', 'bigg boss', 'salman khan', 'shah rukh'
    ];

    // ========================================================================
    // PHASES & STEPS
    // ========================================================================

    const FALLBACK_KEYWORDS = [
        '"where to watch" free',
        '"best free streaming" site',
        '"streaming site" no ads'
    ];

    const PHASES = {
        IDLE: 'IDLE',
        SWITCHING_LOCATION: 'SWITCHING',
        HARVESTING_TRENDS: 'HARVESTING',
        SEARCHING: 'SEARCHING',
        SCANNING: 'SCANNING',
        REPLYING: 'REPLYING'
    };

    const LOCATION_STEPS = {
        NAVIGATE: 'NAVIGATE',
        TYPE: 'TYPE',
        SELECT: 'SELECT',
        RELOAD: 'RELOAD',
        DONE: 'DONE'
    };

    // ========================================================================
    // STATE
    // ========================================================================

    let STATE = {
        isRunning: false,
        phase: PHASES.IDLE,
        currentRegion: null,
        currentLocation: null,
        currentLang: null,
        currentKeywords: [],
        currentTrends: [],
        currentKeywordIndex: 0,
        lastLocationSwitchTime: 0,
        lastLocationSwitchRegion: null,
        lastKeywordRotation: 0,
        lastTrendHarvest: 0,
        repliesThisHour: 0,
        repliesToday: 0,
        lastReplyTime: 0,
        hourStartTime: Date.now(),
        processedTweets: new Set(),
        consecutiveErrors: 0,
        locationSwitchStep: LOCATION_STEPS.NAVIGATE,
        // Smart Search State v8.0
        currentSearchTerm: '',
        currentMovieTitle: null,
        currentTMDBId: null,
        currentSearchLang: 'en',
        currentSearchCategory: null, // frustration, intent, recommendation, trending
        // Exhaustion-based rotation
        shouldRotateKeyword: false,
        consecutiveEmptyScans: 0,
        // Analytics v8.0
        estimatedReach: 0,
        sentimentStats: { frustrated: 0, excited: 0, seeking: 0, neutral: 0 },
    };

    // ========================================================================
    // UTILITIES
    // ========================================================================

    function log(...args) {
        if (CONFIG.DEBUG) {
            console.log('[XBot]', new Date().toISOString(), `[${STATE.phase}]`, ...args);
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function randomBetween(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    async function waitForSelector(selector, timeout = 10000) {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const el = document.querySelector(selector);
            if (el) return el;
            await sleep(500);
        }
        return null;
    }

    function setReactInputValue(input, value) {
        // Get the native value setter
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(input, value);

        // Trigger React's onChange
        const inputEvent = new Event('input', { bubbles: true });
        const changeEvent = new Event('change', { bubbles: true });
        input.dispatchEvent(inputEvent);
        input.dispatchEvent(changeEvent);
    }

    // ========================================================================
    // PERSISTENCE
    // ========================================================================

    function saveState() {
        const data = {
            isRunning: STATE.isRunning,
            phase: STATE.phase,
            currentRegion: STATE.currentRegion,
            currentLocation: STATE.currentLocation,
            currentLang: STATE.currentLang,
            currentTrends: STATE.currentTrends,
            currentKeywordIndex: STATE.currentKeywordIndex,
            lastLocationSwitchTime: STATE.lastLocationSwitchTime,
            lastLocationSwitchRegion: STATE.lastLocationSwitchRegion,
            lastKeywordRotation: STATE.lastKeywordRotation,
            lastTrendHarvest: STATE.lastTrendHarvest,
            repliesThisHour: STATE.repliesThisHour,
            repliesToday: STATE.repliesToday,
            lastReplyTime: STATE.lastReplyTime,
            hourStartTime: STATE.hourStartTime,

            // Smart Search Persistence
            currentSearchTerm: STATE.currentSearchTerm,
            currentMovieTitle: STATE.currentMovieTitle,
            currentTMDBId: STATE.currentTMDBId,

            processedTweets: Array.from(STATE.processedTweets).slice(-200),
            locationSwitchStep: STATE.locationSwitchStep,
            timestamp: Date.now()
        };
        GM_setValue('xbot_state_v80', JSON.stringify(data));
    }

    function loadState() {
        try {
            const saved = GM_getValue('xbot_state_v80', null);
            if (!saved) return false;

            const data = JSON.parse(saved);
            if (Date.now() - data.timestamp > 300000) return false;

            STATE.isRunning = data.isRunning;
            STATE.phase = data.phase || PHASES.IDLE;
            STATE.currentRegion = data.currentRegion;
            STATE.currentLocation = data.currentLocation;
            STATE.currentLang = data.currentLang;
            STATE.currentTrends = data.currentTrends || [];
            STATE.currentKeywordIndex = data.currentKeywordIndex || 0;
            STATE.lastLocationSwitchTime = data.lastLocationSwitchTime || 0;
            STATE.lastLocationSwitchRegion = data.lastLocationSwitchRegion;
            STATE.lastKeywordRotation = data.lastKeywordRotation || Date.now();
            STATE.lastTrendHarvest = data.lastTrendHarvest || 0;

            // Load Smart Search Data
            if (data.currentSearchTerm) STATE.currentSearchTerm = data.currentSearchTerm;
            if (data.currentMovieTitle) STATE.currentMovieTitle = data.currentMovieTitle;
            if (data.currentTMDBId) STATE.currentTMDBId = data.currentTMDBId;

            STATE.processedTweets = new Set(data.processedTweets || []);
            STATE.locationSwitchStep = data.locationSwitchStep || LOCATION_STEPS.NAVIGATE;

            if (Date.now() - data.hourStartTime < 3600000) {
                STATE.repliesThisHour = data.repliesThisHour || 0;
                STATE.hourStartTime = data.hourStartTime;
            }

            log('State loaded, isRunning:', STATE.isRunning, 'locationStep:', STATE.locationSwitchStep);
            return true;
        } catch (e) {
            return false;
        }
    }

    // ========================================================================
    // SAFETY CHECKS
    // ========================================================================

    function isBlockedAccount(handle) {
        const lower = handle.toLowerCase();
        for (const b of BLOCKED_ACCOUNTS) if (lower.includes(b)) return true;
        return false;
    }

    function containsIndiaContent(text) {
        const lower = text.toLowerCase();
        return INDIA_KEYWORDS.some(kw => lower.includes(kw));
    }

    function isVerifiedAccount(el) {
        return el.querySelector('svg[aria-label*="Verified"]') !== null;
    }

    function isPromotedTweet(el) {
        const t = el.innerText.toLowerCase();
        return t.includes('promoted') || t.includes('ad ·');
    }

    // Pre-filter: Check if tweet is likely streaming-related
    // GOAL: Be INCLUSIVE - let LLM make the final decision. Only skip OBVIOUS non-streaming content.
    function isLikelyStreamingRelated(text) {
        const lower = text.toLowerCase();

        // HARD SKIP: Topics that are NEVER relevant (sports, politics, etc.)
        const hardSkipKeywords = [
            // Sports (specific terms only)
            'goal', 'touchdown', 'halftime', 'premier league', 'champions league',
            'nba', 'nfl', 'fifa', 'world cup', 'playoff', 'semifinals',
            // Politics
            'trump', 'biden', 'election', 'vote', 'congress', 'senate',
            // Package delivery (not Prime Video)
            'package delivered', 'shipping', 'tracking number', 'warehouse',
            // Music-only content
            'spotify', 'playlist', 'concert tickets', 'tour dates',
        ];

        if (hardSkipKeywords.some(kw => lower.includes(kw))) {
            return false;
        }

        // PASS: Any of these keywords = send to LLM for analysis
        const streamingKeywords = [
            // Core streaming words
            'streaming', 'stream', 'watch', 'movie', 'film', 'show', 'series',
            'netflix', 'hulu', 'disney', 'hbo', 'prime video', 'amazon prime',
            // Intent signals
            'where to', 'how to', 'want to watch', 'looking for',
            'recommend', 'suggestion', 'what should i',
            // Frustration signals
            'expensive', 'cancel', 'subscription', 'paying for', 'cost',
            'too many', 'sick of', 'tired of', 'hate paying',
            // Quality signals
            'hd', '4k', 'quality', 'buffering', 'ads', 'no ads', 'free',
            // Piracy signals
            'illegal', 'pirate', 'torrent', 'free site',
            // Movie-specific
            'cinema', 'theater', 'box office', 'sequel', 'episode', 'season',
        ];

        if (streamingKeywords.some(kw => lower.includes(kw))) {
            return true;
        }

        // Ambiguous - skip (let next loop find better candidates)
        return false;
    }

    // ========================================================================
    // API
    // ========================================================================

    async function callBrain(endpoint, method = 'GET', data = null) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method,
                url: `${CONFIG.BRAIN_URL}${endpoint}`,
                headers: { 'Content-Type': 'application/json' },
                data: data ? JSON.stringify(data) : null,
                timeout: 30000,
                onload: (r) => {
                    try { resolve(JSON.parse(r.responseText)); }
                    catch (e) { reject(e); }
                },
                onerror: reject,
                ontimeout: () => reject(new Error('Timeout'))
            });
        });
    }

    async function getSchedule() {
        const s = await callBrain('/schedule');
        STATE.currentRegion = s.region;
        STATE.currentLocation = s.location;
        STATE.currentLang = s.lang_code;
        if (s.current_trends?.length > 0) STATE.currentTrends = s.current_trends;
        return s;
    }

    async function sendTrendsToBrain(region, trends) {
        return callBrain('/update-trends', 'POST', { region, trends });
    }

    async function analyzeTweet(data) {
        return callBrain('/analyze', 'POST', data);
    }

    async function selectLocationFromBrain(targetLocation, options) {
        return callBrain('/select-location', 'POST', {
            target_location: targetLocation,
            options: options
        });
    }

    // ========================================================================
    // PAGE DETECTION
    // ========================================================================

    function getCurrentPage() {
        const p = window.location.pathname;
        if (p.includes('/settings/explore/location')) return 'LOCATION';
        if (p.includes('/explore/tabs/trending')) return 'TRENDING';
        if (p === '/explore') return 'EXPLORE';
        if (p.includes('/search')) return 'SEARCH';
        return 'OTHER';
    }

    // ========================================================================
    // LOCATION SWITCHING (FIXED - Better Result Selector)
    // ========================================================================

    function needsLocationSwitch() {
        if (STATE.lastLocationSwitchRegion === STATE.currentRegion) {
            const elapsed = Date.now() - STATE.lastLocationSwitchTime;
            if (elapsed < CONFIG.LOCATION_SWITCH_COOLDOWN) {
                log('Location already set to', STATE.currentRegion, '- skip');
                return false;
            }
        }
        return true;
    }

    function findLocationResults() {
        // Get all buttons with role="button"
        const allButtons = document.querySelectorAll('button[role="button"]');
        const results = [];

        log('[findLocationResults] Found', allButtons.length, 'total buttons');

        for (const btn of allButtons) {
            const text = btn.textContent.trim();

            // Skip empty or very short text
            if (!text || text.length < 3) continue;

            // Skip if too long (locations are short)
            if (text.length > 50) continue;

            // Skip buttons with @ (user handles)
            if (text.includes('@')) continue;

            // Skip "Follow" buttons
            if (text.toLowerCase() === 'follow') continue;

            // Skip numbers only (like 4.1K, 655, etc.)
            if (/^[\d.,KMk]+$/.test(text)) continue;

            // Skip if contains newlines (complex buttons)
            if (text.includes('\n')) continue;

            // Skip common non-location words
            const skipWords = ['follow', 'post', 'premium', 'home', 'explore', 'notifications',
                'messages', 'grok', 'communities', 'profile', 'search', 'more',
                'apple', 'show', 'subscribe', 'trending', 'news', 'sports', 'entertainment',
                'see new posts', 'show more', 'see more'];
            if (skipWords.some(w => text.toLowerCase() === w || text.toLowerCase().includes(w))) continue;

            // Location names typically: Start with capital, might have comma (City, Country)
            // Must match pattern: "Word" or "Word, Word" or "Word Word"
            if (!/^[A-Z][a-zA-Z\s,'-]+$/.test(text)) continue;

            // This looks like a location result!
            results.push(btn);
        }

        log('[findLocationResults] Filtered to', results.length, 'location buttons');
        if (results.length > 0) {
            const samples = results.slice(0, 5).map(el => el.textContent.trim());
            log('[findLocationResults] Results:', samples);
        }

        return results;
    }

    async function handleLocationSwitch() {
        log('=== LOCATION SWITCH ===');
        STATE.phase = PHASES.SWITCHING_LOCATION;

        // STEP 1: Navigate to location settings
        if (getCurrentPage() !== 'LOCATION' && STATE.locationSwitchStep !== LOCATION_STEPS.DONE) {
            log('Step 1: Navigating to location settings...');
            STATE.locationSwitchStep = LOCATION_STEPS.TYPE;
            saveState();
            window.location.href = 'https://x.com/settings/explore/location';
            return 'NAVIGATING';
        }

        // STEP 2: Type the location with React-compatible events
        if (STATE.locationSwitchStep === LOCATION_STEPS.TYPE) {
            log('Step 2: Waiting for search input...');
            const searchInput = await waitForSelector('input[placeholder="Search locations"]');
            if (!searchInput) {
                log('Search input not found after timeout!');
                return 'RETRY';
            }

            log('Typing location (React-compatible):', STATE.currentLocation);
            searchInput.focus();
            await sleep(500);

            // Clear first with React events
            setReactInputValue(searchInput, '');
            await sleep(300);

            // Type character by character to trigger search
            for (let i = 0; i < STATE.currentLocation.length; i++) {
                const partial = STATE.currentLocation.substring(0, i + 1);
                setReactInputValue(searchInput, partial);
                await sleep(randomBetween(100, 200));
            }

            log('Waiting for results to populate...');
            await sleep(4000);

            STATE.locationSwitchStep = LOCATION_STEPS.SELECT;
            saveState();
        }

        // STEP 3: Select and Click Result
        if (STATE.locationSwitchStep === LOCATION_STEPS.SELECT) {
            log('Step 3: Finding location results...');

            const resultElements = findLocationResults();

            if (resultElements.length === 0) {
                log('No location results found! Waiting more...');
                await sleep(2000);
                return 'RETRY';
            }

            const options = resultElements
                .map(el => el.textContent.trim())
                .filter(text => text.length > 0 && text.length < 100);

            log('Found options:', options);

            const selection = await selectLocationFromBrain(STATE.currentLocation, options);
            log('Brain selection:', selection);

            if (selection.index >= 0 && selection.index < resultElements.length) {
                const targetElement = resultElements[selection.index];
                log('Clicking:', targetElement.textContent.trim());

                // Click the location result
                // NOTE: X.com automatically redirects to /home after clicking
                targetElement.click();

                // Mark as successful BEFORE the redirect happens
                STATE.lastLocationSwitchTime = Date.now();
                STATE.lastLocationSwitchRegion = STATE.currentRegion;
                STATE.locationSwitchStep = LOCATION_STEPS.DONE;
                saveState();

                log('Location clicked! X.com will redirect to /home...');
                // Don't manually reload - X does it automatically
                return 'SUCCESS';
            } else {
                log('Brain could not find a suitable match.');
                return 'NO_MATCH';
            }
        }

        // STEP 4: Already handled in STEP 3 (no reload needed)
        if (STATE.locationSwitchStep === LOCATION_STEPS.RELOAD) {
            log('Step 4: Location switch already complete (redirect happened)');
            STATE.lastLocationSwitchTime = Date.now();
            STATE.lastLocationSwitchRegion = STATE.currentRegion;
            STATE.locationSwitchStep = LOCATION_STEPS.DONE;
            saveState();
            return 'SUCCESS';
        }

        return 'UNKNOWN';
    }

    // ========================================================================
    // TREND HARVESTING
    // ========================================================================

    function needsTrendHarvest() {
        if (STATE.currentTrends.length === 0) return true;
        if (Date.now() - STATE.lastTrendHarvest > CONFIG.TREND_HARVEST_INTERVAL) return true;
        return false;
    }

    async function handleTrendHarvest() {
        log('=== TREND HARVEST ===');
        STATE.phase = PHASES.HARVESTING_TRENDS;

        if (getCurrentPage() !== 'TRENDING') {
            log('Navigating to trending tab...');
            saveState();
            window.location.href = 'https://x.com/explore/tabs/trending';
            return 'NAVIGATING';
        }

        await sleep(3000);

        // Enhanced trend extraction - multiple selectors for robustness
        const trends = [];

        // Method 1: Try [data-testid="trend"]
        const trendElements = document.querySelectorAll('[data-testid="trend"]');
        trendElements.forEach(el => {
            const lines = el.innerText.split('\n');
            for (const line of lines) {
                const t = line.trim();
                // Skip metadata lines
                if (/^\d/.test(t) || t.includes('·') || t.toLowerCase().includes('trending')) continue;
                if (t.length < 2 || t.length > 50) continue;
                if (t.toLowerCase().includes('post') || t.toLowerCase().includes('show more')) continue;

                // Add hashtags directly
                if (t.startsWith('#')) {
                    trends.push(t);
                }
                // Convert trending topics to hashtags (no spaces = topic name)
                else if (t.length > 2 && !t.includes(' ') && /^[A-Za-z]/.test(t)) {
                    trends.push('#' + t);
                }
                // Multi-word trends - convert to camelCase hashtag
                else if (t.length > 3 && t.includes(' ') && t.split(' ').length <= 3) {
                    const words = t.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase());
                    trends.push('#' + words.join(''));
                }
            }
        });

        // Method 2: Try trending topic spans directly
        const topicSpans = document.querySelectorAll('[dir="ltr"] > span');
        topicSpans.forEach(span => {
            const t = span.textContent.trim();
            if (t.startsWith('#') && t.length > 2 && t.length < 50) {
                trends.push(t);
            }
        });

        // Method 3: Try to find any hashtag-like text on the page
        const allText = document.body.innerText;
        const hashtagMatches = allText.match(/#[A-Za-z][A-Za-z0-9_]{1,29}/g) || [];
        hashtagMatches.forEach(tag => {
            if (tag.length > 2 && !tag.toLowerCase().includes('xbot')) {
                trends.push(tag);
            }
        });

        // Deduplicate and filter
        const unique = [...new Set(trends)]
            .filter(t => !INDIA_KEYWORDS.some(kw => t.toLowerCase().includes(kw)))
            .slice(0, 10);

        if (unique.length > 0) {
            STATE.currentTrends = unique;
            STATE.lastTrendHarvest = Date.now();

            // Send to Brain
            try {
                await sendTrendsToBrain(STATE.currentRegion, unique);
                log('✅ Harvested & Sent to Brain:', unique);
            } catch (e) {
                log('Failed to send trends to brain:', e);
            }

            saveState();
            return 'SUCCESS';
        }

        // Fallback if no trends found
        log('⚠️ No trends found, using fallbacks');
        STATE.currentTrends = ['#Movies', '#Streaming', '#WatchOnline', '#Cinema', '#Film'];
        STATE.lastTrendHarvest = Date.now();
        saveState();
        return 'FALLBACK';
    }

    // ========================================================================
    // SEARCH & SCAN
    // ========================================================================

    async function handleSearch() {
        if (getCurrentPage() !== 'SEARCH') {
            // New: Fetch Smart Search Term from Brain
            log('Fetching Smart Search Term...');
            try {
                const searchData = await callBrain('/smart-search');
                if (searchData && searchData.search_term) {
                    STATE.currentSearchTerm = searchData.search_term;
                    STATE.currentMovieTitle = searchData.title;
                    STATE.currentTMDBId = searchData.tmdb_id;
                    STATE.currentSearchLang = searchData.lang_code || 'en';
                    STATE.currentSearchCategory = searchData.category || 'trending';

                    log(`Smart Search: "${searchData.search_term}" (Title: ${searchData.title}, Lang: ${searchData.lang_code}, Category: ${searchData.category})`);
                    saveState();

                    window.location.href = `https://x.com/search?q=${encodeURIComponent(searchData.search_term)}&src=typed_query&f=live`;
                    return 'NAVIGATING';
                }
            } catch (e) {
                log('Error fetching smart search term:', e);
            }

            // Fallback to old rotation if smart search fails
            let keywordList = STATE.currentKeywords;
            if (!keywordList || keywordList.length === 0) {
                log('Warning: No keywords in state, using hardcoded fallback.');
                keywordList = FALLBACK_KEYWORDS;
            }

            const keyword = keywordList[STATE.currentKeywordIndex % keywordList.length];
            log('Fallback: Navigating to search for:', keyword);
            saveState();
            window.location.href = `https://x.com/search?q=${encodeURIComponent(keyword)}&src=typed_query&f=live`;
            return 'NAVIGATING';
        }

        // EXHAUSTION-BASED ROTATION: Only rotate when no candidates found after multiple scans
        // This is set by scanAndReply when it finds nothing new
        if (STATE.shouldRotateKeyword) {
            log('🔄 Search exhausted! Rotating to new search term...');
            STATE.shouldRotateKeyword = false;
            STATE.consecutiveEmptyScans = 0;

            try {
                const searchData = await callBrain('/smart-search');
                if (searchData && searchData.search_term) {
                    STATE.currentSearchTerm = searchData.search_term;
                    STATE.currentMovieTitle = searchData.title;
                    STATE.currentTMDBId = searchData.tmdb_id;
                    STATE.currentSearchLang = searchData.lang_code || 'en';
                    STATE.currentSearchCategory = searchData.category || 'trending';
                    STATE.lastKeywordRotation = Date.now();
                    STATE.processedTweets.clear(); // Clear for new search

                    log(`📍 New Search: "${searchData.search_term}" (${searchData.category})`);
                    saveState();

                    window.location.href = `https://x.com/search?q=${encodeURIComponent(searchData.search_term)}&src=typed_query&f=live`;
                    return 'NAVIGATING';
                }
            } catch (e) {
                log('Error rotating search term:', e);
            }
        }

        return 'READY';
    }

    async function scanAndReply() {
        log('=== SCANNING ===');
        STATE.phase = PHASES.SCANNING;

        // AGGRESSIVE SCROLLING - 10 passes to load ALL tweets
        const scrollPasses = 10;
        for (let scrollPass = 0; scrollPass < scrollPasses; scrollPass++) {
            log(`Scroll ${scrollPass + 1}/${scrollPasses}...`);
            window.scrollBy({ top: randomBetween(1000, 1500), behavior: 'smooth' });
            await sleep(800); // Fast scrolling
        }
        await sleep(1000);

        const tweets = document.querySelectorAll('article[data-testid="tweet"]');
        const candidates = [];

        for (const tw of tweets) {
            const data = extractTweetData(tw);
            if (!data || STATE.processedTweets.has(data.tweet_id)) continue;

            STATE.processedTweets.add(data.tweet_id);
            if (isPromotedTweet(tw) || isVerifiedAccount(tw) || isBlockedAccount(data.user_handle) || containsIndiaContent(data.tweet_text)) continue;

            // v8.1: Pre-filter for streaming relevance (saves API calls)
            if (!isLikelyStreamingRelated(data.tweet_text)) {
                log(`⏭️ Pre-filtered (not streaming): @${data.user_handle}`);
                continue;
            }

            // v8.0: Extract thread replies for context
            data.thread_replies = extractThreadReplies(tw);

            candidates.push(data);
        }

        log('Total candidates found:', candidates.length);

        // EXHAUSTION DETECTION: Track empty scans to know when to rotate
        if (candidates.length === 0) {
            STATE.consecutiveEmptyScans++;
            log(`No new candidates (${STATE.consecutiveEmptyScans} consecutive empty scans)`);

            // After N consecutive empty scans, mark for rotation
            if (STATE.consecutiveEmptyScans >= CONFIG.EMPTY_SCANS_BEFORE_ROTATE) {
                log('🔄 Search term exhausted! Flagging for rotation...');
                STATE.shouldRotateKeyword = true;
                saveState();
            }
            return 'NO_CANDIDATES';
        }

        // Reset counter when we find candidates
        STATE.consecutiveEmptyScans = 0;

        // PROCESS MULTIPLE CANDIDATES (up to MAX_REPLIES_PER_SCAN per cycle)
        let repliesThisScan = 0;

        for (const target of candidates) {
            // Check limits
            if (repliesThisScan >= CONFIG.MAX_REPLIES_PER_SCAN) {
                log(`Reached MAX_REPLIES_PER_SCAN (${CONFIG.MAX_REPLIES_PER_SCAN}), stopping this scan`);
                break;
            }
            if (STATE.repliesThisHour >= CONFIG.MAX_REPLIES_PER_HOUR) {
                log(`Reached MAX_REPLIES_PER_HOUR (${CONFIG.MAX_REPLIES_PER_HOUR}), stopping`);
                break;
            }

            // Wait for cooldown if needed (skip in DRY_RUN for fast testing)
            if (!CONFIG.DRY_RUN) {
                const timeSinceLastReply = Date.now() - STATE.lastReplyTime;
                if (timeSinceLastReply < CONFIG.REPLY_COOLDOWN) {
                    const waitTime = CONFIG.REPLY_COOLDOWN - timeSinceLastReply + 1000;
                    log(`Cooldown: waiting ${Math.round(waitTime / 1000)}s before next reply...`);
                    await sleep(waitTime);
                }
            }

            // Analyze this tweet
            log(`Analyzing candidate ${repliesThisScan + 1}: @${target.user_handle}`);
            const analysis = await analyzeTweet({
                tweet_id: target.tweet_id,
                tweet_text: target.tweet_text,
                user_handle: target.user_handle,
                movie_title: STATE.currentMovieTitle,
                search_category: STATE.currentSearchCategory,
                search_lang: STATE.currentSearchLang,
                thread_replies: target.thread_replies
            });

            if (analysis.action !== 'REPLY' || !analysis.draft) {
                log(`⏭️ Skipped: ${target.tweet_id} - ${analysis.reason}`);
                continue;
            }

            // Track sentiment
            if (analysis.sentiment && STATE.sentimentStats[analysis.sentiment] !== undefined) {
                STATE.sentimentStats[analysis.sentiment]++;
            }

            STATE.phase = PHASES.REPLYING;

            // VALIDATION: Check for hashtags and features
            const hasHashtag = analysis.draft.includes('#');
            const hasFeatures = /no ads?|free|4k|hd|dolby|no popup|no signup/i.test(analysis.draft);
            const hasSite = analysis.draft.includes('streamixapp.pages.dev');

            if (CONFIG.DRY_RUN) {
                log('━━━━━━━━━━━━━━━━━━━━━━━━━━━');
                log('[DRY RUN] ✉️ Reply:', analysis.draft);
                log('[DRY RUN] 📊 Checks:',
                    hasSite ? '✅ Site' : '❌ Site',
                    hasHashtag ? '✅ Hashtag' : '❌ Hashtag',
                    hasFeatures ? '✅ Features' : '❌ Features'
                );
                log('[DRY RUN] 💭 Tweet:', target.tweet_text.substring(0, 80) + '...');
                log('━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            }

            STATE.lastReplyTime = Date.now();
            STATE.repliesThisHour++;
            STATE.repliesToday++;
            STATE.estimatedReach += 150;
            repliesThisScan++;

            // Short delay between replies (even in dry run to simulate real behavior)
            if (repliesThisScan < candidates.length) {
                await sleep(randomBetween(2000, 4000));
            }
        }

        saveState();
        log(`🏁 Scan complete: ${repliesThisScan} replies this scan, ${STATE.repliesThisHour} this hour`);
        return repliesThisScan > 0 ? 'SUCCESS' : 'NO_MATCHES';
    }

    // v8.0: Extract existing thread replies for context-aware responses
    function extractThreadReplies(tweetEl) {
        const replies = [];
        try {
            // Look for reply thread context (parent tweet or sibling replies)
            const container = tweetEl.closest('[data-testid="cellInnerDiv"]');
            if (!container) return replies;

            // Get sibling tweets (other replies in thread)
            const siblings = container.parentElement?.querySelectorAll('[data-testid="tweetText"]') || [];
            siblings.forEach((el, index) => {
                if (index > 0 && index <= 3) { // Get up to 3 existing replies
                    const text = el.innerText?.trim();
                    if (text && text.length < 280) {
                        replies.push(text);
                    }
                }
            });
        } catch (e) {
            log('Error extracting thread replies:', e);
        }
        return replies.slice(0, 3);
    }

    function extractTweetData(el) {
        try {
            const link = el.querySelector('a[href*="/status/"]');
            const id = link?.href.match(/status\/(\d+)/)?.[1];
            if (!id) return null;
            const textEl = el.querySelector('[data-testid="tweetText"]');
            const userEl = el.querySelector('[data-testid="User-Name"]');
            const handle = userEl?.innerText.match(/@(\w+)/)?.[1] || '';
            return { tweet_id: id, tweet_text: textEl?.innerText || '', user_handle: handle };
        } catch (e) { return null; }
    }

    // ========================================================================
    // MAIN LOOP
    // ========================================================================

    async function mainLoop() {
        if (!STATE.isRunning) return;

        log('====== LOOP START ======');
        try {
            await getSchedule();

            // CRITICAL: Don't proceed to trends/search until location is set
            if (needsLocationSwitch() || STATE.locationSwitchStep !== LOCATION_STEPS.DONE) {
                const r = await handleLocationSwitch();
                log('Location switch returned:', r);
                if (r === 'NAVIGATING') {
                    // Page is navigating to location settings
                    return; // Wait for navigation to complete
                }
                if (r === 'RETRY' || r === 'NO_RESULTS' || r === 'NO_MATCH') {
                    // Location switch incomplete - retry in next loop
                    log('Location switch incomplete, will retry in next loop');
                    saveState();
                    setTimeout(mainLoop, 5000);
                    return;
                }
                if (r === 'SUCCESS') {
                    // Location clicked! Now navigate to trending page
                    log('Location switch successful! Clearing old trends and navigating to trending page...');

                    // CRITICAL: Clear old trends to force fresh harvest for new region
                    STATE.currentTrends = [];
                    STATE.lastTrendHarvest = 0; // Force immediate harvest

                    saveState();
                    // Wait a moment for X.com to process the location change
                    await sleep(2000);
                    window.location.href = 'https://x.com/explore/tabs/trending';
                    return;
                }
            }

            if (needsTrendHarvest()) {
                const r = await handleTrendHarvest();
                if (r === 'NAVIGATING') return;
            }

            const searchResult = await handleSearch();
            if (searchResult === 'NAVIGATING' || searchResult === 'RELOADING') return;

            await scanAndReply();

        } catch (e) {
            log('ERROR:', e);
        }

        log('====== LOOP END ======');
        saveState();
        if (STATE.isRunning) {
            setTimeout(mainLoop, CONFIG.MAIN_LOOP_INTERVAL);
        }
    }

    // ========================================================================
    // UI & INIT
    // ========================================================================

    function createUI() {
        const p = document.createElement('div');
        p.id = 'xbot-v80';
        p.innerHTML = `
            <style>
                #xbot-v80 {
                    position: fixed; bottom: 20px; right: 20px;
                    background: linear-gradient(135deg, #15202b 0%, #1c2938 100%);
                    border: 1px solid #38444d; border-radius: 16px;
                    padding: 16px; z-index: 9999; color: white; 
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    min-width: 240px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                }
                #xbot-v80 h4 { margin: 0 0 12px 0; color: #1da1f2; font-size: 14px; }
                #xbot-v80 .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 10px 0; }
                #xbot-v80 .stat { background: rgba(29,161,242,0.1); padding: 8px; border-radius: 8px; text-align: center; }
                #xbot-v80 .stat-value { font-size: 18px; font-weight: bold; color: #1da1f2; }
                #xbot-v80 .stat-label { font-size: 9px; color: #8899a6; text-transform: uppercase; }
                #xbot-v80 .info { font-size: 11px; margin: 4px 0; color: #8899a6; }
                #xbot-v80 .info span { color: white; }
                #xbot-v80 button { width: 100%; border: none; padding: 10px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 10px; transition: all 0.2s; }
                #xbot-v80 .start { background: linear-gradient(135deg, #1da1f2 0%, #0d8bd9 100%); color: white; }
                #xbot-v80 .stop { background: linear-gradient(135deg, #e0245e 0%, #c01e50 100%); color: white; }
                #xbot-v80 button:hover { transform: scale(1.02); }
            </style>
            <h4>🚀 XBot v8.0 | Million Engine</h4>
            <div class="stats">
                <div class="stat"><div class="stat-value" id="ui-replies">0</div><div class="stat-label">Replies Today</div></div>
                <div class="stat"><div class="stat-value" id="ui-reach">0</div><div class="stat-label">Est. Reach</div></div>
            </div>
            <div class="info">Status: <span id="ui-status">Stopped</span></div>
            <div class="info">Region: <span id="ui-region">--</span> (<span id="ui-lang">--</span>)</div>
            <div class="info">Phase: <span id="ui-phase">--</span></div>
            <div class="info">Category: <span id="ui-category">--</span></div>
            <button id="ui-toggle" class="start">▶ Start Engine</button>
        `;
        document.body.appendChild(p);
        document.getElementById('ui-toggle').onclick = toggleBot;
        setInterval(updateUI, 1000);
    }

    function updateUI() {
        document.getElementById('ui-status').innerText = STATE.isRunning ? '🟢 Running' : '🔴 Stopped';
        document.getElementById('ui-region').innerText = STATE.currentRegion || '--';
        document.getElementById('ui-lang').innerText = (STATE.currentLang || '--').toUpperCase();
        document.getElementById('ui-phase').innerText = STATE.phase;
        document.getElementById('ui-category').innerText = STATE.currentSearchCategory || '--';
        document.getElementById('ui-replies').innerText = STATE.repliesToday || 0;
        document.getElementById('ui-reach').innerText = formatNumber(STATE.estimatedReach || 0);
        const btn = document.getElementById('ui-toggle');
        btn.innerText = STATE.isRunning ? '⏹ Stop Engine' : '▶ Start Engine';
        btn.className = STATE.isRunning ? 'stop' : 'start';
    }

    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    function toggleBot() {
        STATE.isRunning = !STATE.isRunning;
        if (STATE.isRunning) {
            STATE.locationSwitchStep = LOCATION_STEPS.NAVIGATE;
            mainLoop();
        }
        saveState();
    }

    function init() {
        loadState();
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', createUI);
        } else {
            createUI();
        }
        if (STATE.isRunning) setTimeout(mainLoop, 3000);
    }

    init();

})();
