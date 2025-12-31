// ==UserScript==
// @name         XBot v6.3 (Complete Autonomous 24/7)
// @namespace    http://tampermonkey.net/
// @version      6.3
// @description  X.com Bot - TMDB Smart Search
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
        MAIN_LOOP_INTERVAL: 45000,
        REPLY_COOLDOWN: 75000,
        KEYWORD_ROTATE_INTERVAL: 300000,
        TREND_HARVEST_INTERVAL: 1800000,
        LOCATION_SWITCH_COOLDOWN: 3600000,
        MAX_REPLIES_PER_HOUR: 6,
        MAX_REPLIES_PER_DAY: 100,
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
        currentSearchTerm: '',
        currentMovieTitle: null,
        currentMovieYear: null,
        currentTMDBId: null,
        currentSearchTerm: '',
        currentMovieTitle: null,
        currentMovieYear: null,
        currentTMDBId: null,
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
            currentMovieYear: STATE.currentMovieYear,
            currentTMDBId: STATE.currentTMDBId,

            processedTweets: Array.from(STATE.processedTweets).slice(-200),
            locationSwitchStep: STATE.locationSwitchStep,
            timestamp: Date.now()
        };
        GM_setValue('xbot_state_v63', JSON.stringify(data));
    }

    function loadState() {
        try {
            const saved = GM_getValue('xbot_state_v63', null);
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
            if (data.currentMovieYear) STATE.currentMovieYear = data.currentMovieYear;
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
        STATE.currentKeywords = s.keywords || [];
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

        const trendElements = document.querySelectorAll('[data-testid="trend"]');
        const trends = [];

        trendElements.forEach(el => {
            const lines = el.innerText.split('\n');
            for (const line of lines) {
                const t = line.trim();
                if (/^\d/.test(t) || t.includes('·') || t.toLowerCase().includes('trending')) continue;
                if (t.length < 2 || t.length > 50) continue;

                if (t.startsWith('#')) trends.push(t);
                else if (t.length > 2 && !t.includes(' ')) trends.push('#' + t);
            }
        });

        const unique = [...new Set(trends)].slice(0, 5);
        if (unique.length > 0) {
            STATE.currentTrends = unique;
            STATE.lastTrendHarvest = Date.now();
            await sendTrendsToBrain(STATE.currentRegion, unique);
            log('Harvested:', unique);
            saveState();
            return 'SUCCESS';
        }

        return 'NO_TRENDS';
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
                    STATE.currentMovieYear = searchData.year;
                    STATE.currentTMDBId = searchData.tmdb_id;

                    log(`Smart Search: "${searchData.search_term}" (Title: ${searchData.title})`);
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

        // If we are already on search page, check if we need to rotate
        if (Date.now() - STATE.lastKeywordRotation > CONFIG.KEYWORD_ROTATE_INTERVAL) {
            // New: Fetch Smart Search Term from Brain
            log('Rotating Search Term (Smart Search)...');
            try {
                const searchData = await callBrain('/smart-search');
                if (searchData && searchData.search_term) {
                    STATE.currentSearchTerm = searchData.search_term;
                    STATE.currentMovieTitle = searchData.title;
                    STATE.currentMovieYear = searchData.year;
                    STATE.currentTMDBId = searchData.tmdb_id;
                    STATE.lastKeywordRotation = Date.now();

                    log(`Smart Search: "${searchData.search_term}" (Title: ${searchData.title})`);
                    saveState();

                    window.location.href = `https://x.com/search?q=${encodeURIComponent(searchData.search_term)}&src=typed_query&f=live`;
                    return 'NAVIGATING';
                }
            } catch (e) {
                log('Error rotating smart search term:', e);
            }

            STATE.currentKeywordIndex++;
            STATE.lastKeywordRotation = Date.now();
            log('Rotating keyword (Fallback)...');
            saveState();
            window.location.reload();
            return 'RELOADING';
        }

        return 'READY';
    }

    async function scanAndReply() {
        log('=== SCANNING ===');
        STATE.phase = PHASES.SCANNING;

        window.scrollBy({ top: randomBetween(300, 500), behavior: 'smooth' });
        await sleep(2000);

        const tweets = document.querySelectorAll('article[data-testid="tweet"]');
        const candidates = [];

        for (const tw of tweets) {
            const data = extractTweetData(tw);
            if (!data || STATE.processedTweets.has(data.tweet_id)) continue;

            STATE.processedTweets.add(data.tweet_id);
            if (isPromotedTweet(tw) || isVerifiedAccount(tw) || isBlockedAccount(data.user_handle) || containsIndiaContent(data.tweet_text)) continue;

            candidates.push(data);
        }

        log('Candidates:', candidates.length);
        if (candidates.length === 0) return 'NO_CANDIDATES';

        if (STATE.repliesThisHour >= CONFIG.MAX_REPLIES_PER_HOUR) return 'LIMIT_REACHED';
        if (Date.now() - STATE.lastReplyTime < CONFIG.REPLY_COOLDOWN) return 'COOLDOWN';

        const target = candidates[0];
        const analysis = await analyzeTweet({
            tweet_id: target.tweet_id,
            tweet_text: target.tweet_text,
            user_handle: target.user_handle,
            movie_title: STATE.currentMovieTitle, // Pass context
            movie_year: STATE.currentMovieYear    // Pass context
        });

        if (analysis.action !== 'REPLY' || !analysis.draft) return 'SKIP';

        STATE.phase = PHASES.REPLYING;
        if (CONFIG.DRY_RUN) {
            log('[DRY RUN] Would post:', analysis.draft);
            STATE.lastReplyTime = Date.now();
            STATE.repliesThisHour++;
            STATE.repliesToday++;
            saveState();
            return 'DRY_RUN';
        }

        return 'SUCCESS';
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
                    log('Location switch successful! Navigating to trending page...');
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
        p.id = 'xbot-v63';
        p.innerHTML = `
            <style>
                #xbot-v63 {
                    position: fixed; bottom: 20px; right: 20px;
                    background: #15202b; border: 1px solid #38444d; border-radius: 12px;
                    padding: 12px; z-index: 9999; color: white; font-family: sans-serif; min-width: 200px;
                }
                #xbot-v63 h4 { margin: 0 0 8px 0; color: #1da1f2; }
                #xbot-v63 div { font-size: 11px; margin: 4px 0; }
                #xbot-v63 button { width: 100%; border: none; padding: 6px; border-radius: 4px; font-weight: bold; cursor: pointer; }
                #xbot-v63 .start { background: #1da1f2; color: white; }
                #xbot-v63 .stop { background: #e0245e; color: white; }
            </style>
            <h4>🤖 XBot v6.3</h4>
            <div id="ui-status">Status: Stopped</div>
            <div id="ui-region">Region: --</div>
            <div id="ui-phase">Phase: --</div>
            <div id="ui-step">Step: --</div>
            <button id="ui-toggle" class="start">Start Bot</button>
        `;
        document.body.appendChild(p);
        document.getElementById('ui-toggle').onclick = toggleBot;
        setInterval(updateUI, 1000);
    }

    function updateUI() {
        document.getElementById('ui-status').innerText = `Status: ${STATE.isRunning ? 'Running' : 'Stopped'}`;
        document.getElementById('ui-region').innerText = `Region: ${STATE.currentRegion || '--'}`;
        document.getElementById('ui-phase').innerText = `Phase: ${STATE.phase}`;
        document.getElementById('ui-step').innerText = `Step: ${STATE.locationSwitchStep}`;
        const btn = document.getElementById('ui-toggle');
        btn.innerText = STATE.isRunning ? 'Stop Bot' : 'Start Bot';
        btn.className = STATE.isRunning ? 'stop' : 'start';
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
